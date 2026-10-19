# P0.2 — Identidad y aislamiento diagnóstico

FlexyGram 1.0, responsable @Lukhou23. Se conservan las licencias, copyright y autoría del código original. No se atribuye el incidente anterior a una causa no demostrada.

## Integración P0.1

PR #4 se verificó en `b77938871b9c09f9bc86730471fdcbaffb4a1dbc` y se fusionó exclusivamente a `develop` mediante `889117c376415b1481e6abcd42b170b8c7e68236`. Esta rama nace de esa integración. PR #2 permanece abierto; `main` no se cambia; Actions no se habilita.

Las evidencias históricas verificadas de P0.1 se conservan en `evidence/p01-*`: 13 pruebas con JDK 21/Python 3.11, las siete clases Java compiladas, resultado Gradle ARM64 con salida 0 y auditoría de la APK interna. La APK anterior no se publica. Estos resultados completan las limitaciones de compilación que figuraban en el informe inicial P0.1; no sustituyen pruebas de ejecución Android.

## Diagnóstico únicamente

Identidad fija: **FlexyGram Diagnostic**, `io.github.jose22yt.flexygram.diagnostic`. No se renombra el namespace Java `org.telegram.messenger`. Se rechazan overrides accidentales del application ID. La aplicación no comparte UID ni datos con Telegram/Exteraless; su almacenamiento interno y externo privado dependen de su propio application ID. No se accede a otras apps mediante AccountManager ni se migran sesiones. Los permisos de lectura de almacenamiento compartido/contactos/cuentas se retiran del diagnóstico.

Esta rama es deliberadamente **offline en todos los build types**. No existe un parámetro, preferencia o credencial que pueda habilitarla para uso autenticado. No es un cliente utilizable ni una variante de producción. Cambiar esa política requiere otro cambio de código aprobado y completar las revisiones pendientes.

### Barreras efectivas

- `DiagnosticPolicy.java` deriva del `BuildConfig.ISOLATED_DIAGNOSTIC=true` fijo. `ConnectionsManager` Java no inicializa transporte y rechaza todas las solicitudes antes de serialización, hooks o envío con error local `403 / DIAGNOSTIC_AUTH_DISABLED`.
- `jni/tgnet/DiagnosticPolicy.h` es una política nativa fija. `ConnectionsManager::init` retorna antes de leer configuración de sesiones o crear su hilo; `sendRequest` libera y descarta solicitudes; `ConnectionSocket::openConnection` y `openConnectionInternal` retornan antes de crear/conectar sockets. No se cambia la navegación ni la lógica del transporte original fuera de estas barreras diagnósticas.
- El manifiesto final debe carecer de `android.permission.INTERNET`, incluso tras fusionar manifests de dependencias. Es una barrera Android adicional para Java, JNI, Python y bibliotecas del mismo UID, no solo para botones de login.
- `UserConfig.loadConfig` no restaura usuarios; `AuthTokensHelper` no lee ni guarda tokens en diagnóstico; las preferencias de API personalizadas no pueden reemplazar ID 0/hash vacío en diagnóstico. No se borran datos existentes ni se manipulan sesiones reales.
- Plugins y modo desarrollador no se pueden activar por preferencias o setters; `PythonPluginsEngine.ensureStarted` devuelve fallo sin iniciar intérprete. No se ejecutan plugins ni servidor de desarrollo.
- FCM, UnifiedPush, facturación, comprobaciones de proxy, actualizador y Crashlytics tienen bloqueos de entrada. Se eliminan inicializadores Firebase/ML Kit/AndroidX y entry points de transporte/connector/cast heredados del manifiesto. No se procesa `google-services.json` ni se habilita Crashlytics Gradle.
- Passkeys y los dos accesos Google Sign-In del login tienen guardas antes de contactar con servicios externos. Las guardas de login y del interruptor Crashlytics son cambios de seguridad; no alteran layouts, animaciones o navegación.
- `allowBackup=false`, sin `backupAgent`, `restoreAnyVersion=false`, sin full backup; cloud backup y device transfer excluyen todos los dominios declarados. El helper explícito de respaldo también retorna sin registrar preferencias ni pedir copias.
- AccountManager y sync tienen account type propio, consistente con `BuildConfig.APPLICATION_ID`. Ambos servicios quedan desactivados. `com.android.contacts` permanece como content authority del proveedor del sistema, no como identidad de Exteraless. Los MIME types y enlaces de preferencias/shortcuts usan la identidad nueva; providers propios usan `${applicationId}`.

