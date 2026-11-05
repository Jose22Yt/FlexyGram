# Blur coverage review

Reviewed the existing native blur routes for the home bottom dock, chat composer,
chat header and upper folder tabs. SharedConfig.chatBlurEnabled accepts either
chat blur or Liquid Glass; refraction remains governed separately by Liquid Glass.
Existing source factories, capture positions, theme updates and solid fallbacks
remain intact. No extra blur engine, capture or animation loop is introduced.

The home dock uses its retained composite source and MainTabsLayout background.
The chat header exits its custom solid drawing after a native backdrop is drawn.
The composer uses its retained shared blur source and individual island drawables,
including its stable tint. The message-menu input protection from a2f985d40 stays.
Native GPU rendering follows existing platform/source availability; unavailable
paths keep their solid fallback.

Fixed folder selection painting: the selected pill previously blended a second
almost-opaque or fully opaque surface over native blur. Native selection now draws
only a capped translucent accent tint with selection progress. Solid mode is
unchanged. Two cached palettes resolve selected ink and badge colors against the
composited glass tint; no color-search allocations/work are added per draw. The
Dialogs power-policy refresh invalidates retained folder child display lists via
updateColors so changes take effect without needing to scroll the tabs.

Verification: 294 policy/JVM tests passed, 31 skipped, nine subtests passed; four
native Android Canvas surface tests passed. The new cases check that selected
folders retain backdrop visibility through transition progress, solid fallback
is opaque and cached selected ink meets 4.5 contrast on the tested composited
surfaces. The existing composer source-change/empty-source cases remain passing.
Four production Java files passed Java21 syntax parsing.

These are isolated renderer/policy checks with explicit native service doubles,
not a device run of the full GPU blur pipeline or proof of FPS on every phone.
Device validation remains pending. No APK generated for this source change.
