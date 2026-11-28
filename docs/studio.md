# Svinka Studio

PR-09 serves the native HTML/CSS/JavaScript editor from FastAPI at `/studio/`. No npm dependencies or frontend build are required. Use a current browser (Chrome, Edge, Firefox or Safari). The backend and companion retain their existing runtime dependencies.

## Local setup (Windows PowerShell)

From the repository root with the virtual environment activated:

```powershell
python -m pip install -r backend/requirements-dev.txt
python -m pip install -r companion/requirements.txt
```

Reuse your administrative and device tokens if you still have them. If not, stop the backend before regenerating them; the companion must use the same device token as the newly started server. The database is independent of credentials.

```powershell
if (-not $env:BUDDY_ADMIN_TOKEN) {
    $env:BUDDY_ADMIN_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
}
if (-not $env:BUDDY_DEVICE_TOKEN) {
    $env:BUDDY_DEVICE_TOKEN = (python -c "import secrets; print(secrets.token_urlsafe(32))")
}
$env:BUDDY_API_URL = 'http://127.0.0.1:8000'
$env:BUDDY_DB_PATH = Join-Path $PWD 'data\desk_buddy.sqlite3'
$server = Start-Process -FilePath (Get-Command python).Source -ArgumentList @('-m','uvicorn','backend.app:create_app','--factory','--host','127.0.0.1','--port','8000') -PassThru
```

If the window closes, run the uvicorn command directly in the same terminal to inspect the traceback. Environment variables are session-scoped; a previously running backend does not inherit token changes. Do not start a second backend if one is already running.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$env:BUDDY_ADMIN_TOKEN | Set-Clipboard
Start-Process 'http://127.0.0.1:8000/studio/'
```

Paste the admin token into Studio and select Connect. Clear the clipboard afterward (`Set-Clipboard -Value ' '`). A device token is insufficient to access the catalog. Refreshing the browser or disconnecting requires authentication again. Tokens are not stored in cookies, web storage, URLs or the repository. The browser or extensions may still retain user input outside the application's control; use a trusted browser.

Connect Svinka, stop any other serial client and run:

```powershell
python -m companion --verbose sync
```

Keep the backend and companion running. Studio alone does not open USB. To stop either application, use Ctrl+C in its terminal.

## Editor behavior

- Select a saved mood or create a new draft. Saved IDs are immutable; duplicate to make another ID.
- Edit appearance and animation settings, and preview the approximate 320 x 240 firmware layout. The preview uses a browser font and Canvas geometry, not the original Adafruit pixel rasterizer. Animation periods match the PR-04 design. Preview boop is local-only.
- Save a valid draft. Saving does not change the published snapshot. Unsaved drafts cannot be published.
- Publish saved mood after confirmation. Studio reads the saved definition before publication to detect external changes. This is not an atomic compare-and-publish operation: concurrent external edits can still race between GET and PUT. For now, assume one administrator editing at a time.
- The published panel shows the last fetched server snapshot, revision and timestamp. Click Refresh to retrieve changes made through Swagger or another browser. The panel is not live device telemetry and cannot confirm physical delivery.
- Duplicate uses current draft values and a unique suggested ID. Save to persist. Delete requires confirmation; the server rejects deletion of the active mood.
- Leaving a changed draft prompts for confirmation. There is no persistent draft autosave.
- Messages: at most 24 printable ASCII characters; IDs: 1–24 lowercase ASCII letters, digits, underscores or hyphens. Blink interval: zero or integer 1000–15000 ms.

## Security and deployment

The public static files contain no credentials. The catalog and publication API retain their existing scoped bearer checks. Studio uses relative API paths, no external scripts, no automatic redirects and restrictive CSP. Administrative credentials remain in the JavaScript session only. Do not send them via unencrypted remote HTTP. Keep the server bound to loopback during PR-09. Mobile layout can be tested in browser developer tools; actual remote phone access requires trusted HTTPS deployment (PR-12). No CORS changes are required. A single administrator, single installation, and no multi-user authorization or production login flow are assumed. Server-side receipt tracking, artwork packs and custom keyframes are out of scope.

## Tests

```powershell
node --test tests/studio/model.test.mjs tests/studio/api.test.mjs
python -m unittest discover -s tests/backend -v
python -m unittest discover -s tests/companion -v
```

Node 22 is used for the unit tests, not the application runtime. Optional browser tests use Playwright; run from repository root:

```powershell
python -m pip install playwright==1.57.0
python -m playwright install chromium
python -m unittest discover -s tests/studio -p test_browser.py -v
```

The test uses an isolated temporary database and real Uvicorn process in a thread, plus Chromium. It checks device-token rejection, login, create/edit/save/publish separation, invalid fields, duplicate publication, preview boop, duplicate/delete, mobile width, and storage-free authentication. It does not require the physical ESP32. `STUDIO_CHROMIUM_PATH` optionally selects an installed Chromium executable. `STUDIO_SCREENSHOT_DIR` optionally writes a screenshot into an existing directory.

Manual: start sync, publish each mood, inspect display after a successful poll; edit a published mood and save without publishing; verify it remains unchanged until explicit publication; test invalid input, deletion protection, reload/login and mobile layout. Confirm the actual device matches the published definition using PR-08 logs. Browser preview and firmware visuals may differ slightly.
