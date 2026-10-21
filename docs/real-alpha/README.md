# FlexyGram realAlpha: P1/P2 native integration, external capabilities closed

Responsable de FlexyGram: @Lukhou23. Base de código: Exteraless / Telegram; se conservan las licencias, créditos y autoría originales. Base exacta de esta rama: `2d532562f68946a83f5cdd2fc1059e3024beb525`. El HEAD observado de PR #33, `06d661126e9b958bc208c815a316360b5658c0a4`, solo añade las evidencias de la compilación anterior. PR #23 observado: `090b907cfd305614130fe35340bd148bc247dcff`.

## Código integrado

- Variante opt-in `realAlphaDebug`, paquete `io.github.jose22yt.flexygram.realalpha`, sin firma. `-PflexygramRealAlpha=true` y `NATIVE_TARGET=arm64-v8a` obligatorios. El validador Groovy exige identidad exacta, aislamiento y seis capacidades booleanas falsas; no lee credenciales privadas.
- `RealAlphaActivity` hereda **LaunchActivity real**. Su raíz es **DialogsActivity real**, con la lista vacía y los controladores originales. No usa BetaPreviewActivity, vistas sintéticas, un usuario ficticio ni datos de otra aplicación. El único cambio de Java compartido es hacer `getClientNotActivatedFragment()` protegido, conservando su implementación anterior para las demás variantes.
- Arranque mediante ApplicationLoader, comprobación de JNI cargado y adquisición explícita de AccountInstance / MessagesController / MessagesStorage / ConnectionsManager. RealAlphaBootstrap comprueba todos los slots antes/después; rechaza identidades presentes, inicialización parcial y reentrada. No borra, importa ni revoca sesiones. Verifica tanto el getter como el campo legado `clientUserId`, porque `getClientUserId()` devuelve cero cuando `currentUser` es null.
- Solo se admite DialogsActivity en las dos entradas del delegado de navegación. LoginActivity, SessionsActivity y ChatActivity permanecen compiladas pero **no se habilitan en esta etapa**. No hay lista ni mensajes reales; tampoco otra conversación de demostración. Los controles nativos que requieren pantallas no autorizadas no navegarán a ellas.
- Se descartan intents/deep links y restauración de pantallas vinculadas a cuentas; la recreación empieza en la raíz nativa. El puente Back API33+ despacha `LaunchActivity.onBackPressed()` sin un nuevo motor de animaciones. Las solicitudes de actividades externas desde la Activity se cancelan; esto no se presenta como un cortafuegos universal de Binder.
- Manifiesto propio: launcher único, sin INTERNET, sin importadores, authenticators, sync adapters, servicios, receivers ni inicializadores externos de bibliotecas. Se conserva solo el provider local de jlatexmath, no exportado y con authority del nuevo paquete. La política común de exclusión de backups permanece intacta. **Pendiente verificar el manifiesto fusionado real**, además de las inspecciones del XML fuente realizadas aquí.
- JNI utiliza un scope SHA-256 separado `:realAlpha`, conserva `FLEXYGRAM_BUILD_DIAGNOSTIC=1` y las seis constantes nativas falsas. Se reutiliza la fachada de traducción offline; no se habilitan proveedores ni plugins.

Diagnostic, BetaDevelopment, Production, sus manifiestos/políticas y el contrato histórico no se han reemplazado. No se ha accedido ni modificado la segunda APK firmada. No se han cambiado main, develop, PR #23 ni la configuración de Actions.

## Matriz de transporte/autenticación

