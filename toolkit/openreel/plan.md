# OpenReel (mobile Chrome) — assembling clips

Verification status: this plan was NOT tested in OpenReel (the site was not reachable from this workspace). Check the current UI before following it.

1. Open https://openreel.video/ in Chrome and create a project: 1080 x 1920, 30 fps.
2. Import in order: rendered scene MP4s, the voice-over file, caption track (captions_example.srt or your own).
3. Put clips on the timeline using scene_example.json: each scene's start_time and end_time.
4. Captions: white bold text, black outline, bottom center, 1–2 words per frame.
5. Fallback if clips can't be arranged: use a single image per scene with a slow zoom (2.5D) and export.
6. Export MP4 (H.264), 1080x1920.
