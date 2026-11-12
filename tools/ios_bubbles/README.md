# Telegram iPhone bubble geometry

Original upstream Swift remains unmodified under `upstream/`; `provenance.json` records the immutable repository commit, source path, hash, default radii and cap coordinates. Android implementation: `IosBubbleShape.java`. Source and graphics are retained with attribution to TelegramMessenger/Telegram-iOS.

The native unit runner builds a JVM test harness, never an APK:

```bash
python tools/ios_bubbles/run_native.py --android-jar /path/to/android.jar --maven mvn --output /tmp/flexy-style-tests
```

Requires JDK21, Maven, network for test dependencies and Android SDK35. It reuses explicit isolated Telegram hosts from the existing graphics harness; Android paths, Skia rendering, layouts and accessibility are real Robolectric APIs. The service wallpaper provider is a fallback double, so this does not validate real wallpaper blur or the entire Telegram activity. Preview tick drawables are Android fixture resources, not a fidelity check of the status icons. No login/account/network-message behavior is mocked as device acceptance.
