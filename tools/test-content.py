#!/usr/bin/env python3
"""Content integrity, map reachability and non-destructive acquisition tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fetch_engine', ROOT/'tools/fetch-engine.py')
acquisition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(acquisition)


class ContentTests(unittest.TestCase):
    def test_cc0_sources_match_pinned_hashes(self):
        lock = json.loads((ROOT/'assets/sources/pixvoxel/manifest.json').read_text())
        for name, checksum in lock['files'].items():
            self.assertEqual(hashlib.sha256((ROOT/'assets/sources/pixvoxel'/name).read_bytes()).hexdigest(), checksum)

    def test_png_sheet_regions_and_chrome_dimensions(self):
        for path in (ROOT/'mods/frontier/sequences/assets').glob('*.png'):
            with Image.open(path) as image:
                if 'FrameSize' in image.info:
                    width, height = map(int, image.info['FrameSize'].split(','))
                    count = int(image.info['FrameAmount'])
                    self.assertGreaterEqual((image.width//width)*(image.height//height), count, path.name)
                if path.name.endswith('-icon.png'):
                    for length in image.size:
                        self.assertEqual(length & (length-1), 0, path.name)

    def test_map_routes_and_salvage_are_reachable(self):
        data = (ROOT/'mods/frontier/maps/salt-basin/map.bin').read_bytes()
        version, width, height, tiles, heights, resources = struct.unpack_from('<BHHIII', data)
        self.assertEqual((version, width, height, tiles, heights), (2,66,66,17,0))
        self.assertEqual(len(data), resources+width*height*2)
        cells = {(x,y):struct.unpack_from('<HB',data,tiles+3*(x*height+y))[0] for x in range(width) for y in range(height)}
        salvage = {(x,y) for x in range(width) for y in range(height) if data[resources+2*(x*height+y)] == 1}
        self.assertGreater(len(salvage), 250)
        for start in [(12,12),(52,52)]:
            reached={start}; todo=[start]
            while todo:
                x,y=todo.pop()
                for candidate in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                    if candidate not in reached and cells.get(candidate,2) != 2:
                        reached.add(candidate); todo.append(candidate)
            self.assertTrue(salvage <= reached)
            self.assertIn((12,12), reached)
            self.assertIn((52,52), reached)
            for gap in [13,33,52]:
                self.assertIn((32,gap), reached)

    def test_acquisition_preserves_existing_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            engine=Path(directory)/'engine'; engine.mkdir()
            important=engine/'local-change.cs'; important.write_text('existing work')
            with self.assertRaisesRegex(RuntimeError, 'Preserving it'):
                acquisition.fetch('pinned','unused','invalid',engine)
            self.assertEqual(important.read_text(), 'existing work')

    def test_checksum_failure_does_not_install_engine(self):
        with tempfile.TemporaryDirectory() as directory:
            engine=Path(directory)/'engine'
            def fake_download(args, **kwargs):
                Path(args[-1]).write_bytes(b'wrong archive')
            with patch.object(acquisition.subprocess,'run',side_effect=fake_download):
                with self.assertRaisesRegex(RuntimeError, 'SHA-256 mismatch'):
                    acquisition.fetch('pinned','unused','0'*64,engine)
            self.assertFalse(engine.exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
