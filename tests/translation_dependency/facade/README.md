# Translation facade laboratory — P0.3f

Source facade for the **consumed** `app.nekogram.translator` ABI. This namespace is kept for linkage compatibility, not an application identity or attribution claim. Independent implementation by the FlexyGram project, responsible @Lukhou23; GPL-3.0 under the repository license. Original Exteraless/Nekogram credits are preserved.

This is a standalone Java module under tests. **It is not included in production settings, not a replacement for the active AAR, and not an authorized provider.** No transport implementing HTTP, JWT, credentials, service endpoints or branding identifiers is supplied.

- No-argument constructors and `getInstance()` always have no transport and fail closed.
- Additional constructors accept only the laboratory `FixtureTransport` contract and a cancellation probe. These constructors do not grant production policy authorization. Fake transports are defined in tests only.
- `DeepLTranslator.setJwt(String)` preserves the symbol but rejects every call without retaining its argument.
- Shared `BaseTranslator` ABI retains its protected Gson field and MD5 compatibility helper. Gson is an existing dependency supplied from a local file, not downloaded by this module.
- Request/response text is data, never diagnostics. Exceptions use fixed codes and bounded status numbers. Cancellation discards private messages and preserves interruption. There are no retries, fallbacks or provider remaps.

Build just the laboratory JAR:

```sh
GSON_JAR=/absolute/path/to/already-verified/gson.jar \
GRADLE_USER_HOME=/absolute/path/to/gradle-cache \
/path/to/gradle-9.7.1/bin/gradle --offline --no-daemon \
  -p tests/translation_dependency/facade clean jar
```

Set `JAVA_HOME` to JDK21. This command compiles `main` sources; it does **not** execute the parity harness. Run `test_facade.py` for executable tests, including API24 bootclasspath compilation and D8. See `docs/security-p03f/README.md` for exact environment and limits.

Do not put this JAR and the original AAR on the same classpath. They intentionally contain some identical binary class names. The binary-linkage tests compile against the old artifact and run against the facade in separate classpaths.
