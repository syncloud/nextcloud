local name = "nextcloud";

local build(arch) = {
    kind: "pipeline",
    name: arch,

    platform: {
        os: "linux",
        arch: arch
    },
    steps: [
        {
            name: "version",
            image: "syncloud/build-deps-" + arch,
            commands: [
                "echo $(date +%y%m%d)$DRONE_BUILD_NUMBER > version",
                "echo " + arch + "$DRONE_BRANCH > domain"
            ]
        },
        {
            name: "build",
            image: "syncloud/build-deps-" + arch,
            commands: [
                "VERSION=$(cat version)",
                "./build.sh " + name + " $VERSION"
            ]
        },
        {
            name: "test-intergation",
            image: "syncloud/build-deps-" + arch,
            commands: [
              "pip2 install -r dev_requirements.txt",
              "APP_ARCHIVE_PATH=$(realpath $(cat package.name))",
              "DOMAIN=$(cat domain)",
              "cd integration",
              "py.test -x -s verify.py --domain=$DOMAIN --app-archive-path=$APP_ARCHIVE_PATH --device-host=device --app=" + name
            ]
        },
        if arch == "arm" then {} else
        {
            name: "test-ui",
            image: "syncloud/build-deps-" + arch,
            commands: [
              "pip2 install -r dev_requirements.txt",
              "DOMAIN=$(cat domain)",
              "cd integration",
              "xvfb-run -l --server-args='-screen 0, 1024x4096x24' py.test -x -s test-ui.py --ui-mode=desktop --domain=$DOMAIN --device-host=device --app=" + name,
              "xvfb-run -l --server-args='-screen 0, 1024x4096x24' py.test -x -s test-ui.py --ui-mode=mobile --domain=$DOMAIN --device-host=device --app=" + name,
            ],
            volumes: [{
                name: "shm",
                path: "/dev/shm"
            }]
        },
        {
            name: "upload",
            image: "syncloud/build-deps-" + arch,
            environment: {
                AWS_ACCESS_KEY_ID: {
                    from_secret: "AWS_ACCESS_KEY_ID"
                },
                AWS_SECRET_ACCESS_KEY: {
                    from_secret: "AWS_SECRET_ACCESS_KEY"
                }
            },
            commands: [
              "VERSION=$(cat version)",
              "PACKAGE=$(cat package.name)",
              "pip2 install -r dev_requirements.txt",
              "syncloud-upload.sh " + name + " $DRONE_BRANCH $VERSION $PACKAGE"
            ]
        },
        {
            name: "artifact",
            image: "appleboy/drone-scp",
            settings: {
                host: {
                    from_secret: "artifact_host"
                },
                username: "artifact",
                password: {
                    from_secret: "artifact_password"
                },
                timeout: "2m",
                command_timeout: "2m",
                target: "/home/artifact/repo/" + name + "/${DRONE_BUILD_NUMBER}-" + arch,
                source: "artifact/*",
		             strip_components: 1
            },
            when: {
              status: [ "failure", "success" ]
            }
        }
    ],
    services: [{
        name: "device",
        image: "syncloud/systemd-" + arch,
        privileged: true,
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
    }],
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
            name: "shm",
            temp: {}
        }
    ]
};

[
    build("arm"),
    build("amd64")
]
