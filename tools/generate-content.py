#!/usr/bin/env python3
"""Deterministic CC0 model renderer + original prototype art/map. Requires Pillow.
No upstream renderer/tool binaries are used. See docs/PROVENANCE.md.
"""
from pathlib import Path
from PIL import Image, ImageDraw, PngImagePlugin
import math
import random
import struct

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'mods/frontier'
ART = MOD / 'sequences/assets'
ART.mkdir(parents=True, exist_ok=True)

# Original 3x5 bitmap lettering, CC0; avoids embedding third-party font art.
GLYPHS = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ', [
 '25755','65656','34443','65556','74647','74644','34553','55755',
 '72227','11152','55655','44447','57755','57555','25552','65644',
 '25573','65655','74217','72222','55557','55552','55575','55255',
 '55222','71247']))
def pixel_text(draw, position, text, fill):
    x,y=position
    for char in text:
        if char in GLYPHS:
            for row,bits in enumerate(GLYPHS[char]):
                for col in range(3):
                    if int(bits) & (4>>col): draw.point((x+col,y+row),fill=fill)
        x+=4

def sheet(name, frames):
    w, h = frames[0].size
    out = Image.new('RGBA', (1 << (w * len(frames) - 1).bit_length(), 1 << (h - 1).bit_length()))
    for i, frame in enumerate(frames):
        out.paste(frame, (i * w, 0))
    meta = PngImagePlugin.PngInfo()
    meta.add_text('FrameSize', f'{w},{h}')
    meta.add_text('FrameAmount', str(len(frames)))
    out.save(ART / f'{name}.png', pnginfo=meta)

def voxels(name):
    raw = (ROOT / 'assets/sources/pixvoxel' / f'{name}.vox').read_bytes()
    assert raw[:4] == b'VOX '
    start = raw.index(b'XYZI') + 12
    count, = struct.unpack_from('<I', raw, start)
    return [tuple(raw[start+4+i*4:start+8+i*4]) for i in range(count)]

def model_frame(model, facing):
    points = voxels(model)
    # Source indices encode materials. This deliberately uses a new palette;
    # green paint falls inside OpenRA PlayerColorShift's remap interval.
    colors = {233:(47,57,64),249:(32,38,43),217:(170,189,181),193:(29,222,67),
              241:(18,25,29),137:(92,120,129),141:(111,148,159),161:(130,151,155),
              253:(205,221,215),129:(236,198,112),197:(37,170,58),201:(135,242,174),
              113:(80,99,110),185:(221,181,97),169:(152,177,181)}
    cx = (min(p[0] for p in points)+max(p[0] for p in points))/2
    cy = (min(p[1] for p in points)+max(p[1] for p in points))/2
    z0 = min(p[2] for p in points)
    a = facing * math.pi/4
    c, s = math.cos(a), math.sin(a)
    rotated = []
    for x,y,z,i in points:
        x,y = x-cx,y-cy
        rx,ry = x*c-y*s,x*s+y*c
        rotated.append((rx,ry,z-z0,i))
    im = Image.new('RGBA',(192,192))
    d = ImageDraw.Draw(im)
    d.ellipse((39,116,154,157),fill=(12,20,24,100))
    scale = 2.5
    for x,y,z,i in sorted(rotated,key=lambda p:p[1]+p[2]*0.02):
        px,py = 96+x*scale,130+y*scale*0.60-z*scale*0.84
        base = colors.get(i,(153,175,174))
        d.rectangle((px-1.5,py-2,px+1.5,py+1),fill=(*base,255))
    return im.resize((64,64),Image.Resampling.NEAREST)

models = {'scout':'Tank_S_Large_W','tank':'Tank_Large_W',
          'artillery':'Artillery_S_Large_W','harvester':'Truck_Large_W'}