## Pareja API privada

`gradle/telegram-api.gradle` resuelve una pareja completa sin imprimir valores:

1. `LOCAL_PROPERTIES` (base64) o `local.properties` privado, según la selección original de Gradle. Si el Properties seleccionado contiene cualquiera de las dos claves, ambas deben ser válidas en esa misma fuente.
2. Si no hay ninguna clave API en ese Properties, se acepta la pareja completa del entorno.
3. Ausencia total permite solamente compilar el diagnóstico offline. Configuración parcial, vacía, formato incorrecto, overflow o API ID 6 aborta la configuración con error genérico. Nunca se mezcla una clave local con otra del entorno.

Claves: `TELEGRAM_APP_ID` y `TELEGRAM_APP_HASH`. En esta etapa **no se necesitan ni se solicitan**. Incluso una pareja válida se valida y se descarta para el artefacto diagnóstico: `APP_ID=0`, `APP_HASH=""`. La API personalizada en preferencias también se ignora. El fallback heredado autenticable se eliminó del build.

La propiedad de unas credenciales no puede demostrarse mediante una comprobación de formato. El responsable deberá obtenerlas posteriormente desde my.telegram.org, mantenerlas fuera de Git y completar su aprobación antes de habilitar cualquier uso autenticado. No configurar credenciales ajenas. No habilitar autenticación en esta rama.

## Firma diagnóstica propia

Todos los build types de esta rama usan exclusivamente `signingConfigs.debug`, nunca el keystore release heredado. Se utiliza un keystore diagnóstico separado de la firma Debug genérica del host. No se incluye ninguna clave privada ni contraseña en Git o logs.

Preparación local: crear fuera del repositorio un keystore JKS con alias `flexygram-diagnostic`, certificado `CN=FlexyGram Diagnostic`, claves RSA 2048 y contraseñas aleatorias guardadas con permisos 0600. `keytool -genkeypair` admite `-storepass:env` y `-keypass:env`, evitando contraseñas en argumentos. Exportar únicamente en el proceso de compilación:

- `FLEXYGRAM_DIAGNOSTIC_KEYSTORE`: ruta privada del keystore.
- `FLEXYGRAM_DIAGNOSTIC_STORE_PASSWORD`: contraseña local generada.
- `FLEXYGRAM_DIAGNOSTIC_KEY_PASSWORD`: contraseña local generada.

La ruta predeterminada es `GRADLE_USER_HOME/flexygram-diagnostic/debug.keystore`, pero las contraseñas no tienen fallback. Una máquina nueva debe generar su propia clave o recuperar la clave diagnóstica por un canal privado autorizado. Perderla impide actualizar una instalación diagnóstica existente; nunca desinstalar una app personal para forzar una actualización. La identidad y la firma son diferentes de Exteraless/Telegram.

## Pruebas y compilación

```sh
python -m unittest discover -s tests/security -v
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleDebug --no-daemon --console=plain --max-workers=2
```

Usar el toolchain original: JDK 21, Wrapper 9.7.1, AGP 9.3.1, SDK 37 r2 (paquete `android-37.0`), SDK 35 para Media, Build Tools 36.0.0, NDK 27.2.12479018, CMake 3.31.6, Python host 3.11 y Chaquopy 17.0.0. Configurar las rutas SDK/Python y la firma solo localmente. No usar `NATIVE_TARGET=SKIP`.

