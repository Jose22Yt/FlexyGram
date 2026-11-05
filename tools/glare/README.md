# Original glare effects restored

Only Disabled, Default and Solid outline remain. Their preference values and
native drawing match commit 7f73ce12c. Double/Adaptive rendering and the compact
glare preview are removed. Existing stored values 3/4 resolve to the original
default through the existing bounds-safe native enum and UI mapper.

The isolated Android fixture retains focused app host doubles; production
controller/mapper/static draw methods are compiled against the real Android
Canvas. It does not build an APK or run the full app on a device.
