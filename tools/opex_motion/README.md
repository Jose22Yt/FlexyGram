# Opexgram reference motion — Alpha1289 candidate

Base: Alpha1288 / PR135, a56b816d1e2166a72cda075d80be8b6e3b1073ca.
Reference: owner-uploaded 50124(9).mp4, 19.319 seconds, 1268 x 2756.
Inspected overview and 30-samples/second opening around 1.1–1.9 seconds.
The private reference itself and its frames are not committed.

The reference shows a selected message between a reaction pill above and an
action card below. The card expands visibly from the message side; the shell
and content settle after a small overshoot. Recorded emoji playback is distinct
from the shell motion. The video does not reveal source spring constants,
touch timestamps or actual device frame pacing, so pixel-perfect equivalence
and maximum physical FPS cannot be established from this recording.

Alpha1288's card only grew from 96% to 100%, and its selected-message spatial
progress was clamped, suppressing the spring overshoot. This candidate grows
the card from 62%, pivoting at the selected outgoing/incoming message edge.
One frame owner drives the selected bubble, card and reaction shell, using a
500-stiffness/.60-damping phase spring. Spatial progress preserves overshoot;
opacity and native reaction reveal are bounded. The native reaction pill puts
overshoot on the entire view, keeping emojis and background together without
making its native reveal rectangle exceed its width. Smooth bounded translation
keeps a tall preview's rebound within 4 dp of its fitted destination, avoiding
overlap with the reaction pill. Native emoji playback and reaction actions
are preserved. Press and handoff springs share damping
and keep current position/velocity. The first frame uses elapsed monotonic
time rather than an assumed 120 Hz time step.

Calibrated host trajectory at simulated 60/90/120/144 Hz peaks at 1.076–1.079
around 167 ms and settles around 492–500 ms. The card's actual overshoot is
about 3%; reaction shell about 2%. These are source-model measurements,
not Android/device FPS or a measured match to Opexgram. Existing host probes
also exercise interrupted closing, lifecycle cleanup, bounded geometry and
no callbacks at rest. Full Java, Android isolated regressions, native ARM64
build and APK signature verification remain separate gates.

Classic, native action permissions, media taps, reduced-motion/accessibility,
Work2 startup/network/scroll, fixed default Home, composer and Beta identity
remain unchanged. Physical acceptance needs a side-by-side capture on the
Poco with own/incoming text and media, small/tall/edge messages, repeated taps,
Back/outside during entry/exit, chat switch, keyboard and motion reduction.
Compare compression, card/pill growth, first peak, settling and continuous
return; collect frame timing separately. No exact visual match is claimed.
