# Workflow

1. Write the script and split it into scenes (`scene_example.json`).
2. Record or attach the voice-over. Build captions (`captions_example.srt`): word-by-word, white bold, black outline, bottom center.
3. Search the library: `python tools/search.py <words>`.
4. Make each scene: MAP scenes use 2D map + outline + cartoon face (no 3D); CHARACTER scenes use 3D character + simple background.
5. Render (Colab/Blender, Babylon, Three.js), arrange in OpenReel, export 1080x1920, 30 fps.

# License rules
- CC0 / public domain / commercial-use-permitted only. Unknown licenses are skipped.
- A repository's code license does not cover its media. Check each file.
- Record attribution in `catalog/manifest.json` (field `attribution`).

# Limits
- No PC needed, but Colab and Babylon are the heaviest steps; expect long waits.
- Caption and camera presets are simple; they are not finished production scenes.
