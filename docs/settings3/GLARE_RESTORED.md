# Original glare settings restored

Removed Double outline, Adaptive and the compact glare preview after beta 6.
Restored the three-option selector and original renderers from 7f73ce12c.
Existing preferences keep their original ordinals; removed values safely fall
back to Default through the original native enum/UI mapper.

No other beta 6 changes are reverted: vertical grouped style galleries, compact
group sender, composer position range, Floating header and animation fixes stay.
This source change does not modify the previously built beta 6 artifact.
No new APK or CI build is requested for this restoration.
