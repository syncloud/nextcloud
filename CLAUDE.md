# CI

http://ci.syncloud.org:8080/syncloud/nextcloud

Drone CI (JS SPA). Check builds via API:
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/nextcloud/builds?limit=5"
```

## Debugging CI failures

Identify the failing step:
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/nextcloud/builds/{N}" | python3 -c "
import json,sys
b=json.load(sys.stdin)
for stage in b.get('stages',[]):
    for step in stage.get('steps',[]):
        if step.get('status') == 'failure':
            print(stage['number'], step['number'], step.get('name'), '-', step.get('status'))
"
```

Step log (stage=pipeline index, step=step number):
```
curl -s "http://ci.syncloud.org:8080/api/repos/syncloud/nextcloud/builds/{N}/logs/{stage}/{step}" | python3 -c "
import json,sys; [print(l.get('out',''), end='') for l in json.load(sys.stdin)]
" | tail -80
```

## CI artifacts

Served at `http://ci.syncloud.org:8081` (JSON directory listings).

Top level for a build (distro subdirs + snap file):
```
curl -s "http://ci.syncloud.org:8081/files/nextcloud/{build}-{arch}/"
curl -s "http://ci.syncloud.org:8081/files/nextcloud/{build}-{arch}/{distro}/"
curl -s "http://ci.syncloud.org:8081/files/nextcloud/{build}-{arch}/{distro}/log/"
curl -s "http://ci.syncloud.org:8081/files/nextcloud/{build}-{arch}/{distro}/platform_log/"
```

`log/journalctl.log` is the full journal from integration test teardown — primary signal for `test {distro}` failures.

Download directly:
```
curl -O "http://ci.syncloud.org:8081/files/nextcloud/899-amd64/bookworm/log/journalctl.log"
curl -O "http://ci.syncloud.org:8081/files/nextcloud/899-amd64/nextcloud_899_amd64.snap"
```

# Project structure

Nextcloud snap packaging. `.drone.jsonnet` drives the CI pipeline — do not edit `.drone.yml` directly.

- `nextcloud/` — nextcloud core build
- `nginx/`, `php/`, `redis/`, `postgresql/`, `nats/`, `signaling/`, `python/` — bundled component build scripts
- `config/` — runtime config templates (nginx.conf, php-fpm, etc.)
- `hooks/` — snap lifecycle hooks (configure, install, post-refresh)
- `bin/` — wrapper scripts bundled into the snap
- `meta/snap.yaml` — snap metadata
- `test/` — Python integration tests (pytest) and UI tests (Selenium)
- `package.sh` — builds the `.snap`

`test/test.py` is the integration test that fails most often — it activates the app then exercises REST endpoints. `test_activate_device` failing with "cannot login" usually means the platform changed an auth endpoint; check `../platform/backend/rest/backend.go` for the current routes before blaming local changes.
