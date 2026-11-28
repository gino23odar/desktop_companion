import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app import create_app
from backend.config import Settings

class StudioTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.client = TestClient(create_app(Settings(Path(tmp.name)/'test.db', 'a'*43, 'd'*43)))
        self.client.__enter__()
        self.addCleanup(self.client.__exit__, None, None, None)

    def test_static_page_and_security_headers(self):
        r = self.client.get('/studio/')
        self.assertEqual(r.status_code, 200)
        self.assertIn('Svinka Studio', r.text)
        self.assertIn("script-src 'self'", r.headers['content-security-policy'])
        self.assertIn("frame-ancestors 'none'", r.headers['content-security-policy'])
        self.assertEqual(r.headers['cache-control'], 'no-store')
        self.assertNotIn('a'*43, r.text)
        self.assertNotIn('d'*43, r.text)

    def test_modules_and_styles_served(self):
        for filename in ['app.mjs', 'api.mjs', 'model.mjs', 'preview.mjs', 'style.css']:
            with self.subTest(filename=filename):
                r = self.client.get('/studio/'+filename)
                self.assertEqual(r.status_code, 200)
                self.assertIn('javascript' if filename.endswith('.mjs') else 'text/css', r.headers['content-type'])
                self.assertEqual(r.headers['x-content-type-options'], 'nosniff')

    def test_mount_does_not_expose_project_files(self):
        for path in ['/studio/backend/config.py','/studio/data/desk_buddy.sqlite3','/studio/.env','/studio/missing.js']:
            self.assertEqual(self.client.get(path).status_code, 404)

    def test_api_still_scoped(self):
        self.assertEqual(self.client.get('/api/v1/moods').status_code, 401)
        self.assertEqual(self.client.get('/api/v1/moods',headers={'Authorization':'Bearer '+'d'*43}).status_code,403)
        self.assertEqual(self.client.get('/api/v1/moods',headers={'Authorization':'Bearer '+'a'*43}).status_code,200)
