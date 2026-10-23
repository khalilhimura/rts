import { dotnet } from './_framework/dotnet.js';

const output = document.querySelector('#result');
const started = performance.now();
window.frontierProbe = { status: 'loading', playable: false };
try {
    const runtime = await dotnet.withDiagnosticTracing(false).create();
    await runtime.runMain(runtime.getConfig().mainAssemblyName, []);
    const exports = await runtime.getAssemblyExports(runtime.getConfig().mainAssemblyName);
    const api = exports.Frontier.Browser.Probe.Program;
    const fetchChecked = async name => {
        const response = await fetch(`./content/${name}`);
        if (!response.ok) throw new Error(`${name}: HTTP ${response.status}`);
        return response;
    };
    const [rules, map, sprite] = await Promise.all([
        fetchChecked('actors.yaml').then(r => r.text()),
        fetchChecked('map.yaml').then(r => r.text()),
        fetchChecked('scout.png').then(r => r.arrayBuffer()),
    ]);
    const report = JSON.parse(api.Inspect(rules, map, new Uint8Array(sprite)));
    const rgba = Uint8Array.from(atob(report.rgba), c => c.charCodeAt(0));
    delete report.rgba;
    const canvas = document.querySelector('canvas');
    const gl = canvas.getContext('webgl2', { antialias: false, preserveDrawingBuffer: true });
    if (!gl) throw new Error('WebGL2 unavailable');
    const shader = (kind, source) => {
        const value = gl.createShader(kind);
        gl.shaderSource(value, source); gl.compileShader(value);
        if (!gl.getShaderParameter(value, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(value));
        return value;
    };
    const program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, `#version 300 es
    out vec2 uv; void main() {
        vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2);
        uv = vec2(p.x, 1.0-p.y); gl_Position=vec4(p*2.0-1.0,0,1);
    }`));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `#version 300 es
    precision mediump float; uniform sampler2D sheet; in vec2 uv; out vec4 pixel;
    void main() { pixel=texture(sheet,uv); }`));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    gl.useProgram(program);
    gl.bindVertexArray(gl.createVertexArray());
    gl.bindTexture(gl.TEXTURE_2D, gl.createTexture());
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, report.width, report.height, 0, gl.RGBA, gl.UNSIGNED_BYTE, rgba);
    gl.viewport(0, 0, canvas.width, canvas.height);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    const readback = new Uint8Array(rgba.length);
    gl.readPixels(0, 0, canvas.width, canvas.height, gl.RGBA, gl.UNSIGNED_BYTE, readback);
    for (let y = 0; y < canvas.height; y++)
        for (let x = 0; x < canvas.width*4; x++)
            if (rgba[y*canvas.width*4+x] !== readback[(canvas.height-1-y)*canvas.width*4+x])
                throw new Error(`WebGL RGBA roundtrip mismatch at row ${y}, byte ${x}`);
    if (gl.getError() !== gl.NO_ERROR) throw new Error('WebGL error after original asset upload');
    report.webgl = 'full-sheet RGBA readback matches OpenRA decoder';
    // A warmed lower-bound JS/.NET boundary measurement, not a pathfinding
    // benchmark and not a measurement of a second Rust module or buffer copies.
    for (let i = 0; i < 1000; i++) api.RoundTrip(i);
    const interopStarted = performance.now();
    for (let i = 0; i < 10000; i++)
        if (api.RoundTrip(i) !== i) throw new Error('Primitive interop mismatch');
    report.primitiveInterop10000Ms = performance.now()-interopStarted;
    report.bootMs = performance.now()-started;
    window.frontierProbe = { status: 'passed', playable: false, report, inputs: [] };
    canvas.addEventListener('contextmenu', event => event.preventDefault());
    canvas.addEventListener('pointerdown', event => {
        const rect = canvas.getBoundingClientRect();
        const input = JSON.parse(api.Pointer(Math.floor((event.clientX-rect.left)*canvas.width/rect.width),
            Math.floor((event.clientY-rect.top)*canvas.height/rect.height), event.button));
        window.frontierProbe.inputs.push(input);
    });
    output.textContent = JSON.stringify(report, null, 2)+'\nProbe passed. Full game boot and gameplay remain unimplemented.';
} catch (error) {
    window.frontierProbe = { status: 'failed', playable: false, error: String(error) };
    output.textContent = String(error); console.error(error);
}
