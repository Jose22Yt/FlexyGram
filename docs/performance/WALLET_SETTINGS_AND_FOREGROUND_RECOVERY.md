# Wallet settings and foreground recovery

## Money / Dinero

The wallet entry was unconditionally forced on, even when Telegram's account configuration disabled `wallet_available`. It now follows the server/cached boolean and defaults to unavailable until configured. This does not emulate availability, balances or server support.

Read-only wallet state loading now has explicit request ownership, a 20-second timeout and a retry action. Failure notifies the UI instead of leaving the initial skeleton active. A response from a timed-out, cancelled or superseded request cannot replace the newer state. Temporary RPC failure retains the existing wallet data and the native preservation of a recently streamed balance. Server wallet creation is rechecked only while a wallet page listens, with at most ten responses before a manual retry is required. Closing the page stops the creation poll; account cleanup cancels its pending timeout/request.

Wallet engine initialization errors, including unavailable native linkage, are shown as a recoverable state. A wallet that is still being prepared, an empty wallet and unavailable functionality have distinct messages. Empty wallets offer the existing native create/import flows, triggered only by the user's corresponding button; no new wallet is created automatically. Sending and topping up remain disabled until the wallet is ready and available.

Transaction pagination and refresh now set their in-flight flags before dispatch, reject duplicate requests, and ignore cancelled results. Network failure does not masquerade as the end of history. It exposes Retry and stops automatic load-more/error loops and placeholder rows. Cached history stays visible. An ordinary background refresh retains the native pagination/loading distinction to avoid replacing cached empty-history content with a spinner. Balance-only updates do not rebuild status/history rows.

The native settings list now listens for wallet balance/configuration changes. Settings navigation and wallet child navigation use their owning account; the birthday selector's state comes from that account too. Collectible sender initialization sets the account before looking up its source address.

No signing, transaction preparation/submission, encryption, secret storage or balance arithmetic was changed. Tests use synthetic read-only responses; no live wallet, funds or recovery phrase was used.

## First screen and foreground resume

Cold startup requests the selected account's native local dialog list before starting
the plugin engine. UI startup queues pending-send initialization on the main handler,
so another account's sender/media setup cannot precede that local request. Background
callers retain their direct initialization path; queued sender work checks that the
account still has a user before proceeding. This does not gate synchronization or
pending sends on a display frame or a network response.

The bottom bar updates its layout parameters only when its search margins actually
change. Refreshing its colors and corner radius invalidates drawing without requesting
an additional layout; geometry setters remain responsible for actual size changes.

The native foreground network resume starts before plugin and theme work. The second `resumeNetworkMaybe` call was removed because `setAppPaused(false, false)` already resumes the native network.

The native dialog sorter marks work pending when its existing background guard skips a sort. Foreground entry sorts only if pending or dialogs have not loaded; quick returns with unchanged data reuse the existing ordered lists. Background message changes still force the native sort before fragments resume. Message synchronization, difference loading, network sleep and connectivity checks remain active.

The initial-data Updating label has a 350ms delay. Cached data, a connection change, pausing or destruction cancel the pending label refresh. Once cached dialogs publish, the overlay text is updated without waiting for the network state to change. Sustained real initial synchronization and offline/proxy failures remain visible. There is at most one pending label callback; no polling or frame callbacks were introduced.

## Verification without APK

Executable Java probes exercise the actual read-only request methods, history loading/cancellation methods, configuration boolean and navigation methods, plus the production load/status classes. Cases cover timeouts, stale responses, duplicate dispatch, retries, streamed balance preservation, bounded wallet creation polling, account ownership, paused dialog sorting, status text and callback cleanup. XML resources are checked in English and Spanish.

The integrated regression run completed with 464 passed and 39 skipped. Startup probes execute the production account initialization helpers with controlled UI queues, covering selected-account priority, background entry, pending sends and logout before callback dispatch. Bottom-bar probes cover unchanged margins, RTL, search visibility and theme/radius refresh without additional layout requests. No Gradle/APK build, live transaction or device startup-time/FPS measurement was performed. Pushes use `[skip ci]`.
