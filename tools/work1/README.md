# Work 1 — three corrections over Work 2

Base is PR132 `3db6f7a87d147b84a628af7352299173424ce4f7`, with PR131 `0030904ae2e41d7720f43b7906c6a302ed339839` and PR130 `258dd3590f40ca0083a4b7bad6b413433c4e2c14` verified as ancestors. No main merge or Beta promotion.

## Tap diagnosis and correction

Alpha1286 disabled `tap_panel` by default. It also sent a background tap as `single=false,longpress=true`. `single=false` lets media message types reach multi-selection instead of the menu. Compact presentation required `longpress`.

The complete interaction now defaults ON only when `tap_panel` has no saved value. Explicit false remains false. Reset restores ON. The existing native RecyclerListView still arbitrates links/media/spoilers/polls/buttons, scroll, long press and selection. The actual eligible-cell callback calls the native menu with `single=true,longpress=false,bubbleTap=true`. A separate gesture-origin parameter selects compact presentation. It does not turn arbitrary taps into long presses. Long contacts, motion over slop, pointer changes, cancellation, reuse and pause clear eligibility. Repeated taps cannot replace or close an existing/pending tap menu.

The native reaction availability/permissions and `ReactionsContainerLayout` remain the authority. Explicit full tap requests enable the reaction presentation without depending on the old generic hide-on-tap preference; secret, scheduled, restricted and unavailable reactions remain unavailable. `fillMessageMenu` and fresh action permissions govern the vertical actions. More opens the retained native actions foreground, not a duplicate menu. The selected real bubble, scrim and existing SelectedBubbleMotion are coordinated by the existing menu owner/lifecycle.

## Bottom Bar

The Home-only lens renderer and backdrop capture are removed. Header/composer/other Glass remain unchanged. The legacy Java class/store names preserve preferences; there is no hidden optical switch. Equal slot allocation uses integer division plus at most one residual pixel per cell. Text widths never change slot or indicator widths. Icon labels hide in narrow slots, ultra compact mode or large font scale; accessible destination names remain. No selection/shape/blur render loop runs while idle.

A one-time migration retains the complete old destination order under `bottom_previous_destinations`, activates at most six destinations and preserves required Chats. Original order is recoverable via the stored preference; it is not discarded by reset. Nine real destinations remain reachable, with two to six visible cells. On exceptionally narrow windows a real More route keeps 48dp slots. Long-press Chats opens every non-visible real destination plus the folder selector. Add/remove/reorder/reset uses the native reorder editor and enforces the six-slot cap.

Appearance → Flexy Bottom Bar groups dimensions, tabs, selection and compaction. Width, height, radius, insets, icon size, labels, icon-label spacing, normal selection animation and bounded speed/smoothness are persisted. Normal/Compact/Ultra compact/Custom are supported. Height/compact padding edits select Custom automatically. Width cannot shrink below the touch target budget. The fictitious Home preview uses the production MainTabsLayout and destination factory without account avatars or conversations.

## Native sharing

Custom Share configuration/header/settings and exclusive translations are deleted. The settings entry and forwarding substitution are removed. ShareAlert restores the native implementation immediately before Alpha1286, retaining the source-account resolution before adapters/requests to preserve multi-account sharing. Native forwarding resumes its DialogsActivity flow. Message/send/search/recipient/restriction services are unchanged, including multi-account routing.

## Work 2 preservation

StartupAccounts, ApplicationLoader, ConnectionsManager, NetworkSnapshotAge, CoalescedTask, DialogCell, RecyclerListView, LaunchActivity, ScrollFrameRateHint, RefreshRateMonitor, SignatureBorderPath and BubbleTapMotion remain byte-identical to PR132. Only the explicitly discarded Home lens is removed from that optimization scope. Its historical benchmark is labelled as historical in tools/performance_p0, not a measurement of the new bar.

Official Beta package `com.flexygram.messenger`, version `1.0.0-beta.1` / code1287, PKCS12 alias `flexygram-release` and official certificate pin `5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c` remain unchanged. No new key is generated. Alpha code1287 uses its independent existing Alpha package/certificate; equal codes in different packages do not imply session/data migration.

## Validation and physical acceptance

Run `python3 tools/connected_alpha/run_checks.py`, `python3 tools/identity/check_identity.py`, `python3 tools/performance_p0/check_wiring.py`, `python3 tools/performance_p0/run_checks.py`, and the context_panel/liquid_navigation/interaction2 Android probes. Historical source audit manifests are preserved; work1_contract accepts only exact reviewed bytes and restores PR132 solely for old audit comparisons. These projections never enter Android execution.

Isolated Android probes run production layout/settings/springs and exact extracted cell/tap callback methods. Tab content, account services and menu creation are explicit doubles. Images are synthetic production-layout evidence, not whole-app screenshots. They cannot establish successful reaction transmission, complete real-chat menu display or Poco performance.

No ADB/physical phone is available here. Final acceptance requires a single DOWN/UP on eligible own and received messages in light/dark: compression → highlighted actual message + scrim → native reactions above + vertical options, functional reaction and permitted actions, close/Back, rapid taps, scroll/cancel/recycle/chat changes. Capture the whole gesture, not just rebound. Verify controls keep native behavior and long press remains distinct. This P0 acceptance is pending until exercised in the signed app on device.

For 2/3/4/5/6 tabs test real navigation, RTL, font scales1/1.3/2, label states, dimensions extremes, gesture insets, reordering/persistence/restart, open/close chats, fling/scroll and settings preview. Verify native sharing for text/photo/video/document, search/multiple recipients/restrictions and two accounts.

Use `tools/performance_p0` ABBA methodology with a provenance-pinned PR132 reference and this candidate: same package/cert, account corpus, network, theme/blur/wallpaper, battery/thermal and observed refresh policy, >=20 repetitions. Cold/warm startup, chat open, scroll jank and tap latency are NOT_MEASURED here. No synthetic operation count is presented as physical FPS.

Beta remains blocked until the owner's original PKCS12 is securely provisioned in an authorized environment, key/alias/certificate correspondence and custody are verified, Telegram and required Beta Firebase configuration exist, and real installation/coexistence/login/sharing/notifications/update are tested. Do not paste secrets into chat or replace the official key. A private Alpha validation build does not complete Beta acceptance.

## Variant validation graph correction discovered by the full build

AGP deduplicates the identical RelWithDebInfo CMake task across Alpha and Beta. The actual Alpha graph depended on preBetaBuild via that shared native task; PR131's preBetaBuild validator consequently demanded the official Beta PKCS12 during an Alpha build. No key was substituted and no APK was produced by that failed attempt; private inputs were wiped.

The Beta validation body, package, certificate, alias, private/public challenge, rejection of Alpha/debug, Firebase check and custody requirements remain byte-identical. Only task binding changes: mandatory dependencies now protect Beta BuildConfig, Firebase, signing, packaging and APK/AAB entry points. They cannot enter the Alpha graph through shared CMake. Alpha's existing independent validation remains mandatory. CI obtains both real AGP task graphs without executing private tasks and rejects any cross-variant validator or missing mandatory validator. This is not a signing bypass: neither validator has onlyIf/disabled/fallback logic.
