# Telegram session core — preparación P3/P4

Núcleo Java independiente para FlexyGram (@Lukhou23), bajo la licencia del repositorio. Conserva la procedencia Exteraless / Telegram. **No está registrado en settings.gradle ni incluido en el APK.** No tiene dependencias externas ni implementación MTProto/Android.

- `SessionScope`: variante/paquete/slot inmutables; diez slots, ligados por prueba al UserConfig original.
- `ClosedRuntime`: valida configuración cerrada y coherencia de atestación; todas las operaciones Telegram se deniegan. Una cadena de atestación no concede permisos.
- `RequestCoordinator`: puerto tipado, comprobación de dominio y cuenta, tickets con propietario, respuesta única, cancelación y limpieza. El dominio TELEGRAM no llega a initialize/submit con la política actual. Solo existen adaptadores ficticios en tests.
- `AuthenticationController`: fases locales, sesión vacía, cancelación, generación de peticiones, staging y commit explícito CAS; fallo ambiguo de escritura queda STORAGE_UNCERTAIN, sin reintentos ni borrado.
- `AuthUiRelay`: eventos de estado sin secretos, enlace reemplazable al recrear Activity, descarte por revisión y liberación del observador. No sondeo/timers ni hilos propios. El adaptador Android futuro deberá aportar su ejecutor serial del hilo principal; initialize/commit de almacenamiento deben ejecutarse fuera de ese hilo.

Ejecutar desde la raíz, con JDK21, Python3.11, Gradle9.7.1 (solo su intérprete Groovy) y CMake3.31.6:

```sh
python3.11 -m unittest discover -s tests/session_core -v
python3.11 -O -m unittest discover -s tests/session_core -v
```

Variables: `JAVA_HOME`, `FLEXYGRAM_GRADLE_HOME` y `FLEXYGRAM_CMAKE`. No se resuelven dependencias Gradle, no se genera APK y no se usa una cuenta. Ver `docs/session-core/README.md` para auditoría, límites y traspaso. Los parches de `patches/session-core/` **no se aplican automáticamente**.
