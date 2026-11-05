# Passive touch and composer surface regression

- ChatMessageCell no longer starts BubbleTapMotion from ACTION_DOWN for text or
  media. Gesture recognition, native media handling and the confirmed context-menu
  admission remain in place. Cancellation resets rather than rebounds the cell.
- SelectedBubbleMotion remains the owner of the confirmed menu/reaction transition;
  it is still independent of FlexyStudio Reduce animations.
- Compact composer islands retain their native blur and contour. A reused Paint
  draws an inset, theme-based tint over each present island, so a changed/empty
  captured backdrop cannot make the input surface disappear. Its alpha follows
  the existing input hide factor; hidden actions leave no tinted ghosts.
- No extra bitmap, capture, animator, listener or UI preference is introduced.

Verification without building an APK:

```sh
python -m pytest tests/test_bubble_scroll_feedback.py -q
python tools/connected_alpha/composer_surface/run.py --sdk-root "$ANDROID_HOME"
```

The gesture probe executes the live observer/classifier methods with explicit
native-dispatch doubles, including short tap, drag, cancellation, multitouch and
long press. The raster fixture executes production surface methods on real API35
Canvas/Paint, with native blur replaced by a deliberately empty/changing source.
Full-client device validation remains pending; these tests do not reproduce the
complete recording or measure frame performance.
