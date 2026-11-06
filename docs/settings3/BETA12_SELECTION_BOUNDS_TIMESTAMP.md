# Beta 12 — selection bounds and optional compact timestamps

Version 1.0.0-beta.12 (1301), ARM64 UI test beta with debug signing.

Selection rendering scopes fullyDraw across the parent background and all message
content. Native alpha layers no longer restrict the relocated selection to its
original RecyclerView viewport. Ordinary scrolling rows keep their original clips.
Popup alignment is reconciled after actual window layout using screen coordinates
for the popup, content root, source cell and gap; scroll offsets remain independent.
Opening focus prefers the scrolling container instead of moving past a long message.

Includes the optional small_timestamp control in Bubble settings, both materials:
9dp/body color enabled by default; disabled copies the native time paint size and
uses Telegram/Exteraless direction/selection colors through the chat theme provider.
Existing cells remeasure on rebind when the mode changes. Backup records the setting;
profiles containing smallTimestamp require build1301. No new logging system.

The latest user video exceeded the 32MiB transfer limit and could not be inspected.
These fixes address observed source clipping/window alignment; exact equivalence to
that video and physical-device validation are not claimed. Android Canvas tests use
production snippets with explicit host doubles; no FPS claim is made.
