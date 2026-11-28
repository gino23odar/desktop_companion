"""Real browser -> FastAPI -> SQLite, isolated from development data."""
import os
import socket
import tempfile
import threading
import time
import unittest
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright, expect
from backend.app import create_app
from backend.config import Settings

ADMIN = 'a'*43
DEVICE = 'd'*43

class BrowserTests(unittest.TestCase):
    def test_editor_publication_and_mobile_layout(self):
        with tempfile.TemporaryDirectory() as directory, socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            url = f'http://127.0.0.1:{sock.getsockname()[1]}'
            app = create_app(Settings(Path(directory)/'studio.db', ADMIN, DEVICE))
            server = uvicorn.Server(uvicorn.Config(app, log_level='error', lifespan='on', ws='none'))
            worker = threading.Thread(target=server.run, kwargs={'sockets':[sock]}, daemon=True)
            worker.start()
            try:
                deadline=time.monotonic()+10
                while not server.started and worker.is_alive() and time.monotonic()<deadline:
                    time.sleep(.02)
                self.assertTrue(server.started)
                with sync_playwright() as p:
                    opts = {'headless':True}
                    if os.getenv('STUDIO_CHROMIUM_PATH'):
                        opts['executable_path']=os.environ['STUDIO_CHROMIUM_PATH']
                    browser=p.chromium.launch(**opts)
                    try:
                        page=browser.new_page(viewport={'width':1280,'height':900}, reduced_motion='reduce')
                        errors=[]
                        page.on('pageerror', lambda e: errors.append(str(e)))
                        page.on('console', lambda msg: errors.append(msg.text) if 'Content Security Policy' in msg.text else None)
                        page.on('dialog', lambda d: d.accept())
                        page.goto(url+'/studio/')
                        page.locator('#token').fill(DEVICE)
                        page.get_by_role('button',name='Connect',exact=True).click()
                        expect(page.locator('#status')).to_contain_text('Administrative token required')
                        expect(page.locator('#workspace')).to_be_hidden()
                        page.locator('#token').fill(ADMIN)
                        page.get_by_role('button',name='Connect',exact=True).click()
                        expect(page.locator('#published-id')).to_have_text('idle')
                        expect(page.locator('#revision')).to_have_text('Rev 1')
                        expect(page.locator('#token')).to_have_value('')
                        page.locator('#new').click()
                        page.locator('#mood-id').fill('studio_test')
                        page.locator('#eyes').select_option('happy')
                        page.locator('#accessory').select_option('heart')
                        page.locator('#message').fill('Noches amor')
                        page.locator('#blink').fill('999')
                        expect(page.locator('#save')).to_be_disabled()
                        page.locator('#blink').fill('4500')
                        expect(page.locator('#save')).to_be_enabled()
                        expect(page.locator('#publish')).to_be_disabled()
                        page.locator('#save').click()
                        expect(page.locator('#draft-state')).to_have_text('Saved')
                        expect(page.locator('#published-id')).to_have_text('idle')
                        page.locator('#publish').click()
                        expect(page.locator('#revision')).to_have_text('Rev 2')
                        expect(page.locator('#published-message')).to_have_text('Noches amor')
                        expect(page.locator('#delete')).to_be_disabled()
                        page.locator('#publish').click()
                        expect(page.locator('#status')).to_contain_text('Published revision 2')
                        page.locator('#message').fill('Dulces suenos')
                        expect(page.locator('#publish')).to_be_disabled()
                        page.locator('#save').click()
                        expect(page.locator('#draft-state')).to_have_text('Saved')
                        expect(page.locator('#published-message')).to_have_text('Noches amor')
                        page.locator('#publish').click()
                        expect(page.locator('#revision')).to_have_text('Rev 3')
                        expect(page.locator('#published-message')).to_have_text('Dulces suenos')
                        # The editor can preview a local-only reaction without altering state.
                        before=page.locator('#preview').evaluate('(c)=>c.toDataURL()')
                        page.locator('#boop').click()
                        page.wait_for_function('(before)=>document.querySelector("#preview").toDataURL()!==before',arg=before)
                        page.wait_for_function('(before)=>document.querySelector("#preview").toDataURL()===before',arg=before)
                        expect(page.locator('#revision')).to_have_text('Rev 3')
                        page.locator('#duplicate').click()
                        expect(page.locator('#mood-id')).to_have_value('studio_test_copy')
                        page.locator('#save').click()
                        expect(page.locator('#draft-state')).to_have_text('Saved')
                        page.locator('#delete').click()
                        expect(page.locator('#catalog').get_by_text('studio_test_copy')).to_have_count(0)
                        expect(page.locator('#published-id')).to_have_text('studio_test')
                        page.set_viewport_size({'width':390,'height':844})
                        self.assertTrue(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'))
                        self.assertEqual(page.evaluate('localStorage.length + sessionStorage.length'),0)
                        self.assertEqual(page.context.cookies(),[])
                        if os.getenv('STUDIO_SCREENSHOT_DIR'):
                            page.set_viewport_size({'width':1280,'height':900})
                            page.screenshot(path=str(Path(os.environ['STUDIO_SCREENSHOT_DIR'])/'studio-desktop.png'),full_page=True)
                        page.reload()
                        expect(page.locator('#workspace')).to_be_hidden()
                        expect(page.locator('#token')).to_have_value('')
                        self.assertEqual(errors,[])
                    finally:
                        browser.close()
            finally:
                server.should_exit=True
                worker.join(10)
                self.assertFalse(worker.is_alive())

if __name__=='__main__':
    unittest.main()
