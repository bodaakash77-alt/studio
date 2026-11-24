# Motion Canvas — studio motion-graphics engine

Free, open-source (MIT) motion graphics. Scenes are TypeScript code, so you can edit timing, easing and layout directly.

Source: https://github.com/motion-canvas/motion-canvas
Pinned here: `@motion-canvas/*` 3.17.2, vite 5.4.11.

## What's in this example (1080x1920, 9:16, 30 fps, about 18 s)

| Scene | File | What it does |
|---|---|---|
| 1 | `src/scenes/s1_newspaper.ts` | Newspaper "MAN WALKS ON THE MOON", slow 5 s push-in zoom |
| 2 | `src/scenes/s2_parallax.ts` | Photo parallax: foreground moves faster than background |
| 3 | `src/scenes/s3_date.ts` | "On July 20, 1969" appears word by word |
| 4 | `src/scenes/s4_tv.ts` | Old TV frame with the rocket launch inside |

Images are placeholders in `public/img/` (newspaper.png, bg.png, fg.png, tv.png). Replace them with real files of the same names.

## Open it on your phone (Chrome)

**Option A: StackBlitz (no install).**
1. Open `https://stackblitz.com/github/bodaakash77-alt/studio/tree/main/toolkit/motion-canvas`
2. Wait for the install to finish, then the preview loads.
3. Press play to preview. Use the editor's render/export button to save an MP4.

**Option B: GitHub Codespaces.**
1. On the repo page, open the `toolkit/motion-canvas` folder and choose Code → Codespaces → Create.
2. In the terminal run `npm install` then `npm start`.
3. Open the forwarded port 9000, press play, and export.

## Notes
- Export runs in the editor and uses the `@motion-canvas/ffmpeg` plugin. If the MP4 export fails in your environment, export the PNG image sequence and tell me, and I'll convert it.
- To add a scene: create `src/scenes/<name>.ts`, then import it with `?scene` in `src/project.ts` and add it to `scenes`.
- Node references are used directly (`const x = new Img(...); yield view.add(x);`). Yield after `view.add` for images so they are loaded before you touch their properties.
