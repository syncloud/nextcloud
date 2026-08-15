local name = "nextcloud";
local nextcloud = "34.0.2";
local redis = "7.0.15";
local nginx = "1.24.0";
local nats = "2.10";
local postgresql = "16-bullseye";
local platform = '26.04.10';
local go = '1.26';
local python = '3.12-slim-bookworm';
local debian = 'bookworm-slim';
local playwright = 'v1.48.2-jammy';
local store_publisher = 'stable-346';
local distro_default = "bookworm";
local distros = ['bookworm', 'buster'];
local dind = '20.10.21-dind';

local platform_image(distro, arch) =
  'syncloud/platform-' + distro + '-' + arch + ':' + platform;

local build(arch, test_ui) = [{
    kind: "pipeline",
    type: "docker",
    name: arch,
    platform: {
        os: "linux",
        arch: arch
    },
    steps: [
        {
            name: "version",
            image: "debian:" + debian,
            commands: [
                "echo $DRONE_BUILD_NUMBER > version"
            ]
        },
        {
            name: "nextcloud",
            image: "nextcloud:" + nextcloud + "-fpm",
            commands: [
                "./nextcloud/build.sh"
            ]
        },
{
            name: "nginx",
            image: "docker:" + dind,
                commands: [
                "./nginx/build.sh " + nginx
            ],
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        },
 
         {
            name: "redis",
            image: "redis:" + redis,
            commands: [
                "./redis/build.sh"
            ]
        },
         ] + [
        {
            name: "redis test " + distro,
            image: platform_image(distro, arch),
            commands: [
                "./redis/test.sh"
            ]
        } for distro in distros
        ] + [
         {
            name: "nats",
            image: "debian:" + debian,
            commands: [
                "./nats/build.sh"
            ]
        },
         ] + [
        {
            name: "nats test " + distro,
            image: platform_image(distro, arch),
            commands: [
                "./nats/test.sh"
            ]
        } for distro in distros
        ] + [
         {
            name: "signaling",
            image: "debian:" + debian,
            commands: [
                "./signaling/build.sh"
            ]
        },
         ] + [
        {
            name: "signaling test " + distro,
            image: platform_image(distro, arch),
            commands: [
                "./signaling/test.sh"
            ]
        } for distro in distros
        ] + [
         {
            name: "postgresql",
            image: "postgres:" + postgresql,
            commands: [
                "./postgresql/build.sh"
            ]
        },
        ] + [
        {
            name: "postgresql test " + distro,
            image: platform_image(distro, arch),
            commands: [
                "./postgresql/test.sh"
            ]
        } for distro in distros
        ] + [
        {
            name: "php",
            image: "docker:" + dind,
            commands: [
                "./php/build.sh"
            ],
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        },
        {
            name: "build",
            image: "debian:" + debian,
            commands: [
                "./build.sh"
            ]
        },
        {
            name: "cli",
            image: "golang:" + go,
            commands: [
                "cd cli",
                "mkdir -p ../build/snap/meta/hooks",
                "CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/install ./cmd/install",
                "CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/configure ./cmd/configure",
                "CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/pre-refresh ./cmd/pre-refresh",
                "CGO_ENABLED=0 go build -o ../build/snap/meta/hooks/post-refresh ./cmd/post-refresh",
                "CGO_ENABLED=0 go build -o ../build/snap/bin/cli ./cmd/cli",
                "CGO_ENABLED=0 go build -o ../build/snap/bin/repair-service ./cmd/repair-service",
            ]
        },
        {
            name: "package",
            image: "debian:" + debian,
            commands: [
                "VERSION=$(cat version)",
                "./package.sh " + name + " $VERSION "
            ]
        }] + [
        {
            name: "test " + distro,
            image: "python:" + python,
            commands: [
              "cd test",
              "./deps.sh",
              'py.test -x -s test.py --distro=' + distro + ' --ver=$DRONE_BUILD_NUMBER --app=' + name,
              ]
        } for distro in distros 
        ] + ( if test_ui then [
        {
            name: "e2e",
            image: "mcr.microsoft.com/playwright:" + playwright,
            environment: {
                PLAYWRIGHT_FULL_DOMAIN: distro_default + ".com",
                PLAYWRIGHT_APP_DOMAIN: name + "." + distro_default + ".com",
                PLAYWRIGHT_DEVICE_HOST: name + "." + distro_default + ".com",
                PLAYWRIGHT_DEVICE_USER: "user",
                PLAYWRIGHT_DEVICE_PASSWORD: "Password1",
                PLAYWRIGHT_ARTIFACT_DIR: "/drone/src/artifact/e2e"
            },
            commands: [
                "apt-get update -qq && apt-get install -y -qq sshpass openssh-client curl",
                "cd test/e2e",
                "npm ci --no-audit --no-fund",
                "npx playwright test --project=desktop"
            ]
        }

] else [] ) +[
    {
        name: "test-upgrade",
        image: "python:" + python,
        commands: [
          "cd test",
          "./deps.sh",
          'py.test -x -s upgrade.py --distro=' + distro_default + ' --ver=$DRONE_BUILD_NUMBER --app=' + name,
         ]
    },
        {
            name: "publish",
            image: "syncloud/store-publisher:" + store_publisher,
            environment: {
                SYNCLOUD_TOKEN: {
                    from_secret: "SYNCLOUD_TOKEN"
                }
            },
            command: ["snap", "-c", "${DRONE_BRANCH}"],
            when: {
                branch: ["master", "stable"],
                event: ["push"]
            }
        },
        {
            name: "artifact",
            image: "appleboy/drone-scp:1.6.4",
            settings: {
                host: {
                    from_secret: "artifact_host"
                },
                username: "artifact",
                key: {
                    from_secret: "artifact_key"
                },
                timeout: "2m",
                command_timeout: "2m",
                target: "/home/artifact/repo/" + name + "/${DRONE_BUILD_NUMBER}-" + arch,
                source: "artifact/*",
		             strip_components: 1
            },
            when: {
              status: [ "failure", "success" ],
              event: [ "push" ]
            }
        }
    ],
     trigger: {
       event: [
         "push"
       ]
     },
    services: [
        {
            name: "docker",
            image: "docker:" + dind,
            privileged: true,
            volumes: [
                {
                    name: "dockersock",
                    path: "/var/run"
                }
            ]
        }] + [
        {
            name: name + "."+distro+".com",
            image: platform_image(distro, arch),
            privileged: true,
            entrypoint: ["/bin/sh", "-c", "mkdir -p /etc/systemd/system/snapd.service.d && printf '[Service]\\nExecStartPost=/bin/sh -c \"/usr/bin/snap set system refresh.hold=2099-01-01T00:00:00Z\"\\n' > /etc/systemd/system/snapd.service.d/disable-refresh.conf && exec /sbin/init"],
            volumes: [
                {
                    name: "dbus",
                    path: "/var/run/dbus"
                },
                {
                    name: "dev",
                    path: "/dev"
                }
            ]
        } for distro in distros
    ],
    volumes: [
        {
            name: "dbus",
            host: {
                path: "/var/run/dbus"
            }
        },
        {
            name: "dev",
            host: {
                path: "/dev"
            }
        },
        {
            name: "dockersock",
            temp: {}
        },
      ]
}];

build("amd64", true) +
build("arm64", false)
