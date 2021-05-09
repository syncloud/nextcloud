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
              "py.test -x -s test-ui.py --ui-mode=desktop --domain=$DOMAIN --device-host=device --app=" + name,
              "py.test -x -s test-ui.py --ui-mode=mobile --domain=$DOMAIN --device-host=device --app=" + name,
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
              status: [ "failure", "success" ]
            }
        }
    ],
    services: [
        {
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
        },
        if arch == "arm" then {} else {
            name: "selenium",
            image: "selenium/standalone-firefox:4.0.0-beta-1-20210215",
            volumes: [{
                name: "shm",
                path: "/dev/shm"
            }]
        }
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
            name: "shm",
            temp: {}
        }
    ]
};

[
    build("arm"),
    build("amd64")
]
