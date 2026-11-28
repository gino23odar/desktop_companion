# Remote mood synchronization (PR-08)

The `sync` subcommand polls `GET /api/v1/active` using the read-only device
credential and owns the serial port for its entire session. The existing
PR-07 API and firmware protocol v1 remain unchanged. No additional runtime
Python dependencies are needed beyond the companion's pySerial dependency.

## Windows local development

Use the repository root and activate the existing virtual environment.
Start the PR-07 backend on `127.0.0.1:8000` with its existing admin and device
tokens. In a terminal with the same device token configured:

```powershell
.\.venv\Scripts\Activate.ps1
$env:BUDDY_API_URL = 'http://127.0.0.1:8000'
# BUDDY_DEVICE_TOKEN must match the already running server's device token.
python -m companion ports
python -m companion sync
```

If automatic discovery is ambiguous, use `python -m companion --port COM4 sync`
(replace COM4 with the correct port) or `--usb-serial SERIAL` before `sync`.
Publish using Swagger at http://127.0.0.1:8000/docs with the admin token.
Stop sync using Ctrl+C before running `watch` or other serial commands.
A new PowerShell session does not automatically inherit another terminal's
process-scoped environment variables. Reuse the existing server token, rather
than generating a different token for the companion.

## Linux

Use `source .venv/bin/activate`, `export BUDDY_API_URL=http://127.0.0.1:8000`,
and set `BUDDY_DEVICE_TOKEN` to the server's device token through your local
secret configuration. Use `python -m companion sync`. A selected explicit
port may be `/dev/ttyUSB0`; use automatic discovery or the bridge serial
number if port names change. The user needs permission to access the port.

## Configuration

- `BUDDY_API_URL`: HTTP origin on numeric loopback (`127.0.0.1` or `::1`),
  or HTTPS origin for a remote service. No credentials, paths or queries.
- `BUDDY_DEVICE_TOKEN`: existing read-only token, 32–256 URL-safe characters.
- `BUDDY_SYNC_CACHE`: optional path, defaults to `data/sync-cache.json`.

Do not put credentials on the command line, in Git, or in the cache. Remote
connections require HTTPS with ordinary certificate validation. Redirects
and implicit environment proxies are disabled. Public HTTPS deployment is
PR-12; do not expose the local development server directly to the internet.
Use only the device token on the recipient's computer, with her knowledge
and permission. PR-08 does not install autostart or a background service.

## Behavior

Poll interval: 5 seconds after a successful request. HTTP failures retry
with delays of 5, 10, 20, 40 and at most 60 seconds; USB reconnection retries
after 2 seconds. Connected serial clients ping after 3 seconds of inactivity
as measured by the scheduler (ordinary readback also counts), and re-read
base mood every 15 seconds. These are target intervals, not hard deadlines:
HTTP and serial operations are synchronous and can delay one another. HTTP
socket timeout is 3 seconds per blocking operation, not a total deadline.

Validate publication fields, strict mood schema, animation values and
serial request size before caching or applying a mood. Compare actual base
mood with the desired definition rather than relying solely on revision.
Apply only when different, check the correlated acknowledgment and read back
the base mood. On an ambiguous write timeout, close and reconnect, read the
actual state, then write only if needed. A `ready` event schedules reconciliation;
periodic readback provides additional recovery. Temporary boop overlays do not
change base mood and should not be interrupted by synchronization.

When the API is down, retain the latest valid cached publication. If there
is no cache and no valid network response, leave the physical mood untouched.
When USB is absent, continue fetching and caching new publications. Only the
latest state matters, not every intermediate revision. After reconnect, apply
the newest known valid snapshot. A lower revision or same-revision changed
content can occur after database replacement; the authenticated server's
current state wins. No server delivery receipt is implemented.

The cache uses a versioned envelope scoped to the configured API origin,
atomic replacement in the same directory, and no credentials. It is desired
state, not a delivery receipt. Invalid caches are ignored; cache save failures
do not block online delivery. Treat cached messages as private local data.
If repointing the same origin to another installation, remove the old cache
with sync stopped. Do not run multiple sync processes with the same cache or
serial port. Offline mode may restore an older cached mood until a fresh
server response arrives; cached moods have no expiry in this version.

## Tests

```powershell
python -m unittest discover -s tests/companion -v
python -m unittest discover -s tests/backend -v
python -m compileall -q companion backend tests
```

Existing workflows automatically discover the new tests: 30 sync-specific
companion tests and one live HTTP integration test under the backend suite.
The integration test uses real Uvicorn, SQLite and SerialClient, with a
simulated serial transport instead of physical hardware. Hardware regression:
publish, unplug USB, publish twice, reconnect, stop/restart API, restart sync
with the API offline, test boops and check that repeated identical publication
does not cause redraws. See the implementation guide for expected results.
