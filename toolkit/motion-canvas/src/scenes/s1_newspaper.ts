import {makeScene2D, Img} from '@motion-canvas/2d';
import {easeInOutCubic, tween, waitFor} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const paper = new Img({src: '/img/newspaper.png', width: 900, scale: 1.0});
  yield view.add(paper);
  // slow push-in zoom over 5 seconds
  yield* tween(5, value => paper.scale(1.0 + 0.12 * easeInOutCubic(value)));
  yield* waitFor(0.2);
});
