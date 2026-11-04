# Reversible Reduce animations and independent bubble motion

`FastMotionConfig` routes preference changes, reloads and listener notifications
through `FastMotion.setEnabled`. Turning reduction off restores tracked native
animator/property/legacy durations and delays immediately, including property
animations which can auto-start without another call to `View.animate()`.

Framework animators also restore timings when finished, so cached objects and
clones made after completion retain their nominal values. AnimatorSet children
record the inherited nominal duration before receiving the reduced duration.
A shared cleanup listener preserves application listeners and guards restarts.
The ASM visitor handles `reverse()` as well as `start()` so reversing a restored
animator still follows the selected policy. No global Android setting is written.

The press and selected-bubble springs use their own frame clock and local limits
(280ms entry, 180ms exit). Reduce animations and developer animation scales do not
change those trajectories. Native animation/accessibility opt-outs remain respected.
Closing still releases touch/scroll ownership before the visual return, and a new
DOWN can finish that return with exactly one cleanup callback.

Checks without building an APK:

```sh
python tools/connected_alpha/fast_motion/run.py --sdk-root "$ANDROID_HOME"
python -m pytest tests/test_fast_motion.py tests/test_context_motion_responsiveness.py -q
```

The Android fixture tests production runtime/configuration against API35 animators
and preferences; dynamic-animation Spring types are compile doubles. The host probe
executes production bubble springs at simulated 60/90/120/144Hz, compares trajectories
across preference/scale values and checks interruption and callback ownership.
Neither check measures physical-device FPS or full-app visual behavior.
