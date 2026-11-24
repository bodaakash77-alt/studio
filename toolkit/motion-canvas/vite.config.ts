import {defineConfig} from 'vite';
import * as mcPlugin from '@motion-canvas/vite-plugin';
import * as ffmpegPlugin from '@motion-canvas/ffmpeg';

// these packages are CommonJS: unwrap nested default exports until we reach the plugin factory
const unwrap = (m: any) => {
  let x = m;
  while (typeof x !== 'function' && x && x.default) x = x.default;
  return x;
};
const motionCanvas = unwrap(mcPlugin);
const ffmpeg = unwrap(ffmpegPlugin);

export default defineConfig({
  plugins: [
    motionCanvas({project: './src/project.ts', output: './output'}),
    ffmpeg(),
  ],
});
