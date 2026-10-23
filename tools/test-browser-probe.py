#!/usr/bin/env python3
"""Test the actual WASM diagnostic in Chromium; this is not gameplay acceptance."""
import functools
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.runtime/browser-probe'
EVIDENCE = ROOT/'.runtime/browser-evidence'
EVIDENCE.mkdir(exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser-path', help='Use an existing Chromium instead of the Playwright-pinned browser')
args = parser.parse_args()


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        pass


server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(OUT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser_path, headless=True,
                                    args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width': 1000, 'height': 800})
        context.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        page = context.new_page()
        console, errors, wasm = [], [], []
        page.on('console', lambda message: console.append(message.text))
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.on('response', lambda response: wasm.append(response.url) if '.wasm' in response.url else None)
        try:
            page.goto(base, wait_until='networkidle', timeout=60000)
            page.wait_for_function('window.frontierProbe?.status && window.frontierProbe.status !== "loading"', timeout=90000)
            state = page.evaluate('window.frontierProbe')
            assert state['status'] == 'passed', state
            assert not state['playable']
            assert state['report']['engineTypes'] > 500
            assert state['report']['commonTypes'] > 1000
            assert state['report']['map'] == 'Salt Basin'
            assert len(state['report']['actors']) == 8
            assert wasm, 'No WebAssembly resource was loaded'
            # Repeat real pointer input at two CSS sizes to expose canvas-scaling errors.
            canvas = page.locator('canvas')
            for width in (640, 320):
                canvas.evaluate('(canvas,width) => canvas.style.width = width+"px"', width)
                box = canvas.bounding_box()
                page.mouse.click(box['x']+box['width']/2, box['y']+box['height']/2, button='right')
            state = page.evaluate('window.frontierProbe')
            assert state['inputs'] == [{'x': 256, 'y': 32, 'button': 'Right'}]*2, state['inputs']
            assert not errors, errors
            state['browser'] = browser.version
            state['wasmRequests'] = len(wasm)
            (EVIDENCE/'probe-result.json').write_text(json.dumps(state, indent=2)+'\n')
            page.screenshot(path=str(EVIDENCE/'probe.png'))
            print(json.dumps(state, indent=2))
        finally:
            (EVIDENCE/'console.txt').write_text('\n'.join(console+errors)+'\n')
            browser.close()
finally:
    server.shutdown()
    server.server_close()
