### Running local drone build

Get drone cli binary: http://docs.drone.io/cli-installation/
````
sudo DOCKER_API_VERSION=1.24 arch=amd64 installer=sam /path/to/drone exec
````

Watch drone build processes:
````
watch -n 1 pstree -a $(pgrep -f dockerd)
````

### Build server

http://build.syncloud.org/syncloud/nextcloud

### Build artifacts (screenshots, system logs)

http://artifact.syncloud.org/nextcloud/ci