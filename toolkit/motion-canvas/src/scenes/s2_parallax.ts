import {makeScene2D, Img} from '@motion-canvas/2d';
import {easeInOutCubic, tween, all} from '@motion-canvas/core';

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export default makeScene2D(function* (view) {
  const bg = new Img({src: '/img/bg.png', width: 1080, height: 1920, x: -20});
  const fg = new Img({src: '/img/fg.png', width: 760, x: -300, y: 60});
  yield view.add(bg);
  yield view.add(fg);
  // foreground moves much faster than background = parallax
  yield* all(
    tween(4, value => bg.x(lerp(-20, 20, easeInOutCubic(value)))),
    tween(4, value => fg.x(lerp(-300, 260, easeInOutCubic(value)))),
  );
});
