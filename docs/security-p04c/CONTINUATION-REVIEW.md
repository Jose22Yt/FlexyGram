# P0.4c — Continuación de seguridad y estado de verificación

Responsable: @Lukhou23. Fecha: 19 de octubre de 2026.
Base aprobada: merge de P0.4b en develop, `ab063041804674861e865364206c0ef27ef1e953`.
Trabajo de Work recuperado: `03ee4e03a3497f9082e564b257f7313bbef536ca`, rama `security/paso-3-p04c-android-native-compatibility`.

## Alcance de esta continuación

- Se conserva el cambio original de Work: `ANDROID_PLATFORM=android-24` (frente a minSdk 24), lock Python con versiones y hashes, auditoría estática ELF/API24 y pruebas sintéticas.
- Se cierra una condición permisiva en `tools/native_compatibility/wheelhouse.py`: anteriormente se filtraban solo `*.whl` en el directorio de salida; otros archivos, directorios o symlinks podían permanecer en una ubicación utilizada después por pip mediante `--find-links`.
- Se rechazan **todas** las entradas del directorio que no sean archivos regulares de wheel con nombre listado; se rechazan symlinks tanto en salida como en caché. El comportamiento normal de caché offline y las verificaciones SHA-256/CRC se conservan.
- Se añadieron seis regresiones independientes en `tests/native_compatibility/test_wheelhouse_hardening.py`.
- Se actualizó el hash esperado y la trazabilidad explícita de `tests/native_compatibility/reviewed_changes.json` sin tocar los snapshots históricos de P0.3g/P0.4b.

## Resultados realmente ejecutados

La revisión de esta continuación se hizo con acceso GitHub a la fuente y un entorno Python local aislado, **sin** checkout Android completo ni descarga de artefactos externos.

- `python -m unittest -v test_wheelhouse_hardening` (con la versión exacta de la herramienta copiada del HEAD y los cambios anteriores): **6/6 aprobadas**, 0 fallos (Python 3.13 del host de revisión). Las pruebas no realizan peticiones de red.
- `python -m compileall` de la herramienta y pruebas: **aprobado**.
- No se han ejecutado las pruebas completas de P0.4c/P0.4b en este entorno: falta pyelftools y un checkout completo para las comprobaciones de alcance de Git.
- No se ejecutó Gradle ni se compiló una APK en esta continuación. No se contaba con SDK/NDK/CMake Android, wrapper recuperado o emulador, ni acceso al APK interno de Work.
- No se ha probado en Android: la revisión de imports nativos del API 24, la carga JNI/Chaquopy, la compatibilidad real de páginas de 16 KB, ni la navegación y rendimiento siguen abiertos.

## Gates antes de aprobar la integración a develop

1. En un entorno recuperado y autorizado, comprobar wheelhouse con Python 3.11 y hashes de los 18 paquetes fijados para ARM64 y, por separado, x86_64. Validar que pip instala desde `--no-index --require-hashes` y sin resolución externa no autorizada.
2. Ejecutar **toda** la batería original de pruebas (102 de P0.4b) y los casos nuevos de `tests/native_compatibility`. Registrar resultados reales en logs y resumen por commit. No reutilizar como prueba actual el resultado histórico.
3. Compilar **`:TMessagesProj:assembleDiagnosticDebug` con `NATIVE_TARGET=arm64-v8a`, CMake/JNI y Chaquopy sin SKIP; verificar firma de laboratorio, identidad/manifest, APK SHA-256 y guardas de transporte.
4. Rechazar de nuevo las tareas productivas (bloqueo `FLEXYGRAM_PRODUCTION_INCOMPLETE`); comprobar que Diagnostic no tenga INTERNET, autenticación, push, plugins, traducción ni restablecimiento de sesiones.
5. Inspeccionar *cada* ELF de la nueva APK, incluidos los extraídos de los IMY de Python. Alinear `ANDROID_PLATFORM` con minSdk no demuestra que todos los prebuilts sean cargables en API24.
6. Siguen sin corregirse con un lock de hashes las cuatro librerías Python PT_LOAD de 4 KB: libexslt, libfreetype, libxml2 y libxslt. Conservar los avisos RELRO y probar en Android ARM64 con páginas 4 KB y 16 KB antes de certificar compatibilidad.
7. Obtener instalación, arranque, cargas JNI/Python y logs reales de un Android autorizado. No usar cuentas, tokens ni credenciales reales para la variante de diagnóstico.
8. Revisar los hallazgos y obtener aprobación expresa del propietario antes de cualquier fusión. **No iniciar PASO 4**.

Esta continuación está preparada como **PR en borrador**, no como validación de P0.4c ni como autorización para fusionarlo. No se han activado GitHub Actions ni publicado APK/Releases. `main` y `develop` no deben cambiar.
