# Message menu blur and live composer protection

All four compact message-menu presentations (List, Grid, Groups, Toolbar) use
individual native blur3 surfaces when the effective chat blur gate is enabled.
The gate includes the power-saving blur/Liquid Glass flags and existing per-theme
availability policy. Menu surfaces share scrimBlur3Factory and its existing bitmap;
no capture, blur worker, animation or bitmap allocation is added by each card.

The opaque popup backing is cleared for all compact presentations. List owns its
single rounded background; the other styles own each group/card. The More page
also owns its background and its content container stays transparent. When blur
is unavailable, the existing theme-colored backgrounds remain available.

The message selection scrim previously painted a full-screen captured background
over the live input. Native glass can be absent from that snapshot, making the
composer appear transparent despite its own stable tint. Clip the scrim/message
redraw region above the current visible input bubble top, then restore Canvas
before drawing the remaining foreground controls. The actual input is neither
redrawn twice nor assigned a different alpha. Non-message scrims and hidden input
retain their original full-screen region. Recompute the bound each draw so it
follows the keyboard/layout, without new layout requests or frame allocations.

Validation: 292 policy/JVM tests passed, 31 skipped, nine subtests passed. Seven
isolated native Android menu tests passed, including all styles, shared surface
injection, solid fallback and a Canvas regression for preserving the live input
against an opaque captured scrim. Three modified Java production files passed
Java21 syntax parsing. The Android fixture uses explicit Telegram service hosts;
it does not run ChatActivity or its real GPU blur pipeline on a phone.

No APK compiled. Device checks remain pending for keyboard movement, message-menu
opening/closing, themes, effective battery-saving settings and real backdrop blur.
