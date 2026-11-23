# SculptGL (mobile Chrome) — face/statue sculpt

1. Open https://stephomi.github.io/sculptgl/ in Chrome (mobile).
2. Tap the menu, `Open` and load a base mesh (a sphere from the menu's "Primitives" or your own .obj/.glb).
3. Use Inflate and Smooth brushes to shape a head: brow ridge, nose, cheeks, chin.
4. Export: menu, `Export` as .obj (or .stl). Keep the file under 50 MB.
5. Import the .obj into the Three.js or Babylon scene (or into Blender in Colab) for rendering.

Limits: SculptGL is a sculpting tool, not a renderer. Textures and rigs are not handled. Verify it works on your device before relying on it, since this file was not tested in a mobile browser.