| Área y referencia de código | Estado actual de realAlpha | Trabajo previo a una habilitación futura |
|---|---|---|
| `UserConfig.loadConfig()`; `RealAlphaBootstrap.ensure()` | Restauración denegada por aislamiento; todos los slots deben estar vacíos | Revisar persistencia, fallo parcial, selección de cuenta y reinicio en el nuevo sandbox. Probar en Android antes de habilitar sesiones |
| `ApplicationLoader.postInitApplication()`; `RealAlphaActivity.ACCOUNTS` | Controladores originales, sin usuario; JNI debe estar cargado | Validar apertura de SQLite, callbacks y ciclo de vida de la lista vacía con Android real. Las pruebas host no ejecutan estos controladores |
| `ConnectionsManager.sendRequest(...)` Java y `init(...)` | Retorno local 403 `DIAGNOSTIC_AUTH_DISABLED`; no se entra en `sendRequestInternal` | Revisar callback, cancelación, error y atestación por variante; no cambiar globalmente `isIsolated()` |
| `tgnet/ConnectionsManager.cpp` sendRequest/init; `ConnectionSocket.cpp` openConnection/openConnectionInternal | Guardas nativas conservadas, sin sockets MTProto | Diseñar una autorización Java/JNI coherente y exclusiva de realAlpha; mantener offline los perfiles existentes. No se ha implementado aún transporte permitido |
| `gradle/telegram-api.gradle`; `TMessagesProj/build.gradle` | Resolver privado por pares existente; esta variante **no lo consume**, ID 0 / hash vacío | Habilitación posterior con credenciales propias verificadas y aprobación; no copiar el ID 6 ni secretos heredados. No hacen falta secretos en esta revisión |
| `LoginActivity` send/resendCode, SafetyNet/Firebase; `AuthTokensHelper` | Login inaccesible por la política de pantallas; RPC y restauración bloqueados | Revisar rutas de códigos, comprobaciones externas y almacenamiento. Firebase no se activa para resolver automáticamente el login |
| `SessionsActivity` resetAuthorizations (líneas 357/397 de la base); `MessagesController.performLogout()` | Pantalla de sesiones no admitida; toda petición externa denegada | Revisar consentimiento y alcance de logout/revocación. Estas operaciones no se ejecutaron en pruebas. No se atribuye ningún incidente previo a estas rutas |
| P0.1 / FileLog / excepciones / `sendRequestInternal` | Trece regresiones de logs aprobadas; errores nuevos sin causa/mensaje privado | Revisión de todos los datos que podrán alcanzar la ruta permitida, incluidos callbacks SDK y logs de transporte. P0.1 no demuestra ausencia universal de datos privados |

**P1/P2 son una integración de código en revisión, no hitos Android certificados.** El arranque/vista real de DialogsActivity y su respuesta a errores 403 no se ejecutaron en Android. P3/P4 siguen cerrados; P5 (chats, lectura/envío) no está habilitado. No se introdujeron dobles de transporte o cuenta en el APK; los dobles están únicamente en pruebas host.

## Resultados finales

Código verificado: `8b3787071f41374ed8b22c3a5d03c2b036ed5646` (13 archivos de código/pruebas, blobs Git remotos comparados byte a byte mediante sus hashes con el checkout probado).

**62 pruebas distintas**, todas aprobadas en Python normal y `-O`: 124 ejecuciones finales, cero fallos y cero omisiones. Son 35 nuevas de realAlpha, 13 de P0.1, 9 de CRASH-001, 3 del perfil Beta y 2 de RPC/JNI. No se suman ejecuciones preliminares repetidas. Inventario de métodos y SHA-256 de los logs en `evidence/test-results.json`. Ninguna es una prueba Android real.

## Validación reproducible

Python 3.11.17, JBR/JDK 21.0.10 b1163.105, Gradle 9.7.1 (Groovy incluido), CMake 3.31.6 y compilador C++ del host. Las distribuciones recuperadas se verificaron con hashes fijados; ver `evidence/environment.json`.

```sh
export JAVA_HOME=/ruta/al/jdk21
export PATH="$JAVA_HOME/bin:/ruta/a/cmake-3.31.6/bin:$PATH"
export FLEXYGRAM_GRADLE_HOME=/ruta/a/gradle-9.7.1
export FLEXYGRAM_CMAKE=/ruta/a/cmake-3.31.6/bin/cmake
python3.11 -m unittest discover -s tests/real_alpha -v
python3.11 -O -m unittest discover -s tests/real_alpha -v
```

