# Input backdrop, contour width and asynchronous message-menu blur

Update: the width slider/preference described below was cancelled before packaging. See [beta 8 fixed contour](BETA8_FIXED_GLARE.md). The input and async-menu corrections remain.

The compact composer had an extra 154/255 tint over the native blur provider's
own contrast surface. That compounded opacity hid much of the sampled backdrop.
Keep the existing provider/capture/island geometry and reduce only the additional
inset wash to 40/255, including the existing send-button usage. Solid fallback and
message-menu protection of the live input remain intact. No new blur engine.

Effects of glare retains its three original styles. A new row below Type opens
Outline thickness: a native slider from 0.5x to 3x in 0.1x steps. The dialog stages
changes until Done; Cancel keeps the saved value and Reset restores 1x. Values are
stored as 5..30 with default 10 in OEAppearanceGlassOutlineWidth, in the existing
AppearanceConfig store. Backup/Studio native metadata includes the bounded field;
settings/search ownership points to the same chat glare section.

Width updates dispatch the existing weak contour listeners. Retained drawables
scale nominal geometry once and rebuild/notify only on actual changes. Native
RenderNode paths use raw stroke helpers to avoid a second scale; public static
helpers scale borrowed Paint temporarily and restore its width in finally. Solid
and hidden paths keep their existing semantics. Default 1x glare algorithms remain
pixel-identical to the historical renderer in the isolated Android probe.

Compact menu preparation still snapshots Views on UI, once before showing the
popup. Pixel blur and both color matrices now run together on the existing theme
worker; only completed bitmap publication returns to UI. The old synchronous API
and classic menu path are preserved. The new async AndroidUtilities overload
explicitly delivers its intermediate callback on the worker. Stale/closed menu
owners reject and recycle published bitmaps. This reduces critical-path pixel work;
it does not remove the cost of creating menu Views or taking the initial snapshot.

A backdrop spring shares SelectedBubbleMotion's existing Choreographer callback.
Late results fade in without restarting card geometry or adding an animator. Frame
deltas use the callback's own time base with a small initial subframe, avoiding a
mixed clock origin. The clock remains independent of Reduce animations.

Checks: 298 policy/JVM tests passed, 31 skipped, nine subtests passed; 13 isolated
Android contour/dialog tests, 12 menu/capture/worker tests and five composer/folder
surface tests passed. Studio API37 host compilation and 32 client checks passed.
Tests use explicit service/queue hosts and native Android Canvas; they are not a
full application build, end-to-end GPU/device test or device FPS measurements.
No APK compiled. Physical-device validation remains pending.
