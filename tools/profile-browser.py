#!/usr/bin/env python3
"""Profile the real local browser game without modifying simulation or game state."""
import argparse
from collections import Counter
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--bundle',type=Path,default=ROOT/'.runtime/browser-world')
parser.add_argument('--label',default='current')
parser.add_argument('--seconds',type=int,default=20)
parser.add_argument('--browser-path')
args = parser.parse_args()
assert 1<=args.seconds<=120
assert args.label and all(c.isalnum() or c in '-_' for c in args.label)
out = ROOT/'.runtime/latency-profiles'
out.mkdir(exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_args): pass

server = ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(args.bundle)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=args.browser_path,headless=True,
            args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page = browser.new_page(viewport={'width':1280,'height':900})
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
        page.add_init_script("""window.glProfile={enabled:false,calls:{}};
            for(const name of ['getError','isTexture','getParameter','drawArrays','drawElements','bufferSubData','flush','finish','readPixels']){
                const original=WebGL2RenderingContext.prototype[name];
                WebGL2RenderingContext.prototype[name]=function(...args){
                    if(!glProfile.enabled)return original.apply(this,args);
                    const start=performance.now();
                    try{return original.apply(this,args);}finally{
                        const value=glProfile.calls[name]??={count:0,ms:0};
                        value.count++;value.ms+=performance.now()-start;
                    }
                };
            }""")
        try:
            page.goto(base,wait_until='domcontentloaded')
            deadline = time.monotonic()+180
            while time.monotonic()<deadline:
                state = page.evaluate('window.frontierGame')
                if state and state.get('status')=='failed':raise RuntimeError(state['error'])
                if state and state.get('latest',{}).get('tick',0)>=100:break
                page.wait_for_timeout(250)
            else:raise RuntimeError('World boot timed out')
            print('Warmup complete at tick',state['latest']['tick'],flush=True)
            cdp = page.context.new_cdp_session(page)
            cdp.send('Profiler.enable');cdp.send('Profiler.start')
            page.evaluate('glProfile.enabled=true')
            snapshot = '({time:performance.now(),tick:frontierGame.latest.tick,metrics:frontierGame.metrics,phase:frontierGame.latest.performance})'
            start = page.evaluate(snapshot)
            page.wait_for_timeout(args.seconds*1000)
            end = page.evaluate(snapshot)
            gl = page.evaluate('glProfile.calls')
            cpu = cdp.send('Profiler.stop')['profile']
            page.evaluate('glProfile.enabled=false')
            nodes = {node['id']:node for node in cpu['nodes']}
            hot = [{'function':nodes[i]['callFrame']['functionName'],'samples':count}
                for i,count in Counter(cpu.get('samples',[])).most_common(12)]
            result = {'browser':browser.version,'renderer':'headless SwiftShader','start':start,'end':end,'gl':gl,
                'ticksPerSecond':(end['tick']-start['tick'])*1000/(end['time']-start['time']),'cpuHotFunctions':hot}
            build = args.bundle/'world-build.json'
            if build.exists():result['build']=json.loads(build.read_text())
            (out/(args.label+'.json')).write_text(json.dumps(result,indent=2)+'\n')
            (out/(args.label+'-cpu.json')).write_text(json.dumps(cpu)+'\n')
            page.screenshot(path=str(out/(args.label+'.png')))
            print(json.dumps(result,indent=2),flush=True)
        finally:browser.close()
finally:
    server.shutdown();server.server_close()
