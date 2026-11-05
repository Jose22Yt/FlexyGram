# Beta 7: selected-message menu motion

Version 1.0.0-beta.7 (1296), ARM64 UI test beta.

The compact path previously ran updateScrimSourceBitmap before popup construction
and captured again through dimBehindView after showAtLocation. Both use the same
synchronous global blur pipeline, so this duplicated capture/blur work and could
capture the menu itself. Compact menus now prepare one generation-guarded snapshot
before the popup is visible, only when effective chat blur is enabled. The original
classic menu flow remains separate. No extra bitmap engine or background loop is
introduced; the existing shared source and native surfaces are reused.

Compact setup no longer starts and immediately cancels a second AnimatorSet.
SelectedBubbleMotion owns card, reaction, selected-message and scrim progress.
The card is initialized hidden before showAtLocation to avoid a full-size flash.
Its reveal now scales from .94 instead of .62 and moves 8dp instead of 18dp.
Settling performs one redraw callback instead of two in the final frame.
The spring's own Choreographer clock and interruption/cleanup semantics remain
independent of FlexyStudio Reduce animations.

Includes source changes since beta 6: restoration of original glare options,
removal of glare preview, shared blur for all menu styles/More, live composer
scrim protection and folder accent/backdrop fixes.

Pre-build checks: 296 policy/JVM tests passed, 31 skipped, nine subtests passed;
nine isolated Android menu tests passed. Deterministic real-spring probes cover
30/60/90/120 Hz step sizes and single callback ownership; existing probes cover
60/90/120/144 Hz handoff/interruptions and motion-preference independence. Modified
production Java files passed Java21 syntax parsing. These are not device FPS,
end-to-end GPU blur or a guarantee of animation smoothness on every phone.

Uses the existing UI beta debug-signing pipeline, not the protected official
release signing workflow. Full assembly/artifact verification happen in CI.
