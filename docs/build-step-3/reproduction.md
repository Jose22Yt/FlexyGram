# Procedimiento de construcción de referencia

Este procedimiento describe la preparación realizada y los pasos necesarios para reintentar el build; su presencia no acredita una compilación exitosa. Consultar el resultado real en [README](README.md).

## Fuente y herramientas

Partir del merge documental `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2` en una rama independiente. El código funcional proviene de `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`.

```sh
git clone --filter=blob:none https://github.com/Jose22Yt/FlexyGram.git
cd FlexyGram
git switch --detach 082aff3d0fc57ce90b0154fe76d9d7c796ed45a2
git switch -c build/paso-3-clean-debug-local
git submodule update --init --depth 1 --filter=blob:none --jobs 4
git submodule status --recursive
```

Comprobar cada SHA con [submodules.json](evidence/submodules.json). No actualizar a HEAD remoto. Revisar cualquier `.gitmodules` anidado y gitlink antes de inicializar dependencias adicionales. En el checkout preparado se encontraron 16 submódulos activos y no se detectaron gitlinks anidados adicionales.

Instalar JDK 21 de JetBrains para satisfacer `gradle/gradle-daemon-jvm.properties`; fijar su ruta en `org.gradle.java.installations.paths` de un GRADLE_USER_HOME privado y desactivar descarga automática si ya está instalado. El wrapper se verificó contra el SHA-256 oficial antes de ejecutar Gradle 9.7.1. SDK 37 r2 y SDK 35 r2, Build Tools 36.0.0, NDK 27.2.12479018 y CMake 3.31.6. SDK 35 lo declara `TMessagesProj_Modules/media/constants.gradle`. El host requiere Python 3.11; no usar por accidente el 3.12 preinstalado.

En esta máquina se usó SDK Manager Java de command-line tools 19.0 porque el launcher de la versión más reciente intentaba descargar otra herramienta y no establecía conexión. Es una elección del instalador del entorno, sin sustitución del SDK/NDK/AGP de la aplicación. Una plataforma SDK instalada con estructura anidada se volvió a extraer de su ZIP oficial verificado para disponer de `platforms/android-37.0/android.jar` en la ruta correcta. No se corrigió código del proyecto para resolver esas incidencias del host.

## Configuración privada

`local.properties` está ignorado por Git. Definir `sdk.dir` y `CHAQUOPY_BUILD_PYTHON` con rutas absolutas locales. Antes de distribuir una APK, proporcionar `TELEGRAM_APP_ID` y `TELEGRAM_APP_HASH` propios mediante ese archivo privado; no enviarlos por chat, PR, logs o commits. Obtenerlos en el portal oficial de Telegram (`my.telegram.org`, API development tools), conforme a las instrucciones enlazadas por el código. No se necesitan contraseñas de cuenta Telegram, códigos de acceso, tokens de bot ni claves de producción para un debug local.

Usar permisos restrictivos del archivo (`chmod 600 local.properties`) y verificar que `git check-ignore local.properties` lo reconoce. No imprimir su contenido. No crear `TMessagesProj/release.keystore` ni proporcionar contraseñas de firma release: el build original selecciona `signingConfigs.debug` cuando ese archivo no existe. Verificar después el certificado real con apksigner; la inspección del ternario no sustituye la comprobación de la APK.

Si hace falta proxy, usar exclusivamente la configuración de red autorizada del host en el GRADLE_USER_HOME local. En este entorno sus puertos cambian entre comandos; se deben obtener del entorno vigente en cada ejecución. Mantener validación TLS y almacén de certificados confiable. No incluir endpoints internos ni credenciales en documentación pública.

## Comando previsto

Con JAVA_HOME, ANDROID_HOME/ANDROID_SDK_ROOT, GRADLE_USER_HOME y rutas ajustadas al host:

```sh
export NATIVE_TARGET=arm64-v8a
export CHAQUOPY_BUILD_PYTHON=/ruta/python3.11
export CMAKE=/ruta/android-sdk/cmake/3.31.6/bin/cmake
export PATH="$JAVA_HOME/bin:/ruta/android-sdk/cmake/3.31.6/bin:$PATH"
./gradlew :TMessagesProj:assembleDebug --no-daemon --console=plain --stacktrace --max-workers=2
```

El checkout nuevo no tiene salidas previas de compilación; no reutiliza APK, parches ni cachés de versiones antiguas de FlexyGram. La caché de dependencias de este paso es nueva. No usar `NATIVE_TARGET=SKIP`: omite tareas nativas y no acredita una base ARM64.

El script inspeccionado `TMessagesProj/chaquopy/exteraless/build.sh` compila el runtime Python personalizado con NDK/CMake, Cython 3.0.11 y el target ZIP resuelto por Chaquopy. No ejecutarlo sobre otra versión de Python ni regenerar todos los prebuilts sin necesidad. Los scripts de publicación o envío de Telegram no forman parte de esta construcción.

## Verificación obligatoria tras obtener APK

1. Registrar exit code real y logs de Gradle, componentes nativos y runtime Chaquopy; resolver errores y advertencias relevantes.
2. Enumerar APK generadas y analizar manifest con aapt/apkanalyzer: package, versionCode/versionName, min/target SDK y debuggable.
3. Inspeccionar ZIP: `lib/arm64-v8a`, binarios ELF AArch64, runtime Python y bibliotecas transitivas. Revisar alineación y soporte de páginas de 16 KB de cada `.so`; no basta con un flag de CMake.
4. Ejecutar `apksigner verify --verbose --print-certs`, registrar huella del certificado Debug y `sha256sum` de la APK. No publicar la clave privada.
5. Conectar dispositivo autorizado; comprobar API, ABI y página, instalar y arrancar, conservar logcat depurado. Si no hay dispositivo, marcar explícitamente instalación/arranque pendientes.
6. No cambiar el applicationId para evitar un conflicto silenciosamente. La base usa `com.exteraless.app`; una instalación existente podría tener firma incompatible y datos importantes. No desinstalarla para forzar la prueba. Una variante aislada exige revisión posterior de package, Firebase/Maps y diferencias de configuración antes de construirla.
