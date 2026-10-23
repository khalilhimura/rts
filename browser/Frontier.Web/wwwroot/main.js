// SPDX-License-Identifier: GPL-3.0-or-later
import { dotnet } from './_framework/dotnet.js';
import { attachInput } from './input.js';

const label = document.querySelector('#status');
const canvas = document.querySelector('canvas');
window.frontierGame = { status: 'loading', history: [], error: null };
canvas.addEventListener('webglcontextlost',event=>{
    event.preventDefault();
    fail(new Error('Graphics context lost. Choose New skirmish to reload the game.'));
});
const fontCanvas = document.createElement('canvas');
const context = fontCanvas.getContext('2d', { willReadFrequently: true });
function glyph(family, character, pixels) {
    if (!document.fonts.check(`${pixels}px "${family}"`)) throw new Error('Original font was not staged: '+family);
    context.font = `${pixels}px "${family}"`;
    context.fontKerning = 'none';
    const metrics = context.measureText(character);
    const left = Math.ceil(metrics.actualBoundingBoxLeft), right = Math.ceil(metrics.actualBoundingBoxRight);
    const ascent = Math.ceil(metrics.actualBoundingBoxAscent), descent = Math.ceil(metrics.actualBoundingBoxDescent);
    const width = Math.max(0,left+right), height = Math.max(0,ascent+descent);
    fontCanvas.width = Math.max(1,width); fontCanvas.height = Math.max(1,height);
    context.font = `${pixels}px "${family}"`; context.fontKerning = 'none';
    context.textBaseline = 'alphabetic'; context.fillStyle = '#fff';
    context.fillText(character,left,ascent);
    const alpha = new Uint8Array(width*height);
    if (width && height) {
        const rgba = context.getImageData(0,0,width,height).data;
        for (let i=0;i<alpha.length;i++) alpha[i]=rgba[i*4+3];
    }
    return JSON.stringify({width,height,x:-left,y:-ascent,advance:Math.floor(metrics.width),alpha:btoa(String.fromCharCode(...alpha))});
}

try {
    const runtime = await dotnet.withDiagnosticTracing(false).create();
    runtime.setModuleImports('frontier-fonts',{glyph});
    await runtime.runMain(runtime.getConfig().mainAssemblyName,[]);
    const api=(await runtime.getAssemblyExports(runtime.getConfig().mainAssemblyName)).Frontier.Web.Program;
    const manifest=await fetch('./content-manifest.json').then(r=>r.json());
    label.textContent='Staging original game files…';
    for (const file of manifest.files) {
        const response=await fetch('./content/'+file.path);
        if (!response.ok) throw new Error(`Missing ${file.path}: HTTP ${response.status}`);
        const bytes=new Uint8Array(await response.arrayBuffer());
        const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),b=>b.toString(16).padStart(2,'0')).join('');
        if (hash!==file.sha256) throw new Error('Content integrity mismatch: '+file.path);
        api.Stage(file.path,bytes);
        if (file.path.endsWith('.ttf')) {
            const face=new FontFace('Frontier_'+hash,bytes);
            await face.load(); document.fonts.add(face);
        }
    }
    label.textContent='Starting Salt Basin…';
    attachInput(canvas,api);
    const result=api.Start();
    if (result!=='OK') throw new Error(result);
    window.frontierGame.status='running';
    let observedAt=0, reportedAt=0, callbacks=0, totalStepMs=0, maxStepMs=0;
    const startedAt=performance.now();
    function frame(now) {
        if (window.frontierGame.status!=='running') return;
        try {
            const stepStart=performance.now();
            if (api.Step()) { location.reload(); return; }
            const stepMs=performance.now()-stepStart;
            callbacks++; totalStepMs+=stepMs; maxStepMs=Math.max(maxStepMs,stepMs);
            if (now-observedAt>1000) {
                const state=JSON.parse(api.State());
                window.frontierGame.history.push(state);
                if (window.frontierGame.history.length>1000) window.frontierGame.history.shift();
                window.frontierGame.latest=state;
                const elapsedMs=performance.now()-startedAt;
                window.frontierGame.metrics={elapsedMs,ticksPerSecond:state.tick*1000/elapsedMs,
                    callbacksPerSecond:callbacks*1000/elapsedMs,meanStepMs:totalStepMs/callbacks,maxStepMs};
                label.textContent='Salt Basin · Frontier Collective';
                if (now-reportedAt>10000) {
                    console.info('FRONTIER_BROWSER_STATE '+JSON.stringify(state));
                    reportedAt=now;
                }
                observedAt=now;
            }
            requestAnimationFrame(frame);
        } catch(error) { fail(error); }
    }
    requestAnimationFrame(frame);
} catch(error) { fail(error); }

function fail(error) {
    window.frontierGame.status='failed';window.frontierGame.error=String(error);
    label.textContent=String(error).includes('Graphics context lost')
        ? 'Graphics context lost. Choose New skirmish to restart.'
        : 'Unable to run this skirmish. Choose New skirmish to retry.';
    console.error(error);
}