for name, model in models.items():
    frames = [model_frame(model,i) for i in range(8)]
    sheet(name,frames)
    icon=Image.new('RGBA',(64,48),(23,36,44,255)); icon.alpha_composite(frames[3],(0,-8))
    pixel_text(ImageDraw.Draw(icon),(3,36),name.upper(),fill=(228,240,229))
    sheet(name+'-icon',[icon])

# Original building silhouettes: four distinct industrial structures on 2x2 pads.
for name in ('hub','generator','refinery','fabricator'):
    im=Image.new('RGBA',(96,96)); d=ImageDraw.Draw(im)
    d.polygon([(8,72),(23,82),(91,73),(77,61)],fill=(10,20,23,110))
    d.rectangle((15,33,78,75),fill=(31,42,49),outline=(124,154,160),width=2)
    d.rectangle((19,37,74,70),fill=(62,79,85))
    d.rectangle((19,66,74,70),fill=(30,225,66))
    if name=='hub':
        d.rectangle((28,28,66,58),fill=(95,120,130),outline=(177,204,199),width=2)
        d.rectangle((32,34,62,42),fill=(30,225,66)); d.line((55,28,55,9),fill=(215,225,208),width=2)
        d.ellipse((43,3,67,14),fill=(155,179,181)); d.ellipse((50,6,60,10),fill=(34,66,76))
    elif name=='generator':
        for x in (29,54):
            d.rectangle((x,22,x+14,59),fill=(41,58,66),outline=(137,170,174),width=2)
            for y in (28,36,44,52): d.rectangle((x+3,y,x+11,y+3),fill=(30,225,66))
    elif name=='refinery':
        for x in (26,54):
            d.rectangle((x,29,x+18,58),fill=(124,149,153)); d.ellipse((x,23,x+18,35),fill=(179,195,181))
        d.rectangle((35,61,59,77),fill=(10,19,26)); d.rectangle((38,62,56,65),fill=(74,226,224))
    else:
        d.rectangle((22,30,70,57),fill=(117,141,149)); d.rectangle((27,37,65,72),fill=(17,26,33))
        d.line((24,61,24,25,69,25,69,61),fill=(30,225,66),width=4)
        d.line((49,26,49,45),fill=(235,191,98),width=3)
    sheet(name,[im])
    icon=Image.new('RGBA',(64,48),(23,36,44,255)); icon.alpha_composite(im.resize((52,52)),(6,-12))
    pixel_text(ImageDraw.Draw(icon),(2,36),name.upper(),fill=(228,240,229)); sheet(name+'-icon',[icon])

# Original terrain and overlays. Random texture seed is fixed for reproducibility.
rng=random.Random(5041)
terrain=MOD/'tilesets/frontier'; terrain.mkdir(parents=True,exist_ok=True)
for name,base in [('ground',(76,88,82)),('road',(109,115,108)),('rock',(38,53,62))]:
    im=Image.new('RGBA',(32,32),(*base,255)); d=ImageDraw.Draw(im)
    for _ in range(120):
        x,y=rng.randrange(32),rng.randrange(32); delta=rng.randrange(-8,9)
        d.point((x,y),fill=tuple(max(0,min(255,v+delta)) for v in base)+(255,))
    if name=='rock':
        d.polygon([(0,23),(9,5),(20,4),(31,15),(26,31)],fill=(53,69,77),outline=(78,94,99))
        d.line((9,5,12,19,26,31),fill=(30,43,52),width=2)
    im.save(terrain/f'{name}.png')
