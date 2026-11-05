# Beta 8: fixed subtle contour, input blur and menu response

Version 1.0.0-beta.8 (1297), ARM64 UI test beta.

User cancelled contour-width customization before it was packaged. Restore the
original three-choice glare page (Disabled, Default, Solid), with no width row,
slider, extra preference, export metadata or search entry. The old unused width
preference, if present in a development environment, is not read. Keep only a fixed
1.10x contour emphasis: modestly thicker edges, without changing blur radius,
opacity, shadow, effect types or adding a preview. Retained/native/static renderers
apply this factor once, preserve borrowed Paint state and respect Hidden mode.

Includes 19d38b8dc's other corrections: lighter additional composer wash, worker
pixel processing and single-owner menu/backdrop crossfade. The existing real
snapshot of Views still runs on UI; pixel blur and color transforms do not hold
up menu animation. No device FPS or zero-latency claim is made.

The earlier adjustable-width report describes development history only and is
superseded by this decision. Uses the existing debug-signing UI beta pipeline,
not the protected official release-signing workflow. Device verification pending.
