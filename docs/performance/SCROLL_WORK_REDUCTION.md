# Scroll work reduction

The chat and dialog lists keep their native scrolling, touch handling, fling physics,
prefetch, recycling, and visual design. No scroll effects, springs, frame loops, or
display-mode overrides are added.

## Confirmed redundant work

- Chat scroll callbacks constructed new method-reference Runnables for both cancelling
  and scheduling the bot and saved-tag hints. Android removes callbacks by identity;
  those different objects did not cancel the queued checks. Stable callback instances
  now bound the pending work to one check per hint. Leaving or destroying the chat
  cancels them, and hint scans do not run during an active scroll or while paused.
- Translation checks no longer remove/repost a 150ms task on each scroll step or poll
  throughout a long fling. The existing idle notification schedules the final scan;
  explicit translation changes still use the immediate path.
- Native chat pagination now checks the existing load thresholds, in-flight flags and
  history-end flags before allocating/posting a UI task. Search/filtered results and
  merged histories retain their original native load paths. Queued loads recheck the
  paused, finished, frozen and synchronization states before accessing the controller.
- Dialog scroll handling reuses its already computed attached adapter range for
  pagination, eliminating two extra layout traversals. It avoids posting further
  folder/archive loads while the native controller already has one in progress.

## Verification

Executable Java probes use the production methods and scheduling blocks with fake
UI queues. They cover 10,000 scroll events, bounded hint queues, cancellation, idle
translation and explicit requests, both pagination directions, merged histories,
search, frozen/closed chats and independent folder/archive loading flags. The targeted
scroll/render regression run passed all 11 tests. The full regression suite completed
with 458 passed and 39 skipped.

These checks establish reduced scheduled work and preserved load behavior. Device
frame-time and touch-latency measurements are still needed to quantify the perceived
improvement. No APK or Gradle build was requested or run. The source commit uses
`[skip ci]` to avoid starting an APK build.
