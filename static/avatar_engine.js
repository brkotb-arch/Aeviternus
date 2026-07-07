// Файл: avatar_engine.js
// Файл: avatar_engine.js
const FACE_PARTS = {
    brow_left: { path: 'brow_left', base: { x: [46, 62, 78], y: [94, 86, 94] } },
    brow_right: { path: 'brow_right', base: { x: [98, 114, 128], y: [94, 86, 94] } },
    eye_left: { path: 'eye_left', base: { cx: 58, cy: 108, rx: 10, ry: 4 } },
    eye_right: { path: 'eye_right', base: { cx: 118, cy: 108, rx: 10, ry: 4 } },
    mouth: { path: 'mouth', base: { d: 'M 74,164 Q 88,168 100,164' } },
    nose: { path: 'nose', base: { d: 'M 88,108 Q 87,118 86,120 Q 85,126 84,130 Q 87,132 88,132 Q 89,132 92,130 Q 91,126 90,120 Q 89,118 88,108 Z' } },
    lid_left: { path: 'lid_left', base: { opacity: 0 } },
    lid_right: { path: 'lid_right', base: { opacity: 0 } },
};

const FACE_EXPRESSIONS = {
    NEUTRAL: {
        brow_left: { x: [46, 62, 78], y: [94, 86, 94] },
        brow_right: { x: [98, 114, 128], y: [94, 86, 94] },
        mouth: { d: 'M 74,164 Q 88,168 100,164' },
    },
    SASS_ON: {
        brow_left: { x: [46, 62, 78], y: [92, 84, 92] },
        brow_right: { x: [98, 114, 130], y: [98, 104, 98] },
        mouth: { d: 'M 74,164 Q 80,160 86,165 Q 93,170 100,166' },
    },
    DARK: {
        brow_left: { x: [52, 66, 76], y: [98, 100, 100] },
        brow_right: { x: [100, 110, 122], y: [104, 104, 102] },
        mouth: { d: 'M 72,166 Q 86,168 100,166' },
    },
    SOFT: {
        brow_left: { x: [46, 62, 78], y: [92, 84, 92] },
        brow_right: { x: [98, 114, 128], y: [92, 84, 92] },
        mouth: { d: 'M 74,164 Q 88,170 100,164' },
    },
    CHAOS: null,
    FOCUS: {
        brow_left: { x: [50, 66, 74], y: [98, 100, 98] },
        brow_right: { x: [102, 110, 126], y: [98, 100, 98] },
        mouth: { d: 'M 78,163 Q 88,164 94,163' },
    },
};

function resetFace() {
    Object.values(FACE_PARTS).forEach(p => {
        const el = document.getElementById(p.path);
        if (!el) return;
        if (p.base.opacity !== undefined) {
            el.setAttribute('opacity', p.base.opacity);
        } else if (p.base.cx !== undefined) {
            el.setAttribute('cx', p.base.cx);
            el.setAttribute('cy', p.base.cy);
            el.setAttribute('rx', p.base.rx);
            el.setAttribute('ry', p.base.ry);
            el.setAttribute('fill', '#d0c0e0');
        } else if (p.base.d) {
            el.setAttribute('d', p.base.d);
            el.setAttribute('stroke', '#b07060');
            el.setAttribute('stroke-width', '1.8');
            el.setAttribute('fill', 'none');
            el.setAttribute('stroke-linecap', 'round');
        } else if (p.base.x) {
            const xs = p.base.x, ys = p.base.y;
            el.setAttribute('d', `M${xs[0]},${ys[0]} Q${xs[1]},${ys[1]} ${xs[2]},${ys[2]}`);
            el.setAttribute('stroke', '#c0c0d0');
            el.setAttribute('stroke-width', '2');
            el.setAttribute('fill', 'none');
        }
    });
    const nose = document.getElementById('nose');
    if (nose) {
        nose.setAttribute('d', 'M 88,108 Q 87,118 86,120 Q 85,126 84,130 Q 87,132 88,132 Q 89,132 92,130 Q 91,126 90,120 Q 89,118 88,108 Z');
        nose.setAttribute('stroke', '#8a7a8a');
        nose.setAttribute('stroke-width', '1.2');
        nose.setAttribute('fill', 'none');
        nose.setAttribute('stroke-linecap', 'round');
        nose.setAttribute('opacity', '0.6');
    }
    const pupilL = document.getElementById('pupil_left');
    const pupilR = document.getElementById('pupil_right');
    if (pupilL) { 
        pupilL.setAttribute('cx', '59'); 
        pupilL.setAttribute('cy', '109'); 
        pupilL.setAttribute('fill', '#050510');
        pupilL.setAttribute('r', '3.5');
    }
    if (pupilR) { 
        pupilR.setAttribute('cx', '117'); 
        pupilR.setAttribute('cy', '109'); 
        pupilR.setAttribute('fill', '#050510');
        pupilR.setAttribute('r', '3.5');
    }
}

function applyExpression(state) {
    stopChaosMode();
    resetFace();

    const expr = FACE_EXPRESSIONS[state];
    if (!expr) {
        if (state === 'CHAOS') startChaosMode();
        return;
    }

    Object.entries(expr).forEach(([part, mods]) => {
        if (part === 'mouth') {
            const el = document.getElementById('mouth');
            if (el && mods.d) {
                el.setAttribute('d', mods.d);
                el.setAttribute('stroke', '#b07060');
                el.setAttribute('stroke-width', '1.8');
                el.setAttribute('fill', 'none');
                el.setAttribute('stroke-linecap', 'round');
            }
            return;
        }
        const el = document.getElementById(part);
        if (!el) return;
        const base = FACE_PARTS[part]?.base;
        if (!base) return;
        if (base.cx !== undefined) return;
        const xs = mods.x || base.x;
        const ys = mods.y || base.y;
        if (xs && ys) {
            const curve = mods.curve || 'Q';
            el.setAttribute('d', `M${xs[0]},${ys[0]} ${curve}${xs[1]},${ys[1]} ${xs[2]},${ys[2]}`);
            el.setAttribute('stroke', '#c0c0d0');
            el.setAttribute('stroke-width', '2');
            el.setAttribute('fill', 'none');
        }
    });
}

let blinkInterval = null;
function startBlinking() {
    if (blinkInterval) clearInterval(blinkInterval);
    blinkInterval = setInterval(() => {
        ['lid_left', 'lid_right'].forEach(id => {
            const lid = document.getElementById(id);
            if (!lid) return;
            lid.setAttribute('opacity', '0.5');
            setTimeout(() => lid.setAttribute('opacity', '0'), 150);
        });
    }, 3500 + Math.random() * 2000);
}

let chaosRAF = null;
function startChaosMode() {
    stopChaosMode();
    const parts = ['brow_left', 'brow_right', 'mouth', 'eye_left', 'eye_right', 'nose'];
    function jitter() {
        parts.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            const dx = (Math.random() - 0.5) * 6;
            const dy = (Math.random() - 0.5) * 6;
            el.setAttribute('transform', `translate(${dx}, ${dy})`);
        });
        chaosRAF = requestAnimationFrame(jitter);
    }
    chaosRAF = requestAnimationFrame(jitter);
}
function stopChaosMode() {
    if (chaosRAF) {
        cancelAnimationFrame(chaosRAF);
        chaosRAF = null;
    }
    ['brow_left', 'brow_right', 'mouth', 'eye_left', 'eye_right', 'nose'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.setAttribute('transform', '');
    });
}

window.applyExpression = applyExpression;
window.startBlinking = startBlinking;
window.drawHair = drawHair;
window.drawMouth = drawMouth;