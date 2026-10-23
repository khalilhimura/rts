#!/usr/bin/env python3
"""Drive the real OpenRA desktop client through XTest; never inject game state.
Run with DISPLAY configured (locally or through xvfb-run). Requires Pillow and
libX11/libXtst. The game must already be built. Outputs remain in .runtime/.
"""
import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import time
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'.runtime'
LOG = RUNTIME/'ci-desktop-smoke.log'


def snapshots():
    result = []
    for line in LOG.read_text(errors='replace').splitlines():
        if line.startswith('FRONTIER_STATE '):
            try:
                result.append(json.loads(line.removeprefix('FRONTIER_STATE ')))
            except json.JSONDecodeError:
                pass  # The client may currently be writing the final line.
    return result


def player(state):
    return next(p for p in state['players'] if p['name'] == 'Multi0')


def wait_until(process, condition, label, timeout=120):
    deadline = time.monotonic()+timeout
    while time.monotonic() < deadline:
        states = snapshots()
        if states and condition(states):
            print('PASS: '+label, flush=True)
            return states[-1]
        if process.poll() is not None:
            raise RuntimeError(f'Client exited before {label}; see {LOG}')
        time.sleep(.2)
    raise RuntimeError(f'Timed out waiting for {label}; see {LOG}')


class Mouse:
    def __init__(self):
        self.x = ctypes.CDLL('libX11.so.6')
        self.t = ctypes.CDLL('libXtst.so.6')
        self.x.XOpenDisplay.argtypes = [ctypes.c_char_p]
        self.x.XOpenDisplay.restype = ctypes.c_void_p
        self.display = self.x.XOpenDisplay(os.environ['DISPLAY'].encode())
        if not self.display:
            raise RuntimeError('Cannot connect to DISPLAY')
        self.x.XFlush.argtypes = [ctypes.c_void_p]
        self.t.XTestFakeMotionEvent.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_ulong]
        self.t.XTestFakeButtonEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_int, ctypes.c_ulong]

    def move(self, x, y):
        self.t.XTestFakeMotionEvent(self.display, -1, x, y, 0)
        self.x.XFlush(self.display)

    def click(self, x, y, button=1):
        self.move(x, y)
        self.t.XTestFakeButtonEvent(self.display, button, 1, 0)
        self.t.XTestFakeButtonEvent(self.display, button, 0, 0)
        self.x.XFlush(self.display)
        time.sleep(.4)


def main():
    RUNTIME.mkdir(exist_ok=True)
    env = dict(os.environ, FRONTIER_DIAGNOSTICS='1', LIBGL_ALWAYS_SOFTWARE='1',
               MESA_SHADER_CACHE_DISABLE='true', LP_NUM_THREADS='2')
    with LOG.open('w') as output:
        process = subprocess.Popen(['./play.sh', 'Graphics.Mode=Windowed', 'Graphics.WindowedSize=1280,800',
                                    'Graphics.VSync=false', 'Graphics.CapFramerateToGameFps=true'], cwd=ROOT,
                                   env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
        try:
            initial = wait_until(process, lambda states: len(states[-1]['players']) == 2,
                                 'two-player desktop skirmish started')
            human = player(initial)
            hub = next(a for a in human['actors'] if a['type'] == 'hub')
            hx, hy = hub['x'], hub['y']
            mouse = Mouse()

            def screen(x, y):
                return 640+(x-hx)*32, 400+(y-hy)*32

            scout = next(a for a in human['actors'] if a['type'] == 'scout')
            mouse.click(*screen(scout['x'], scout['y']))
            mouse.click(*screen(hx+3, hy+2), button=3)
            mouse.move(900, 420)
            wait_until(process, lambda states: any(a['id'] == scout['id'] and (a['x'], a['y']) != (scout['x'], scout['y'])
                       for a in player(states[-1])['actors']), 'mouse selection and movement')

            def build(name, icon_x, candidates):
                mouse.click(1090, 329)  # Structures tab
                mouse.click(icon_x, 378)
                mouse.move(900, 420)
                # Rendering speed varies on software GL. Observe the real queue
                # rather than guessing how many simulation ticks have elapsed.
                wait_until(process, lambda states: any(i['name'] == name and i['ready']
                           for q in player(states[-1])['queues'] for i in q['items']), name+' production ready')
                for dx, dy in candidates:
                    mouse.click(icon_x, 378)  # Pick up the completed structure.
                    mouse.click(*screen(hx+dx, hy+dy))
                    mouse.move(900, 420)
                    try:
                        wait_until(process, lambda states: any(a['type'] == name for a in player(states[-1])['actors']),
                                   name+' placed by mouse', timeout=20)
                        return
                    except RuntimeError:
                        mouse.click(900, 420, button=3)  # Cancel only the placement preview.
                raise RuntimeError('Could not place '+name)

            build('generator', 1075, [(-3,-3), (-4,-2), (2,2)])
            build('refinery', 1140, [(-5,2), (-3,3), (3,1)])
            build('fabricator', 1210, [(2,-3), (3,3), (-4,-5)])
            mouse.click(1200, 329)  # Vehicles tab
            for x in (1140, 1210, 1075):  # Tank, artillery, scout
                mouse.click(x, 378)
            mouse.move(900, 420)
            initial_ids = {a['id'] for a in human['actors']}
            wait_until(process, lambda states: {'tank','artillery','scout'} <= {
                a['type'] for state in states for a in player(state)['actors'] if a['id'] not in initial_ids
            }, 'all three combat vehicles produced')
            wait_until(process, lambda states: all(p['earned'] > 0 for p in states[-1]['players']),
                       'both economies delivered salvage')
            ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(RUNTIME/'ci-desktop-smoke.png')
            wait_until(process, lambda states: {p['state'] for p in states[-1]['players']} == {'Won','Lost'},
                       'combat ended with a decisive outcome', timeout=420)
            subprocess.run(['python3', 'tools/check-runtime-log.py', str(LOG), '--require-victory'], cwd=ROOT, check=True)
        except Exception:
            states = snapshots()
            if states:
                print('Last observed state: '+json.dumps(states[-1]), flush=True)
            ImageGrab.grab(xdisplay=os.environ['DISPLAY']).save(RUNTIME/'ci-desktop-smoke.png')
            raise
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=15)


if __name__ == '__main__':
    main()
