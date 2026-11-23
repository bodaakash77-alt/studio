# studio

Free documentary/motion studio. Works from mobile Chrome, GitHub and Google Colab. Nothing needs to be installed on a PC.

## Contents
- `library/` — CC0 / public domain assets (HDRI, matcaps, 3D fonts, India state map, world maps). See `library/LICENSES.md`.
- `tools/search.py` — `python tools/search.py "sunset warm"`, `python tools/search.py andhra`.
- `toolkit/blender/blender_script.py` — Blender script (EEVEE, 1080x1920). Presets: push_in, pull_out, orbit, crane, drone, top_down. Run in Colab (see below).
- `toolkit/threejs/` — Three.js scene (open `index.html` in Chrome, or host on GitHub Pages).
- `toolkit/babylon/scene.js` — paste into https://playground.babylonjs.com/.
- `toolkit/sculptgl/README.md` — sculpting in mobile Chrome.
- `toolkit/openreel/plan.md` — assembling clips in OpenReel.
- `toolkit/colab/blender_colab.ipynb` — free Colab render.
- `captions_example.srt`, `scene_example.json` — caption and scene formats.
- `docs/README.md` — workflow and license rules.

## Use on mobile Chrome only
1. Colab: open `toolkit/colab/blender_colab.ipynb` from GitHub in Colab, then Run all.
2. Babylon: copy `toolkit/babylon/scene.js` into the Playground and press Run.
3. Three.js: open the GitHub Pages link for `toolkit/threejs/`.

## Limits
- The Blender test render uses placeholder geometry, not a finished character model.
- Three.js and Babylon scenes were syntax-checked only; they have not been run in a mobile browser from this workspace.
- Colab Blender render needs a runtime with xvfb; untested in Colab from this workspace.
- Poly Haven, ambientCG, Freesound are not in the library yet; download them and attach to add.
