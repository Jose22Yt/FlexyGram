# Current beta corrections

These changes are based on `codex/flexygram-beta-glass` at
`6342e1d4603b41fc37f6a34d02475edf6205ec83`, rather than the `main`
checkout that was initially used. They are developed on the local branch
`fix/current-beta-ui-retention`. They do not change the beta build workflow
or its signing configuration.

The initial edits are retained in the `work` branch's stash and in the verified
archive at `/workspace/.flexygram/recovery/20261103T161523Z/` in this environment.
The new implementation keeps the beta's Signature header, composer, native glass
surfaces and embedded settings controllers.

## Adapted behavior

- The actual Signature unread badge follows the theme accent, chooses contrasting
  text, and uses its own text paint. The count sums unread messages in the current
  folder/filter, without counting archive summary rows twice.
- Composer AI/editor actions are available through the attachment long press and
  text selection menu. A compact expand control appears after three lines; AI
  visibility no longer forces the contact composer to switch layout. The beta's
  existing guard against repeated height-animation restarts is retained.
- Channel capsules use the same retained native blur/border surfaces as contact
  conversations. Hardware/blur-disabled cases retain their readable fallback.
- AyuMoments completes the local preservation operation before the queued storage
  deletion. Empty channels/groups also consult preserved history. Chat exclusions,
  manual deletion and bot preferences remain in effect.
- The actual Signature settings screen has no introductory subtitle. Its category
  order follows the approved Personalization / Tools / System and Data /
  Information groups. Root and embedded navigation icons use small outline
  resources and the active theme foreground. Existing callbacks and licenses are
  preserved.

## Validation limits

The complete host suite passed: **228 passed, 31 skipped**. Skips cover unavailable
external plugin corpora and generated artifacts. Tests include the beta's existing
suites and focused regressions for the adapted behavior. Java syntax and the new vector/string resources are checked.
The actual `Settings2Cell` is also type-checked against Android API 37 with project
services stubbed. These checks do not replace a complete Android application
compilation, a real Room database test, or testing rendering/IME behavior on a
device. No APK was built as part of this migration.

To repeat host tests with the environment's installed JDK:

```sh
export JAVA_HOME=/workspace/.flexygram/jdk/jbrsdk-21.0.11-linux-x64-b1163.125
export PATH="$JAVA_HOME/bin:$PATH"
/workspace/.flexygram/venv/bin/python -m pytest tests/ -q -ra \
  -o cache_dir=/workspace/.flexygram/pytest-cache
```

The active beta uses the modern Signature classes under `app/flexygram`; its
`app/exteraless/settings/OpenExteraSettingsActivity` class is a compatibility
alias. Future UI changes must target the live implementation and preserve this
alias for existing links/plugins.
