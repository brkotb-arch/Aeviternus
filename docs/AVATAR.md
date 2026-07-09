# SVG Avatar — Reactive Visual Interface

## Overview

The Aeviternus web interface includes a **Reactive Avatar Layer**: a lightweight, dependency-free visual component that reflects runtime mood and expression state through inline SVG and DOM manipulation.

This is not a separate rendering engine. It is a **Runtime Visual Interface** embedded directly in the chat template — a vector face controlled by JavaScript state mapping and CSS-bound theming.

### What it is

- **Inline SVG Rendering** — the avatar is defined as markup inside `templates/chat.html`, not loaded from external image assets
- **DOM-controlled vector interface** — facial geometry is mutated at runtime via SVG attribute updates
- **No external image assets** — no PNG, GIF, or sprite sheets
- **No canvas or WebGL dependency** — pure SVG + CSS + JavaScript

### Source files

| File | Role |
|------|------|
| `templates/chat.html` | SVG markup, mood controls, state wiring |
| `static/avatar_engine.js` | Expression mapping, blinking, procedural animation |
| `static/style.css` | Theme binding, glow effects, mood-dependent styling |

---

## Architecture

The avatar system is organized into three layers:

### SVG Layer

The face is composed of individually addressable SVG elements, each assigned a stable `id` for DOM targeting:

| Element | SVG type | Purpose |
|---------|----------|---------|
| `head` | `<ellipse>` | Face outline |
| `eye_left`, `eye_right` | `<ellipse>` | Eye shapes |
| `pupil_left`, `pupil_right` | `<circle>` | Pupil position and size |
| `lid_left`, `lid_right` | `<ellipse>` | Eyelids (blink animation) |
| `brow_left`, `brow_right` | `<path>` | Eyebrow curves |
| `mouth` | `<path>` | Mouth curve |
| `nose` | `<path>` | Nose outline |

The SVG uses a fixed `viewBox="0 0 200 280"` coordinate space. All expression changes operate within this coordinate system.

### CSS Layer

CSS provides **CSS-bound Theming** and ambient visual context:

- **Theme binding** — three body classes (`theme-purple`, `theme-red`, `theme-dark`) set CSS custom properties for the avatar panel:
  - `--avatar-panel-bg`
  - `--avatar-panel-border`
  - `--avatar-svg-glow`
- **Visual transitions** — `transition` rules on the avatar panel and SVG filter for smooth theme changes
- **Glow effects** — `filter: drop-shadow(...)` on `.avatar-panel svg` using theme variables
- **Mood-dependent styling** — `.chat-container[data-mood="..."]` selectors apply border and box-shadow colors that correspond to each expression state

Theme selection is persisted in `localStorage` and cycled via the header theme button.

### JavaScript Layer

`static/avatar_engine.js` implements **Procedural DOM Animation** and **State-driven Expression Mapping**:

- `FACE_PARTS` — base geometry registry for each facial element
- `FACE_EXPRESSIONS` — lookup table mapping state names to parameter overrides
- `resetFace()` — restores all elements to base geometry and styling
- `applyExpression(state)` — applies a named expression via SVG attribute mutation
- `startBlinking()` — periodic eyelid opacity animation
- `startChaosMode()` / `stopChaosMode()` — procedural jitter via `requestAnimationFrame`

Public API (exported to `window`):

- `applyExpression(state)`
- `startBlinking()`

---

## State Flow

The avatar reacts to mood/expression state from two sources: manual user selection and server-detected mood in chat responses.

```
Runtime State (mood / expression)
        |
        v
Mood / Expression State
  (NEUTRAL, SASS_ON, DARK, SOFT, FOCUS, CHAOS)
        |
        v
switchState() in chat.html
  - sets data-mood on .chat-container
  - updates header label
  - calls applyExpression(state)
        |
        v
avatar_engine.js
  - resetFace()
  - apply FACE_EXPRESSIONS[state]
  - or startChaosMode() for CHAOS
        |
        v
SVG DOM mutation
  (setAttribute on path d, opacity, transform)
        |
        v
Visual expression
  + CSS mood glow on chat container
  + CSS theme glow on avatar panel
```

**Manual input:** mood bar buttons call `switchState()` with the selected state.

**Server input:** when `/send` returns a `mood` field, `chat.html` calls `switchState(data.mood)` to synchronize the avatar with the Cognitive Pipeline output.

---

## Expression Mapping

Each expression state maps to specific visual parameters. All non-CHAOS states modify eyebrow curve control points and mouth path data (`d` attribute).

### NEUTRAL

Default resting expression. Symmetric eyebrows at standard height. Neutral mouth curve (`M 74,164 Q 88,168 100,164`).

### SASS_ON

Asymmetric eyebrows — left brow raised, right brow lowered. Mouth curve adjusted with an additional quadratic segment for a sharper contour.

### DARK

Both eyebrows lowered and compressed inward. Mouth path flattened slightly downward.

### SOFT

Both eyebrows raised symmetrically. Mouth curve deepened for a softer arc.

### FOCUS

Eyebrows drawn closer together and lowered. Mouth narrowed to a tighter horizontal curve.

### CHAOS

No static expression table entry (`FACE_EXPRESSIONS.CHAOS = null`). Instead, **Procedural DOM Animation** applies random `translate()` transforms to brows, eyes, mouth, and nose on every animation frame via `requestAnimationFrame`. Previous transforms are cleared when switching away from CHAOS.

---

## Blinking

Blinking is implemented as **eyelid opacity changes** on a timed loop:

1. `startBlinking()` registers a `setInterval` callback
2. Interval duration: `3500 + Math.random() * 2000` ms (3.5–5.5 seconds)
3. On each tick, both `lid_left` and `lid_right` opacity is set to `0.5`
4. After 150 ms, opacity is restored to `0`
5. Eyes remain visible underneath; lids overlay the eye ellipses

This produces a lightweight periodic blink without path morphing or keyframe libraries.

---

## Design Rationale

This architecture was chosen for the following engineering properties:

| Property | Benefit |
|----------|---------|
| **Lightweight** | Single JS file (~170 lines), no animation framework |
| **Dependency-free** | No canvas library, no WebGL, no image pipeline |
| **Inspectable** | SVG elements visible in DevTools; state changes are attribute-level |
| **Extensible** | New expressions added by extending `FACE_EXPRESSIONS`; new parts added to `FACE_PARTS` and SVG markup |

The avatar is a visual indicator of runtime state — not a separate application layer. It integrates with the existing mood system and web interface without introducing additional runtime dependencies.

---

## Related Documentation

- [Architecture Showcase](SHOWCASE.md) — system overview for engineers and researchers
- [Cognitive Architecture](COGNITION.md) — Cognitive Pipeline and mood detection
- [Identity System](IDENTITY.md) — Identity Core and behavioral continuity
