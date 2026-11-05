# Beta 6 integration

Version 1.0.0-beta.6 (1295), ARM64 UI beta build.

Merged Codex 2 delivery b877ee8fe9d70d691a6c398c59d22ee6b3bf8e55 into
codex/flexygram-beta-glass without replacing this branch's header, animation,
composer surface or bubble touch fixes.

Conflict resolutions retain the five glare choices and the centered inline
Floating status. Preview padding is reduced to 12dp, without reintroducing the
old detached status. The new glare sample uses the actual contour renderer for
Double/Adaptive with its own alpha, rather than borrowing the legacy glare paint's
opacity. The adaptive sample uses its available theme/surface color.

Includes grouped vertical previews, in-pill group sender selection and the
extended composer vertical range. The minimum position intentionally permits the
composer to move offscreen; native layout reservation remains nonnegative.

Pre-build verification: 295 policy/JVM tests passed, 31 skipped, nine subtests;
32 Studio client checks and API37 isolated Studio compilation passed. Four native
Floating preview/header tests and fourteen native glare tests passed. Updated
historical native test expectations for reduced preview padding and automatic
restoration of nominal animator timing after completion. Full app compilation and
APK verification are separate pipeline stages; these tests are not device testing.

Uses the existing ui-beta-debug.yml ARM64 pipeline and its existing debug signing
identity, like the previous UI beta; this is not the protected official release
signing workflow. Physical device visual/gesture/IME validation remains pending.
