# Beta 10 — adaptive bubbles and complete message selections

Version 1.0.0-beta.10 (1299), ARM64 UI beta with debug signing.

Integrates Codex 2 source 56db7f21295b921fd577f5e2c9015f5d932b1b3a with the
user's timestamp exception: both directions use the native incoming timestamp
colors from the chat theme/provider, including selection. Adaptive text/status
icons can use the service material ink; timestamp rendering bypasses that override.
The preview uses the same native timestamp policy. Media timestamps keep native
media/service behavior.

Full-sized selected messages, reactions and actions now scroll together instead
of cropping/shrinking a bubble to reserve room for actions. The real composer is
drawn above the captured menu backdrop, retaining its own native glass and state.
Opening focus targets the scroll container to avoid jumping directly to actions.

The adaptive material is the default; the previous effect remains selectable and
its preferences are retained. No device FPS or full visual validation is claimed.
