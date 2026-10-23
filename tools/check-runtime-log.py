#!/usr/bin/env python3
"""Assert outcomes recorded by FRONTIER_DIAGNOSTICS=1 during a desktop smoke test.
This reads evidence; it does not automate mouse input or simulate a match.
"""
import argparse
import json
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('log',type=Path)
parser.add_argument('--require-victory',action='store_true')
args=parser.parse_args()
states=[json.loads(line.removeprefix('FRONTIER_STATE ')) for line in args.log.read_text().splitlines() if line.startswith('FRONTIER_STATE ')]
assert states, 'No diagnostic snapshots found'
players=[p for state in states for p in state['players']]
human=[p for p in players if p['name']=='Multi0']
ai=[p for p in players if p['name']=='Multi1']
assert human and ai, 'Both skirmish players must exist'
for label, history in [('human',human),('AI',ai)]:
    types={a['type'] for p in history for a in p['actors']}
    assert {'hub','generator','refinery','fabricator','harvester'} <= types, f'{label}: incomplete base/economy'
    assert max(p['earned'] for p in history)>0, f'{label}: no resource deliveries'
assert {'scout','tank','artillery'} <= {a['type'] for p in human for a in p['actors']}, 'Human combat roster incomplete'
original={a['id']:a for a in human[0]['actors'] if a['type']=='scout'}
assert any(a['id'] in original and (a['x'],a['y']) != (original[a['id']]['x'],original[a['id']]['y']) for p in human[1:] for a in p['actors']), 'No human scout movement recorded'
assert max(p['kills'] for p in players)>0, 'No combat kills recorded'
initial_tanks={a['id'] for a in human[0]['actors'] if a['type']=='tank'}
assert any(a['type']=='tank' and a['id'] not in initial_tanks for p in human for a in p['actors']), 'No human tank production recorded'
if args.require_victory:
    final={p['state'] for p in states[-1]['players']}
    assert final == {'Won','Lost'}, f'No decisive outcome: {final}'
print(f"PASS: {len(states)} desktop snapshots through tick {states[-1]['tick']}; bases, harvesting, movement, production and combat confirmed.")
