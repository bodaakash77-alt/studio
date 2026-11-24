import {makeScene2D, Img} from '@motion-canvas/2d';
import {easeOutCubic, tween, waitFor} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const tv = new Img({src: '/img/tv.png', width: 1000, scale: 0.9, opacity: 0});
  yield view.add(tv);
  yield* tween(0.8, value => tv.opacity(easeOutCubic(value)));
  yield* tween(4.2, value => tv.scale(0.9 + 0.1 * value));
  yield* waitFor(0.3);
});
