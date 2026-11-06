# Beta 11 — common border controls on adaptive and legacy bubbles

Version 1.0.0-beta.11 (1300), ARM64 UI beta with debug signing.

Border enable/style/width/position/pearl/fusion controls remain available in both
surface modes. Only legacy fill transparency and cached wallpaper blur controls
remain specific to the previous effect. Switching materials does not reset any
border preferences.

MessageDrawable draws each fill independently, then runs the same native contour,
per-cell partial-path cache and fusion finish. Adaptive fill keeps its native
service material and selection; it does not acquire the old outgoing gradient or
its selection overlay. No additional blur cache, bitmap or per-frame shader is
introduced for this change.

Regression checks cover the production row factory and real Android Canvas draws
of MessageDrawable in both modes, styles, edge positions, fusion modes, dark/light,
incoming/outgoing and selected states, alpha, source callbacks and cache reuse.
Android theme/service hosts are explicit doubles; physical-device validation and
FPS measurements are not claimed.
