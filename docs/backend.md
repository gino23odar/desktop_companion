# Desk Buddy backend (PR-07)

Local development API for a single Svinka installation. Firmware 0.5.1 and USB protocol 1 are unchanged. The companion does not contact this server until PR-08.

## Windows setup

From the repository root, use Python 3.12 and the existing virtual environment.

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements-dev.txt
$env:BUDDY_ADMIN_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
$env:BUDDY_DEVICE_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
$env:BUDDY_DB_PATH = Join-Path $PWD 'data\desk_buddy.sqlite3'
$server = Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-m','uvicorn','backend.app:create_app','--factory','--host','127.0.0.1','--port','8000') -PassThru
```

This opens the server in a separate window and leaves the original shell available for API requests. Stop the server with Ctrl+C in its window. Alternatively, run `python -m uvicorn backend.app:create_app --factory --host 127.0.0.1 --port 8000` directly in a dedicated terminal.

Generate the credentials once for a development session; stop and restart the server in the same PowerShell session to reuse them. A fresh PowerShell session will need its own variables. Credentials are not stored in SQLite. Do not print them in logs, commit them, or include them in frontend bundles. Do not use public network binding or unencrypted remote traffic. PR-12 will cover HTTPS deployment. Production secret storage and rotation, rate limiting, request size limits and backups are deferred. This is a local single-user API, not a multi-tenant service. `/health` is an unauthenticated liveness check, not a database readiness check.

Open http://127.0.0.1:8000/docs locally. Use Authorize with the admin token (without the `Bearer ` prefix in Swagger). The device token can only retrieve the active snapshot. All API requests use `Authorization: Bearer <token>`.

## API

| Method | Path | Role | Success |
|---|---|---|---|
| GET | /health | Public | 200 |
| GET | /api/v1/moods | Admin | 200 |
| POST | /api/v1/moods | Admin | 201 |
| GET | /api/v1/moods/{mood_id} | Admin | 200 |
| PUT | /api/v1/moods/{mood_id} | Admin | 200 |
| DELETE | /api/v1/moods/{mood_id} | Admin | 204 |
| GET | /api/v1/active | Admin or device | 200 |
| PUT | /api/v1/active | Admin | 200 |

POST and PUT mood bodies are the plain mood definitions used by `moods/sleepy.json`, not USB command envelopes. PUT replaces an existing entry and cannot rename its ID. The activation body is `{"mood_id":"sleepy"}`. Errors: 401 missing/invalid credential, 403 wrong role, 404 absent mood, 409 duplicate ID or attempted deletion of published mood, 422 invalid body, 503 SQLite operational failure. No-cache headers protect API responses from stale caching.

## Testing requests from PowerShell

In the shell where credentials are defined (or a second shell with those same credentials), use:

```powershell
$base = 'http://127.0.0.1:8000/api/v1'
$admin = @{ Authorization = "Bearer $env:BUDDY_ADMIN_TOKEN" }
$device = @{ Authorization = "Bearer $env:BUDDY_DEVICE_TOKEN" }
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod "$base/moods" -Headers $admin
Invoke-RestMethod "$base/moods" -Method Post -Headers $admin -ContentType 'application/json' -InFile moods/sleepy.json
Invoke-RestMethod "$base/active" -Method Put -Headers $admin -ContentType 'application/json' -Body '{"mood_id":"sleepy"}'
Invoke-RestMethod "$base/active" -Headers $device | ConvertTo-Json -Depth 8
```

On a fresh database, the initial active revision is 1 (`idle`). The first successful publication of sleepy increments it to 2. Duplicate POST is 409; use PUT to edit the existing mood. Repeat activation with the same definition to verify the unchanged revision.

## Validation and synchronization contract

Required fields: `id`, `background`, `eyes`, `mouth`, `blush`, `accessory`, `message`. Optional `animation`; if present all its fields are required, and null is rejected. ID: 1–24 lowercase ASCII letters/digits/underscore/hyphen. Background: #RRGGBB, normalized uppercase. Eyes: open/happy/sleepy/excited/glasses. Mouth: none/smile/neutral/open. Accessory: none/heart/star/zzz. Message: 0–24 printable ASCII characters. Booleans are strict. blink_ms: 0 or integer 1000–15000. Unknown fields are rejected. Absent animation defaults to 4500/true/true.

GET active returns `{ "revision": 2, "mood": { ... }, "published_at": "<UTC timestamp>" }`. Only the nested `mood` object is passed to USB `set_mood` in PR-08. Catalog edits never change the published snapshot until explicit activation. Identical snapshots do not increment the revision or alter the publication timestamp. A changed publication increments the revision in a SQLite transaction. Revision ordering applies to a single database lifetime; replacing/restoring a database can reset it. PR-08 should reconcile actual device state on reconnect, not blindly trust a stored revision. Publication is not proof of delivery; no device acknowledgments, online status or boop events are tracked by the backend yet.

## Database

SQLite creates `data/desk_buddy.sqlite3` by default. `moods` holds canonical JSON indexed by mood ID; `active_state` holds one published snapshot, revision and timestamp. Schema version is tracked via `PRAGMA user_version`. Unknown versions fail startup. There is no migration beyond schema 1. A published mood cannot be deleted until another is activated. SQLite uses short-lived connections and explicit `BEGIN IMMEDIATE` for writes. Do not commit `data/` or database files. Back up the database when the server is stopped; a new file starts at revision 1. There is no cross-database revision identity or history in PR-07.

## Automated tests

```powershell
python -m unittest discover -s tests/backend -v
python -m compileall -q backend tests/backend
```

27 test methods cover credentials, role boundaries, CRUD, invalid fields, firmware wire length, publication, concurrent revision updates, restart, unsupported DB schema and cache headers. Tests use temporary databases and in-process FastAPI TestClient; no hardware or external service is needed. CI runs Python 3.12 on Windows and Linux.
