#!/usr/bin/env python3
"""Real-world bootstrap checkpoint; full gameplay acceptance is a later assertion set."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import io
from pathlib import Path
import threading
import time
from playwright.sync_api import sync_playwright
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--browser-path')
parser.add_argument('--bundle',type=Path,default=ROOT/'.runtime/browser-world')
parser.add_argument('--full-gameplay',action='store_true',help='Drive production, economy and the complete AI match through real canvas input')
args=parser.parse_args()
out=args.bundle.resolve()
evidence=ROOT/'.runtime/browser-world-evidence'
evidence.mkdir(exist_ok=True)

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_args): pass

server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(out)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=args.browser_path,headless=True,
            args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page(viewport={'width':1280,'height':900})
        page.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
        messages=[]
        (evidence/'console-live.txt').write_text('')
        def record(message):
            messages.append(message)
            with (evidence/'console-live.txt').open('a') as log:
                log.write(message+'\n')
            print(message[:600],flush=True)
        page.on('console',lambda message:record(message.text))
        page.on('pageerror',lambda error:record(str(error)))
        try:
            page.goto(base,wait_until='domcontentloaded')
            page.wait_for_function('window.frontierGame?.status === "failed" || window.frontierGame?.latest?.tick >= 100',timeout=180000)
            state=page.evaluate('window.frontierGame')
            (evidence/'world-state.json').write_text(json.dumps(state,indent=2)+'\n')
            print('World checkpoint: tick '+str(state.get('latest',{}).get('tick')),flush=True)
            assert state['status']=='running',state.get('error')
            assert state['latest']['type']=='Regular'
            assert len(state['latest']['players'])==2
            assert state['latest']['tick']>=100
            assert state['latest']['tick']>state['history'][0]['tick']
            rendered=page.screenshot(path=str(evidence/'world-before-input.png'),timeout=10000)
            image=Image.open(io.BytesIO(rendered)).convert('RGB')
            assert len(image.crop((260,0,1000,800)).getcolors(1000000) or [])>64,'Battlefield did not render'
            assert len(image.crop((1035,0,1280,800)).getcolors(1000000) or [])>64,'HUD did not render'
            # Exercise the actual world widget through real browser events.
            observed=list(state['history'])
            def state():
                # Fetch the current observation, rather than copying an ever
                # growing match history across CDP four times per second.
                value=page.evaluate('({status:window.frontierGame.status,error:window.frontierGame.error,latest:window.frontierGame.latest})')
                assert value['status']=='running',value.get('error')
                if not observed or value['latest']['tick']!=observed[-1]['tick']:
                    observed.append(value['latest'])
                value['history']=observed
                return value

            def wait_until(predicate,label,timeout=300,max_ticks=2000):
                deadline=time.monotonic()+timeout
                first_tick=last_tick=state()['latest']['tick']
                progressed_at=reported_at=time.monotonic()
                while time.monotonic()<deadline:
                    current=state()
                    tick=current['latest']['tick']
                    if predicate(current):
                        print(f'PASS: {label} (tick {tick})',flush=True)
                        return current
                    if tick!=last_tick:
                        last_tick,progressed_at=tick,time.monotonic()
                    if tick-first_tick>max_ticks: raise RuntimeError('Tick budget exceeded waiting for '+label)
                    if time.monotonic()-progressed_at>90: raise RuntimeError('Simulation stalled waiting for '+label)
                    if time.monotonic()-reported_at>15:
                        print(f'Waiting: {label}; tick {tick}',flush=True)
                        reported_at=time.monotonic()
                    page.wait_for_timeout(250)
                raise RuntimeError('Timed out waiting for '+label)

            def human(value):
                return next(p for p in value['latest']['players'] if p['name']=='Multi0')

            def click(x,y,button='left'):
                bounds=page.locator('canvas').bounding_box()
                x,y=bounds['x']+x*bounds['width']/1280,bounds['y']+y*bounds['height']/800
                page.mouse.move(x,y)
                page.wait_for_timeout(300)
                page.mouse.click(x,y,button=button)
                page.wait_for_timeout(400)

            initial=state()
            hub=next(a for a in human(initial)['actors'] if a['type']=='hub')
            hx,hy=hub['x'],hub['y']
            def screen(x,y): return 640+(x-hx)*32,400+(y-hy)*32
            scout=next(a for a in human(initial)['actors'] if a['type']=='scout')
            click(*screen(scout['x'],scout['y']))
            wait_until(lambda value:scout['id'] in value['latest']['selected'],'mouse selection',timeout=30)
            click(*screen(hx+3,hy+2),button='right')
            page.mouse.move(900,420)
            wait_until(lambda value:any(a['id']==scout['id'] and (a['x'],a['y'])!=(scout['x'],scout['y'])
                for a in human(value)['actors']),'right-click movement',timeout=60)
            page.set_viewport_size({'width':640,'height':500})
            current_scout=next(a for a in human(state())['actors'] if a['id']==scout['id'])
            click(*screen(current_scout['x'],current_scout['y']))
            wait_until(lambda value:value['latest']['selected']==[scout['id']],'selection with CSS scaling',timeout=30)
            page.keyboard.down('Shift')
            page.locator('#restart').focus()
            page.keyboard.up('Shift')
            wait_until(lambda value:value['latest']['inputModifiers']==0,'focus loss releases held modifiers',timeout=30)
            page.set_viewport_size({'width':1280,'height':900})
            click(*screen(current_scout['x'],current_scout['y']))
            page.keyboard.press('Escape')
            page.wait_for_timeout(500)
            state()
            page.keyboard.press('Escape')
            page.wait_for_timeout(500)
            state()
            print('PASS: actual Salt Basin world with two players, advancing ticks and responsive input')
            if args.full_gameplay:
                def build(name,icon_x,candidates):
                    click(1090,329)
                    click(icon_x,378)
                    page.mouse.move(900,420)
                    wait_until(lambda value:any(i['name']==name and i['ready'] for q in human(value)['queues']
                        for i in q['items']),name+' production ready')
                    fallback=[(0,-4),(4,0),(0,4),(-4,0),(-4,-4),(4,-4),(-4,4),(4,4),(0,-5),(5,0),(0,5),(-5,0)]
                    for dx,dy in dict.fromkeys(candidates+fallback):
                        occupied=set()
                        for player in state()['latest']['players']:
                            for actor in player['actors']:
                                size=2 if actor['type'] in {'hub','generator','refinery','fabricator'} else 1
                                occupied.update((actor['x']+x,actor['y']+y) for x in range(size) for y in range(size))
                        if {(hx+dx+x,hy+dy+y) for x in (-1,0,1) for y in (-1,0,1)} & occupied: continue
                        click(icon_x,378)
                        click(*screen(hx+dx,hy+dy))
                        page.mouse.move(900,420)
                        try:
                            wait_until(lambda value:any(a['type']==name for a in human(value)['actors']),
                                name+' placed by mouse',timeout=20)
                            return
                        except RuntimeError:
                            click(900,420,button='right')
                    raise RuntimeError('Could not place '+name)

                build('generator',1075,[(-3,-3),(-4,-2),(2,2)])
                build('refinery',1140,[(-5,2),(-3,3),(3,1)])
                build('fabricator',1210,[(2,-3),(3,3),(-4,-5)])
                click(1200,329)
                for x in (1140,1210,1075): click(x,378)
                page.mouse.move(900,420)
                original_ids={a['id'] for a in human(initial)['actors']}
                wait_until(lambda value:{'tank','artillery','scout'} <= {a['type'] for sample in value['history']
                    for player in sample['players'] if player['name']=='Multi0' for a in player['actors'] if a['id'] not in original_ids},
                    'all three combat vehicles produced')
                wait_until(lambda value:all(p['earned']>0 for p in value['latest']['players']),'both economies delivered salvage')
                page.screenshot(path=str(evidence/'world-economy.png'),timeout=10000)
                wait_until(lambda value:{p['state'] for p in value['latest']['players']}=={'Won','Lost'},
                    'decisive AI combat outcome',timeout=1500,max_ticks=8000)
                final=state()
                players=[player for sample in final['history'] for player in sample['players']]
                for name in ('Multi0','Multi1'):
                    assert {'hub','generator','refinery','fabricator','harvester'} <= {
                        a['type'] for player in players if player['name']==name for a in player['actors']},name+' incomplete base/economy'
                assert max(player['kills'] for player in players)>0,'No combat kills'
                (evidence/'world-accepted.json').write_text(json.dumps(final,indent=2)+'\n')
                metrics=page.evaluate('window.frontierGame.metrics')
                (evidence/'performance.json').write_text(json.dumps({'browser':browser.version,
                    'renderer':'headless SwiftShader','metrics':metrics,'configuredTicksPerSecond':25},indent=2)+'\n')
                print('Measured browser performance: '+json.dumps(metrics),flush=True)
                print('PASS: full original Frontier browser skirmish acceptance',flush=True)
                # Real engine menu -> confirmation -> browser-native fresh session.
                page.keyboard.press('Escape')
                page.wait_for_timeout(1000)
                click(203,435)
                page.wait_for_timeout(1000)
                page.keyboard.press('Enter')
                page.wait_for_function('window.frontierGame?.status === "failed" || (window.frontierGame?.latest?.tick > 5 && window.frontierGame.latest.tick < 100)',timeout=180000)
                fresh=page.evaluate('window.frontierGame')
                assert fresh['status']=='running',fresh.get('error')
                assert all(p['state']=='Undefined' for p in fresh['latest']['players']),'Restart retained ended match'
                print('PASS: in-game restart starts a fresh browser world',flush=True)
                page.evaluate("document.querySelector('canvas').getContext('webgl2').getExtension('WEBGL_lose_context').loseContext()")
                page.wait_for_function('window.frontierGame.status === "failed"',timeout=10000)
                assert 'Graphics context lost' in page.evaluate('window.frontierGame.error')
                page.locator('#restart').click()
                page.wait_for_function('window.frontierGame?.status === "failed" || window.frontierGame?.latest?.tick > 5',timeout=180000)
                recovered=page.evaluate('window.frontierGame')
                assert recovered['status']=='running',recovered.get('error')
                print('PASS: context loss reports an error and New skirmish recovers',flush=True)
        finally:
            if 'observed' in locals():
                (evidence/'world-observed.json').write_text(json.dumps(observed,indent=2)+'\n')
            (evidence/'world-final.json').write_text(json.dumps(page.evaluate('window.frontierGame'),indent=2)+'\n')
            (evidence/'console.txt').write_text('\n'.join(messages)+'\n')
            try:
                page.screenshot(path=str(evidence/'world.png'),timeout=10000)
            finally:
                browser.close()
finally:
    server.shutdown();server.server_close()
