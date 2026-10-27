# Flexy Motion Engine — independent motion core (integration candidate)

**Branch:** `feature/flexy-motion-independent-core`, based on the immutable PR106
Alpha1278 candidate at `9d731fb471058c190ee571baea66e25836e044ea`.
**Status:** core source only; no APK/device demonstration, no global animation migration.

## Delivered

- `FlexyMotionProfile`: FLASH, FLOW (default), SIGNATURE physics constants.
- `FlexyMotionSpring`: bounded, allocation-free spring; retarget retains
  velocity. Stiffness and damping vary by selected profile.
- `FlexyFrameMotion`: lifecycle-bound `Choreographer` clock driven by frame
  timestamps, **not** `ValueAnimator` / `ObjectAnimator`. Stops on detach,
  interrupt/cancel/dispose supported. Main-thread-only.
- `FlexyMotionSettings`: local SharedPreferences, plus explicit reduced-motion
  preference. Does **not** write Android global settings or alter window scales.
- `FlexyTouchFeedback`: optional pressed-scale decorator for controls whose
  scale is not already owned by a conflicting animation. Does not consume
  touch events. The host must reset it on detach and dispose when abandoned.
- `test_flexy_motion.py`: compiles actual production spring/profile Java on
  JDK and verifies interrupted motion, 60/120 Hz and bounded large-frame deltas.

## Limitations: important

This branch does **not** replace the existing reaction `ObjectAnimator` in
PR106 or its notification lock logic. It cannot guarantee identical animations
on 0x, 0.5x, 1x, 2x and 5x in the application until Work 1 integrates individual
surfaces. Window, keyboard, third-party and system-owned animations remain OS
controlled. Accessibility needs a discoverable explicit reduce-motion option.

## Safe Work 1 integration order

1. Review PR106 reaction ownership/lifecycle and existing animator callbacks.
   Select **one progress owner** (never run two drivers on the same property).
2. Add a user-facing Motion section to the correct customization screen;
   use `FlexyMotionSettings.setProfile()` to update FLASH/FLOW/SIGNATURE.
   Expose `setReduceMotion()`. Preserve existing Studio import/export schemas
   until a deliberate migration and compatibility plan exist.
3. Replace just **one opt-in interaction** (e.g. a non-recycled isolated
   settings button). Forward `MotionEvent` without consuming it, cancel on
   ACTION_CANCEL, reset on view detach. Do not register duplicate listeners.
4. Switch reaction progress to `FlexyFrameMotion` only after the same
   notification-lock and transition-end cleanup is implemented; verify
   reverse mid-flight and no zombie callbacks.
5. Apply to chat navigation/tabs and composer incrementally with independent
   performance regression comparisons, respecting theme, RTL and touch hitbox.
6. Test native API 37 resource/build, host CI and physical Poco X8 Pro:
   Android 0x/0.5x/1x/2x/5x, FLASH/ FLOW/ SIGNATURE and explicit reduce-motion;
   repeated open/cancel/detach, multi-tap, chat scroll, IME and dark mode.

**Acceptance is measurable**, not claimed: comparable frame time/jank, no
crashes/freeze, no prolonged main-thread work, correct behavior with Android 0x.
Do not automatically merge into Alpha1278 or publish an unverified APK.
