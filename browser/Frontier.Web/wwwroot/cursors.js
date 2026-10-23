// SPDX-License-Identifier: GPL-3.0-or-later
// Reuse the engine's BGRA cursor frames and hotspot, scoped to this canvas.
// The OS/browser moves this one cursor without waiting for a game frame.
export function createCursorBridge(canvas) {
    const cursors = new Map();
    let nextId = 1, currentId = 0, pointerOutside = false;
    function apply() {
        if (pointerOutside) {
            canvas.style.cursor = 'auto';
            canvas.dataset.cursorMode = 'outside';
            return;
        }
        const cursor = cursors.get(currentId);
        if (!cursor) {
            canvas.style.cursor = 'none';
            canvas.dataset.cursorMode = 'hidden';
            return;
        }
        const ratio = canvas.getBoundingClientRect().width / canvas.width;
        const scale = Math.min(ratio * (cursor.pixelDouble ? 2 : 1), 128 / Math.max(cursor.width, cursor.height));
        const width = Math.max(1, Math.round(cursor.width * scale));
        const height = Math.max(1, Math.round(cursor.height * scale));
        const key = `${width}x${height}`;
        if (!cursor.variants.has(key)) {
            const image = document.createElement('canvas');
            image.width = width; image.height = height;
            const context = image.getContext('2d');
            context.imageSmoothingEnabled = false;
            context.drawImage(cursor.image, 0, 0, width, height);
            const x = Math.min(width - 1, Math.max(0, Math.round(cursor.x * width / cursor.width)));
            const y = Math.min(height - 1, Math.max(0, Math.round(cursor.y * height / cursor.height)));
            cursor.variants.set(key, `url("${image.toDataURL('image/png')}") ${x} ${y}, default`);
        }
        canvas.style.cursor = cursor.variants.get(key);
        canvas.dataset.cursorMode = 'browser';
    }
    canvas.addEventListener('pointerenter',()=>{pointerOutside=false;apply();});
    canvas.addEventListener('pointerleave',()=>{pointerOutside=true;apply();});
    canvas.addEventListener('pointermove',event=>{
        // Pointer capture keeps delivering a drag outside canvas bounds.
        const bounds=canvas.getBoundingClientRect();
        const outside=event.clientX<bounds.left || event.clientX>=bounds.right || event.clientY<bounds.top || event.clientY>=bounds.bottom;
        if (outside!==pointerOutside) { pointerOutside=outside;apply(); }
    });
    new ResizeObserver(apply).observe(canvas);
    return {
        create(bgra, width, height, x, y, pixelDouble) {
            if (width <= 0 || height <= 0 || bgra.length !== width * height * 4)
                throw new Error('Invalid engine cursor frame');
            const image = document.createElement('canvas');
            image.width = width; image.height = height;
            const rgba = new Uint8ClampedArray(bgra.length);
            for (let i = 0; i < rgba.length; i += 4) {
                rgba[i] = bgra[i + 2]; rgba[i + 1] = bgra[i + 1];
                rgba[i + 2] = bgra[i]; rgba[i + 3] = bgra[i + 3];
            }
            image.getContext('2d').putImageData(new ImageData(rgba, width, height), 0, 0);
            const id = nextId++;
            cursors.set(id, {image, width, height, x, y, pixelDouble, variants: new Map()});
            return id;
        },
        set(id) {
            if (id === currentId) return;
            currentId = id;
            apply();
        },
        dispose(id) {
            cursors.delete(id);
            if (id === currentId) { currentId = 0; apply(); }
        },
    };
}
