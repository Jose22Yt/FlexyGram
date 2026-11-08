# Lyrics runtime regression

Run with JDK 17+, Maven, Android API 37 and build-tools 36:

```sh
python tools/connected_alpha/lyrics_runtime/run.py --sdk-root "$ANDROID_HOME"
```

Tests compile the complete production `OnlineLyrics` and `Lyrics` classes and
run them under Robolectric Android API 35. HTTPS responses and the worker queue
are explicit fixtures. No request goes to a live lyrics service in these tests.

Coverage includes metadata matching, album-specific cache keys, duplicate
requests, cancellation before/during a fetch, malformed/oversized responses,
retry after network failure, expiring negative results and plain-lyrics fallback.
The music visual probe separately exercises actual player widgets, extracted
production layout, Android touches, theme contrast, blur lifecycle and timer.
These checks do not certify a packaged application or a physical Android device.
