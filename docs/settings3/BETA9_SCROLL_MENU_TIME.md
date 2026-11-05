# Beta 9 — readable timestamps, menu previews and scroll work

Version 1.0.0-beta.9 (1298), ARM64 UI test beta with debug signing.

- Generated outgoing gradient themes use secondary timestamp ink instead of primary
  message white; distinct theme timestamp colors and native media rendering remain.
- Message-menu backdrop covers the composer, without changing live input alpha.
- Large selected messages keep a minimum 0.9 preview scale and scroll within the
  reserved viewport; reaction bar remains above it and action cards below it.
- Dialog-list blur capture runs once per root draw after header geometry updates.
- Automatic translation scans wait until dragging/flinging stops; explicit
  translation requests remain immediate and queued work is cancelled on destroy.
- Integrates Codex 2 source 4a1fdd168112577f587cf7a3017eb0d31277c450:
  homepage, credits, contribution/build/security documentation, local configuration
  exclusions and workflow environment handling. Existing beta configuration and
  UI debug build route are preserved.

Host tests and isolated Android tests do not establish physical-device FPS,
zero latency, complete visual correctness or official distribution signing.
