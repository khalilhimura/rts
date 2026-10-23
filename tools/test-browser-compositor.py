#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare the framebuffer compositor against the actual general sprite shader."""
import argparse
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--bundle',type=Path,default=ROOT/'.runtime/browser-world')
p.add_argument('--browser-path')
a=p.parse_args()
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*_args): pass
    def do_GET(self):
        if self.path=='/__test':
            body=b'<!doctype html><title>Compositor equivalence</title>'
            self.send_response(200);self.send_header('Content-Type','text/html');self.end_headers();self.wfile.write(body)
        else:super().do_GET()
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(a.bundle.resolve())))
threading.Thread(target=server.serve_forever,daemon=True).start()
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=a.browser_path,headless=True,args=['--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        page=browser.new_page()
        try:
            page.goto(f'http://127.0.0.1:{server.server_port}/__test')
            result=page.evaluate(r'''async()=>{
                const sources={};for(const name of ['combined.vert','combined.frag','framebuffer.vert','framebuffer.frag']){
                    const response=await fetch('./content/glsl/'+name);if(!response.ok)throw new Error('Missing '+name);
                    sources[name]=await response.text();
                }
                const canvas=document.createElement('canvas');canvas.width=128;canvas.height=128;
                const gl=canvas.getContext('webgl2',{antialias:false});if(!gl)throw new Error('WebGL2 unavailable');
                const names=['aVertexPosition','aVertexTexCoord','aVertexAttributes','aVertexTint'];
                function program(prefix,swap){
                    const value=gl.createProgram();
                    for(const [suffix,type] of [['vert',gl.VERTEX_SHADER],['frag',gl.FRAGMENT_SHADER]]){
                        const shader=gl.createShader(type);
                        gl.shaderSource(shader,sources[prefix+'.'+suffix].replace('{VERSION}','300 es').replace('{DEFINES}',swap?'#define SWAP_TEXTURE_CHANNELS':''));
                        gl.compileShader(shader);if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(shader));
                        gl.attachShader(value,shader);
                    }
                    names.forEach((name,index)=>gl.bindAttribLocation(value,index,name));gl.linkProgram(value);
                    if(!gl.getProgramParameter(value,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(value));
                    return value;
                }
                const fixture=new Uint8Array(8*8*4);
                for(let i=0;i<64;i++){
                    const alpha=[0,64,128,255][i%4];fixture[i*4]=Math.round((i*29%256)*alpha/255);
                    fixture[i*4+1]=Math.round((i*53%256)*alpha/255);fixture[i*4+2]=Math.round((i*97%256)*alpha/255);fixture[i*4+3]=alpha;
                }
                const source=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,source);
                for(const parameter of [gl.TEXTURE_WRAP_S,gl.TEXTURE_WRAP_T])gl.texParameteri(gl.TEXTURE_2D,parameter,gl.CLAMP_TO_EDGE);
                gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,8,8,0,gl.RGBA,gl.UNSIGNED_BYTE,fixture);
                gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
                const target=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,target);
                gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,128,128,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
                const fbo=gl.createFramebuffer();gl.bindFramebuffer(gl.FRAMEBUFFER,fbo);
                gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,target,0);
                if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw new Error('Fixture framebuffer incomplete');
                gl.bindVertexArray(gl.createVertexArray());gl.bindBuffer(gl.ARRAY_BUFFER,gl.createBuffer());
                for(const [index,size,offset] of [[0,3,0],[1,4,12],[3,4,32]]){gl.enableVertexAttribArray(index);gl.vertexAttribPointer(index,size,gl.FLOAT,false,48,offset);}
                gl.enableVertexAttribArray(2);gl.vertexAttribIPointer(2,1,gl.UNSIGNED_INT,48,28);
                gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,gl.createBuffer());gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,new Uint16Array([0,1,2,0,2,3]),gl.STATIC_DRAW);
                function render(value,width,height,filter,tint,blend,flip,uvWidth=1,uvHeight=1){
                    const buffer=new ArrayBuffer(4*48),data=new DataView(buffer);
                    [[0,0,0,0],[width,0,1,0],[width,height,1,1],[0,height,0,1]].forEach(([x,y,u,v],i)=>{
                        const offset=i*48;[x,y,0,u*uvWidth,(flip?1-v:v)*uvHeight,0,0].forEach((n,j)=>data.setFloat32(offset+j*4,n,true));
                        data.setUint32(offset+28,2,true);tint.forEach((n,j)=>data.setFloat32(offset+32+j*4,n,true));
                    });
                    gl.bufferData(gl.ARRAY_BUFFER,buffer,gl.STREAM_DRAW);gl.useProgram(value);
                    gl.uniform3f(gl.getUniformLocation(value,'Scroll'),0,0,0);gl.uniform3f(gl.getUniformLocation(value,'p1'),2/width,2/height,0);
                    gl.uniform3f(gl.getUniformLocation(value,'p2'),-1,-1,0);gl.uniform1f(gl.getUniformLocation(value,'PaletteRows'),1);
                    gl.uniform1i(gl.getUniformLocation(value,'EnablePixelArtScaling'),filter);gl.uniform1i(gl.getUniformLocation(value,'EnableDepthPreview'),0);
                    gl.uniform1f(gl.getUniformLocation(value,'DepthTextureScale'),0);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,source);
                    gl.uniform1i(gl.getUniformLocation(value,'Texture0'),0);gl.viewport(0,0,width,height);
                    gl.clearColor(.02,.1,.23,.4);gl.clear(gl.COLOR_BUFFER_BIT);
                    if(blend){gl.enable(gl.BLEND);gl.blendFunc(gl.ONE,gl.ONE_MINUS_SRC_ALPHA);}else gl.disable(gl.BLEND);
                    gl.drawElements(gl.TRIANGLES,6,gl.UNSIGNED_SHORT,0);const pixels=new Uint8Array(width*height*4);
                    gl.readPixels(0,0,width,height,gl.RGBA,gl.UNSIGNED_BYTE,pixels);
                    if(gl.getError()!==gl.NO_ERROR)throw new Error('GL error in compositor fixture');return pixels;
                }
                let cases=0,bytes=0;
                for(const swap of [false,true]){
                    const original=program('combined',swap),optimized=program('framebuffer',swap);
                    for(const [width,height] of [[8,8],[16,16],[6,5],[64,32]])for(const filter of [false,true])
                    for(const tint of [[1,1,1,1],[.5,.75,1,.5],[.4,.6,.8,-.75]])for(const blend of [false,true])for(const flip of [false,true]){
                        const expected=render(original,width,height,filter,tint,blend,flip),actual=render(optimized,width,height,filter,tint,blend,flip);
                        for(let i=0;i<expected.length;i++)if(expected[i]!==actual[i])throw new Error(JSON.stringify({swap,width,height,filter,tint,blend,flip,byte:i,expected:expected[i],actual:actual[i]}));
                        cases++;bytes+=actual.length;
                    }
                }
                // Actual game-sized 1:1 subrect in a power-of-two framebuffer.
                const large=new Uint8Array(2048*1024*4);
                for(let i=0;i<large.length;i++)large[i]=fixture[i%fixture.length];
                gl.bindTexture(gl.TEXTURE_2D,source);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,2048,1024,0,gl.RGBA,gl.UNSIGNED_BYTE,large);
                gl.bindTexture(gl.TEXTURE_2D,target);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,2048,1024,0,gl.RGBA,gl.UNSIGNED_BYTE,null);
                for(const swap of [false,true]){
                    const original=program('combined',swap),optimized=program('framebuffer',swap);
                    for(const blend of [false,true])for(const flip of [false,true]){
                        const expected=render(original,1280,800,true,[1,1,1,1],blend,flip,1280/2048,800/1024);
                        const actual=render(optimized,1280,800,false,[1,1,1,1],blend,flip,1280/2048,800/1024);
                        for(let i=0;i<expected.length;i++)if(expected[i]!==actual[i])throw new Error(JSON.stringify({identity:true,swap,blend,flip,byte:i,expected:expected[i],actual:actual[i]}));
                        cases++;bytes+=actual.length;
                    }
                }
                return {status:'passed',cases,comparedBytes:bytes,exact:true};
            }''')
            out=ROOT/'.runtime/browser-compositor-evidence';out.mkdir(exist_ok=True)
            result['browser']=browser.version;(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
        finally:browser.close()
finally:server.shutdown();server.server_close()
