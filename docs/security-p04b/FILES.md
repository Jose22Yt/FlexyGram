# Archivos de implementación y pruebas

Commit de código `c55915ce0bf9a820d4744a31f8c6aeddb80a1d02`: **29 archivos**. El movimiento del manifiesto conserva todos sus bytes; no elimina componentes de Diagnostic.

- `TMessagesProj/build.gradle`
- `TMessagesProj/jni/CMakeLists.txt`
- `TMessagesProj/jni/exports.map`
- `TMessagesProj/jni/tgnet/DiagnosticPolicy.h`
- `TMessagesProj/jni/tgnet/VariantPolicy.cpp`
- `TMessagesProj/jni/tgnet/VariantPolicy.generated.h.in`
- `TMessagesProj/jni/variant-policy.cmake`
- `TMessagesProj/src/diagnostic/AndroidManifest.xml`
- `TMessagesProj/src/main/AndroidManifest.xml`
- `TMessagesProj/src/main/java/org/telegram/messenger/BuildVariantPolicy.java`
- `TMessagesProj/src/main/res/xml/auth.xml`
- `TMessagesProj/src/main/res/xml/sync_contacts.xml`
- `TMessagesProj/src/production/AndroidManifest.xml`
- `config/flexygram-production.properties.example`
- `gradle.properties`
- `gradle/production-readiness.gradle`
- `gradle/variant-policy.gradle`
- `gradle/variant-policy.json`
- `tests/build_variants/check_diagnostic.py`
- `tests/build_variants/native_fixture.py`
- `tests/build_variants/reviewed_changes.json`
- `tests/build_variants/scope.py`
- `tests/build_variants/test_variants.py`
- `tests/security/test_p02_isolation.py`
- `tests/security/test_p03b_push.py`
- `tests/translation_dependency/test_facade.py`
- `tests/translation_safety/test_preparation.py`
- `tests/translation_staging/review_scope.py`
- `tests/translation_staging/test_staging.py`

La carpeta `docs/security-p04b/` contiene exclusivamente el informe y evidencias adicionales; su commit posterior no se presenta como una segunda compilación.
