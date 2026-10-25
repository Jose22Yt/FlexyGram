# Next Alpha — stage A checkpoint

Base verified: PR91 / 8619ba40fbd8fd9d9d898ff307fb0c0716661254. PR89 and PR90 heads match the supplied references. Keep draft; no stable branch merge.

## P0 input ownership

The existing sibling-detach fix remains intact. A separate reproducible source path leaves DialogsActivity.blurredView VISIBLE with alpha zero and a click listener. MainTabsActivity receives onBecomeFullyVisible after preview close, but its ViewPagerActivity.FragmentState does not emit a child transition end if both springs complete before any fractional visibility update. A previously fully visible child also receives no new onBecomeFullyVisible in that sequence. The overlay's click handler only attempts to close a preview that no longer exists: the list below stays blocked, while the separate bottom tab bar can respond.

DialogsActivity now implements the existing TabFragmentDelegate.onParentBecomeFullyVisible ownership hook. It clears the overlay only when the shared navigation layout reports neither a preview nor a transition. Ordinary direct-fragment visibility uses the same idempotent cleanup. No timers, exception masking, animation removal, chat data, or navigation replacement.

`test_preview_input1273.py` executes the real FragmentState and MainTabs callback bodies with explicit UI doubles, comparing original1272 and candidate over2000cycles. Original: alpha-zero clickable overlay survives. Candidate: GONE, background released; active preview/transition preserved; repeated return harmless. This is a source behavior regression, not an Android framework touch or physical phone test.

Current stage: P0 source regression PASS; original source/security contracts retained through exact inverse patch. Native navigation/compilation checkpoint and physical Poco acceptance pending. New theme/header/Music3/blur work has not started in this checkpoint. No new APK exists yet.
