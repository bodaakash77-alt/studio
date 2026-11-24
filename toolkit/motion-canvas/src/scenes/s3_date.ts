import {makeScene2D, Layout, Txt} from '@motion-canvas/2d';
import {easeOutCubic, tween, waitFor} from '@motion-canvas/core';

export default makeScene2D(function* (view) {
  const words = ['On', 'July', '20,', '1969'];
  const nodes = words.map(w => new Txt({text: w, fontSize: 120, fontWeight: 800, fill: '#ffffff', opacity: 0}));
  view.add(
    new Layout({layout: true, direction: 'row', wrap: 'wrap', justifyContent: 'center', width: 900, gap: 28, children: nodes}),
  );
  // word by word
  for (const n of nodes) {
    yield* tween(0.35, value => n.opacity(easeOutCubic(value)));
    yield* waitFor(0.25);
  }
  yield* waitFor(1.5);
});