resources=[]
for density in range(20):
    im=Image.new('RGBA',(32,32)); d=ImageDraw.Draw(im)
    for k in range(1+density//2):
        x,y=6+(k*13)%20,9+(k*7)%18
        d.polygon([(x,y-7),(x+4,y),(x,y+4),(x-3,y)],fill=(70,210,216),outline=(151,247,231))
    resources.append(im)
sheet('salvage',resources)
for name,color in [('build-valid',(30,220,90,100)),('build-invalid',(230,55,65,100)),('build-unknown',(220,190,60,100))]:
    im=Image.new('RGBA',(32,32),color); ImageDraw.Draw(im).rectangle((0,0,31,31),outline=color[:3]+(230,)); sheet(name,[im])
# Production progress clock: 32 clockwise sector overlays, transparent when ready.
clocks=[]
for n in range(32):
    im=Image.new('RGBA',(64,48)); d=ImageDraw.Draw(im)
    if n<31: d.pieslice((-10,-18,74,66),n*360/31-90,270,fill=(0,0,0,155))
    clocks.append(im)
sheet('clock',clocks)
sheet('rallypoint',[Image.new('RGBA',(16,16),(30,225,66,180))])

sequences=[]
for name in list(models)+['hub','generator','refinery','fabricator']:
    facings='\n\t\tFacings: 8' if name in models else ''
    sequences.append(f'{name}:\n\tidle:\n\t\tFilename: sequences/assets/{name}.png{facings}\n\ticon:\n\t\tFilename: sequences/assets/{name}-icon.png\n')
sequences += ['resources:\n\tsalvage:\n\t\tFilename: sequences/assets/salvage.png\n\t\tLength: 20\n',
'overlay:\n'+''.join(f'\t{name}:\n\t\tFilename: sequences/assets/{name}.png\n\t\tStart: 0\n' for name in ('build-valid','build-invalid','build-unknown')),
'clock:\n\tidle:\n\t\tFilename: sequences/assets/clock.png\n\t\tLength: 32\n',
'rallypoint:\n\tflag:\n\t\tFilename: sequences/assets/rallypoint.png\n\tcircles:\n\t\tFilename: sequences/assets/rallypoint.png\n']
(MOD/'sequences/frontier.yaml').write_text('\n'.join(sequences))

# Map v2: x-major tile/resource planes; symmetric rocks with three traversable lanes.
size=66; cells={}; ore={}
for x in range(size):
    for y in range(size):
        tile=1 if abs(x-y)<2 else 0
        if x in (0,65) or y in (0,65): tile=2
        if 29<=x<=36 and 5<=y<=60 and not any(abs(y-gap)<=3 for gap in (13,33,52)): tile=2
        cells[x,y]=tile
for cx,cy in [(9,23),(23,9),(42,56),(56,42),(23,34),(42,31)]:
    for x in range(cx-4,cx+5):
        for y in range(cy-4,cy+5):
            if (x-cx)**2+(y-cy)**2<=16 and cells[x,y]==0: ore[x,y]=20
header=struct.pack('<BHHIII',2,size,size,17,0,17+size*size*3)
data=header+b''.join(struct.pack('<HB',cells[x,y],0) for x in range(size) for y in range(size))
data+=b''.join(bytes((1,ore[x,y])) if (x,y) in ore else b'\0\0' for x in range(size) for y in range(size))
preview=Image.new('RGB',(size,size)); palette={0:(76,88,82),1:(109,115,108),2:(38,53,62)}
for pos,tile in cells.items(): preview.putpixel(pos,(70,210,216) if pos in ore else palette[tile])
for name in ('salt-basin',):
    target=MOD/'maps'/name; (target/'map.bin').write_bytes(data); preview.resize((256,256),Image.Resampling.NEAREST).save(target/'map.png')
print('Generated eight-direction sprites, original buildings/terrain/HUD assets, and Salt Basin map.')

# Original menu mark replaces the SDK example logo.
logo=Image.new('RGBA',(512,256)); d=ImageDraw.Draw(logo)
d.polygon([(28,198),(115,42),(202,198)],outline=(101,228,206),width=10)
d.line((65,160,115,75,165,160),fill=(200,222,212),width=5)
d.line((45,199,186,199),fill=(227,183,96),width=8)
pixel_text(d,(42,220),'FRONTIER COLLECTIVE',fill=(220,236,222))
logo.save(MOD/'chrome/assets/loadscreen.png')
