#!/usr/bin/env python3
"""Real canvas cursor/input/performance checks; full skirmish acceptance remains separate."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import io
import json
from pathlib import Path
import statistics
import threading
import time
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser-path')
parser.add_argument('--bundle',type=Path,default=ROOT/'.runtime/browser-world')
args = parser.parse_args()
bundle = args.bundle.resolve()
evidence = ROOT/'.runtime/browser-responsiveness'
evidence.mkdir(exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self, *_args): pass
    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'self'")
        super().end_headers()

server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(bundle)))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser_path, headless=True,
            args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':1280, 'height':900})
        page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(base) else route.abort())
        messages = []
        page.on('console', lambda m: messages.append(m.text))
        page.on('pageerror', lambda e: messages.append(str(e)))
        page.add_init_script("""window.glQueries={getError:0,isTexture:0};for(const name of Object.keys(glQueries)){const original=WebGL2RenderingContext.prototype[name];WebGL2RenderingContext.prototype[name]=function(...args){glQueries[name]++;return original.apply(this,args);};}window.inputSamples=[];""")
        def until(expression, timeout=30):
            deadline = time.monotonic()+timeout
            while time.monotonic()<deadline:
                if page.evaluate(expression): return
                page.wait_for_timeout(50)
            raise AssertionError('Timed out: '+expression)
        try:
            page.goto(base, wait_until='domcontentloaded')
            until('window.frontierGame?.status==="failed" || window.frontierGame?.latest?.tick>=50', 180)
            assert page.evaluate('frontierGame.status')=='running', page.evaluate('frontierGame.error')
            canvas = page.locator('canvas')
            assert canvas.get_attribute('data-cursor-mode')=='browser'
            assert canvas.evaluate('(c)=>getComputedStyle(c).cursor').startswith('url(')
            # Browser-managed cursors are excluded from a canvas screenshot. A
            # software duplicate would alter this otherwise static HUD region.
            clip = {'x':1090, 'y':660, 'width':60, 'height':60}
            page.mouse.move(900,850)
            before = Image.open(io.BytesIO(page.screenshot(clip=clip))).convert('RGB')
            page.mouse.move(1110,680)
            page.wait_for_timeout(1000)
            after = Image.open(io.BytesIO(page.screenshot(clip=clip))).convert('RGB')
            assert ImageChops.difference(before,after).getbbox() is None, 'Software cursor duplicated in canvas'
            assert page.locator('#status').evaluate('(e)=>getComputedStyle(e).cursor')=='auto'
            assert page.evaluate('document.pointerLockElement') is None
            print('PASS: one browser cursor over canvas; ordinary cursor outside; no pointer lock', flush=True)

            page.evaluate(r"""async()=>{const {createCursorBridge}=await import('./cursors.js');const c=document.createElement('canvas');c.width=2;c.height=1;c.style.width='4px';c.style.height='2px';document.body.append(c);const bridge=createCursorBridge(c);const id=bridge.create(new Uint8Array([3,2,1,255,6,5,4,255]),2,1,1,0,true);bridge.set(id);const css=c.style.cursor;const image=new Image();image.src=css.match(/url\("([^"]+)"\)/)[1];await image.decode();if(image.width!==8||image.height!==4||!css.includes(' 4 0,'))throw new Error('Cursor scale/hotspot mismatch');const pixels=document.createElement('canvas');pixels.width=8;pixels.height=4;const context=pixels.getContext('2d');context.drawImage(image,0,0);if([...context.getImageData(0,0,1,1).data].join(',')!=='1,2,3,255')throw new Error('Cursor BGRA conversion mismatch');bridge.dispose(id);if(c.style.cursor!=='none')throw new Error('Cursor disposal mismatch');c.remove();}""")
            print('PASS: exact engine cursor colours, scaled hotspot and disposal',flush=True)
            # Observe actual pointerdown -> engine selection -> a completed render.
            page.evaluate("""window.latencyArmed=false;document.querySelector('canvas').addEventListener('pointerdown',e=>{if(e.button!==0||!latencyArmed)return;latencyArmed=false;const started=e.timeStamp;const initial=frontierGame.observe().performance.renderCount;let submitted=null;function check(){const s=frontierGame.observe();if(submitted===null&&s.selected.length&&s.performance.renderCount>initial)submitted=performance.now()-started;if(submitted!==null&&frontierGame.completedRenderFrame>initial)inputSamples.push({submittedMs:submitted,completedMs:performance.now()-started});else if(performance.now()-started<3000)requestAnimationFrame(check);}requestAnimationFrame(check);});""")
            current = page.evaluate('frontierGame.observe()')
            human = next(p for p in current['players'] if p['name']=='Multi0')
            hub = next(a for a in human['actors'] if a['type']=='hub')
            scout = next(a for a in human['actors'] if a['type']=='scout')
            x,y = 640+(scout['x']-hub['x'])*32,400+(scout['y']-hub['y'])*32
            for width in (1280,640):
                page.set_viewport_size({'width':width,'height':900})
                page.wait_for_timeout(100)
                box = canvas.bounding_box()
                page.mouse.move(box['x']+x*box['width']/1280,box['y']+y*box['height']/800)
                assert canvas.evaluate('(c)=>getComputedStyle(c).cursor').startswith('url(')
                for _ in range(5):
                    page.mouse.click(box['x']+850*box['width']/1280,box['y']+700*box['height']/800)
                    until('frontierGame.observe().selected.length===0')
                    page.evaluate('latencyArmed=true')
                    page.mouse.click(box['x']+x*box['width']/1280, box['y']+y*box['height']/800)
                    page.wait_for_timeout(500)
                until(f'frontierGame.observe().selected.includes({scout["id"]})')
            page.set_viewport_size({'width':1280,'height':900})
            # Captured drag leaves the canvas, then releases outside it.
            page.mouse.move(450,285);page.mouse.down();page.mouse.move(820,620,steps=8)
            page.mouse.move(900,840)
            assert canvas.evaluate('(c)=>getComputedStyle(c).cursor')=='auto'
            assert not page.evaluate('frontierGame.observe().inputFocus')
            page.mouse.up()
            page.mouse.move(x,y);page.mouse.click(x,y)
            until(f'frontierGame.observe().selected.includes({scout["id"]})')
            page.keyboard.down('Shift');page.locator('#restart').focus();page.keyboard.up('Shift')
            until('frontierGame.observe().inputModifiers===0')
            print('PASS: scaled hover/selection, captured drag release and focus recovery', flush=True)

            start = page.evaluate('({time:performance.now(),state:frontierGame.observe(),queries:{...glQueries}})')
            page.wait_for_timeout(10000)
            end = page.evaluate('({time:performance.now(),state:frontierGame.observe(),queries:{...glQueries},samples:inputSamples,metrics:frontierGame.metrics,inputInterop:frontierGame.inputMetrics})')
            samples = end['samples']
            assert len(samples)>=10, samples
            submitted = [sample['submittedMs'] for sample in samples]
            completed = [sample['completedMs'] for sample in samples]
            p95 = sorted(submitted)[int((len(submitted)-1)*.95)]
            completed_p95 = sorted(completed)[int((len(completed)-1)*.95)]
            assert p95<250, f'Input-to-submission p95 {p95:.1f} ms exceeds 250 ms'
            assert completed_p95<750, f'GPU-completed input frame p95 {completed_p95:.1f} ms exceeds 750 ms'
            rendered = end['state']['performance']['renderCount']-start['state']['performance']['renderCount']
            assert rendered>=10, 'Renderer stopped progressing'
            assert end['queries']['isTexture']==start['queries']['isTexture'], 'Synchronous texture validity checks returned'
            assert end['queries']['getError']-start['queries']['getError']<=rendered+5, 'GL errors queried per operation'
            tps = (end['state']['tick']-start['state']['tick'])*1000/(end['time']-start['time'])
            assert tps>=20, f'Simulation {tps:.1f} ticks/sec is below responsive budget'
            result = {'build':json.loads((bundle/'world-build.json').read_text()),'browser':browser.version,'renderer':'SwiftShader','inputMedianMs':statistics.median(submitted),'inputP95Ms':p95,'completedFrameP95Ms':completed_p95,'samplesMs':samples,'ticksPerSecond':tps,'start':start,'end':end}
            (evidence/'result.json').write_text(json.dumps(result,indent=2)+'\n')
            print(json.dumps({k:v for k,v in result.items() if k not in ('start','end')},indent=2),flush=True)
            # Retained frame-boundary validation must catch an actual GL error.
            page.evaluate("document.querySelector('canvas').getContext('webgl2').enable(0xDEAD)")
            until('frontierGame.status==="failed"')
            assert 'OpenGL Error' in page.evaluate('frontierGame.error')
            print('PASS: real invalid GL command remains detected by frame validation',flush=True)
        finally:
            (evidence/'console.txt').write_text('\n'.join(messages)+'\n')
            page.screenshot(path=str(evidence/'world.png'))
            browser.close()
finally:
    server.shutdown();server.server_close()