La batería incluye P0.1 y P0.2: resolvedor Groovy real con parejas sintéticas; manifiesto/account types/backup; método Java real de dispatch con transporte falso; callbacks FCM reales con dobles; guardas nativas extraídas literalmente ejecutadas con transporte/configuración falsos y destructor comprobado; contratos estáticos de puntos de entrada. No abre sockets ni usa Telegram, Firebase, cuentas, sesiones, revocación o plugins reales. Los tests P0.1 mantienen sus dobles con aislamiento falso para seguir comprobando los caminos originales de logs; P0.2 utiliza la política Java de producción con BuildConfig diagnóstico verdadero.

Los resultados finales y los controles sobre el artefacto se registran en `evidence/`. No confundir los tests con pruebas de instalación o captura de tráfico en Android.

## Reservado para P0.3 (no implementado aquí)

Auditar y decidir política definitiva de backup/transferencia de sesiones, migración y borrado; titularidad y restricciones de Firebase/push/Maps/OAuth/billing; destinos y firma del actualizador; servicios de terceros y telemetría; requisitos legales/API pendientes. Los bloqueos actuales no configuran servicios propios ni completan esa revisión. El archivo Firebase heredado permanece como material original inactivo, sin aplicarse al diagnóstico.

Se necesitan después pruebas Android offline autorizadas de arranque, permisos reales, providers, AccountManager y ausencia de tráfico. No se ha instalado esta APK, no se ha iniciado sesión y no se han hecho solicitudes Telegram. Una compilación exitosa no demuestra comportamiento completo en el Poco X8 Pro. No distribuir la APK ni aprobar nuevas pruebas autenticadas por haber terminado P0.2.

## Resultado verificado de esta revisión

- **18 pruebas aprobadas, 0 fallidas y 0 omitidas**, ejecutadas con JDK 21 y Python 3.11; se conservan también las 13 pruebas históricas P0.1.
- Primera compilación de integración: `BUILD SUCCESSFUL`, salida 0, 7 min 55 s. Pasada final con todas las guardas: `BUILD SUCCESSFUL`, salida 0, 5 min 3 s; 244 tareas (12 ejecutadas y 232 al día). No se omitieron componentes nativos con SKIP. Compila Java/Kotlin, C++ ARM64 y runtime Chaquopy.
- APK interna: identidad y nombre propios, Debug, firma válida y distinta de P0.1, solo ARM64 (18 bibliotecas ELF), ZIP íntegro. El manifiesto binario no contiene INTERNET ni los inicializadores Firebase/ML Kit/AndroidX retirados. Account types/MIME/shortcuts/auth-menu compilados con identidad propia; providers de la app usan authorities propias.
- BuildConfig generado: API ID 0/hash vacío/política aislada verdadera. Las cinco guardas de AuthTokensHelper aparecen en su clase compilada. No se instala, ejecuta ni publica el binario.
- Se mantienen advertencias heredadas de Gradle, CMake, recursos y APIs obsoletas; no se corrigen funciones ajenas a P0.2. El doble de pruebas P0.1 se adapta para proporcionar la nueva clase de política; su lógica y las comprobaciones de secretos siguen ejecutándose.
- No se ha usado un dispositivo/emulador ni capturado tráfico Android. La coexistencia se verifica por identificadores/firma/manifiesto; la instalación y el arranque offline quedan pendientes. No se afirma haber probado notificaciones, autenticación, sesiones, backups o plugins reales.

Firma pública de la compilación interna: SHA-256 `7184de239dc697f4957e8074300a9e440e3154cad5aac3f2f04a490fc90e78a5`.
APK interna SHA-256: `ed7a6c4ded34fb992dae7e90f07eed0988bd109fa911bc4d006eea8586c34c2a`. Solo se conserva evidencia; no se distribuye la APK.

Recomendación: revisión del PR P0.2 para aceptar **exclusivamente diagnóstico aislado**, sin habilitar cuentas ni servicios de producción. P0.3 y P0.4 no se implementan ni quedan aprobados por este resultado.