Los comandos adicionales y sus salidas están en `evidence/regression-commands.json` y los logs. Los tests Java ejecutan los wrappers nuevos con dobles explícitos de Android/controladores; **no compilan ni renderizan LaunchActivity/DialogsActivity completos**. Los tests de guardas reutilizados ejecutan el método Java y las entradas C++ originales extraídos con colas ficticias. El test CMake nuevo genera el header realAlpha y ejecuta las constantes reales de DiagnosticPolicy.h. El control XML es de fuente, no del APK fusionado. `--release 8` prueba sintaxis/bytecode de estos wrappers, no compatibilidad Android minSdk24.

## Compilación y traspaso a Work 2

Intentos con la tarea real `:TMessagesProj:assembleRealAlphaDebug`, sin SKIP ni firma:

1. Fallo de settings por `TMessagesProj_Modules/media/core_settings.gradle` ausente. Se recuperaron media `c430d207677071b1873f9f18266d55ec45722180` y jlatexmath `f59d6eecfac6fb58d6e3b7d6cff6c8aed9dbd5b4`, sin cambiar gitlinks.
2. Segundo intento: buildSrc compilado; corte del proceso cliente al alcanzar 180 segundos. No es un resultado de Gradle satisfactorio ni un fallo de Java de la aplicación. No se llegó a validar la variante Android.
3. Diagnóstico `--offline`: BUILD FAILED por dependencias de build aún no cacheadas, entre ellas Google Services 4.5.0, Crashlytics 3.0.8 y Chaquopy 17.0.0, con transitivas. No se cambiaron versiones ni TLS.

El intento offline también notificó un workspace inmutable modificado en el cache de transforms de Gradle. No se ignora esa advertencia: se detuvieron los daemons del cache propio de esta misión y se puso ese directorio en cuarentena, sin tocar caches de otros Work ni versiones de dependencias. Ver `cache-quarantine.json`. La regeneración debe comprobarse en la próxima compilación; no se afirma que un build Android posterior haya pasado.

Este entorno no conserva el SDK/NDK ni los caches/insumos privados de la sesión que compiló la segunda APK. No se reconstruyeron ELF/wheels, no se generó APK realAlpha y no hay SHA de APK nuevo. Los mensajes `SKIPPED` de comprobaciones Kotlin y `NO-SOURCE` de buildSrc no son omisiones de nuestras suites unittest; tampoco demuestran JNI/Python completos.

En el entorno Android completo de Work 2, aplicar el commit de código de esta rama sobre la base corregida (no sobreescribir PR #23), restaurar los submódulos fijados y los insumos privados ya verificados, y ejecutar:

```sh
NATIVE_TARGET=arm64-v8a CHAQUOPY_BUILD_PYTHON=/ruta/a/python3.11 \
  ./gradlew --no-daemon --max-workers=2 -PflexygramRealAlpha=true \
  :TMessagesProj:assembleRealAlphaDebug
```

No usar SKIP, firma automática ni `flexygramBetaDevelopment` como sustituto. Antes de aceptar el unsigned: comprobar paquete realAlpha, ID/hash vacíos, capacidades Java/JNI, manifiesto fusionado sin INTERNET/IPC heredado, DEX, JNI/Chaquopy completos, políticas nativas, 16 KB, hash y respaldo privado. Los verificadores atados a identidades Beta/Diagnostic **no deben aceptar automáticamente realAlpha** ni relajarse para que pase: su adaptación explícita es pendiente.

Después: revisión de este PR, compilación completa, autorización específica de firma/instalación para un binario identificado, y prueba del root nativo sin cuenta. Solo tras validar P1/P2 se revisarán la ruta permitida de transporte, credenciales propias y una autorización independiente para usar una cuenta. No se necesitan credenciales personales para continuar la compilación offline.
