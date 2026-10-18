# Construcción, dependencias y compatibilidad

[Índice](README.md). **Configuración declarada, no construcción validada.** No se ejecutó Gradle, ni siquiera para listar tareas: su configuración puede iniciar procesos externos de Chaquopy y resolver artefactos.

## Toolchain declarado

| Componente | Valor en el código | Evidencia y límite |
| --- | --- | --- |
| Java/JDK | 21 para source/target y Kotlin JVM; CI Temurin 21; daemon configurado JetBrains 21 | [build.gradle:L33](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L33), [gradle/gradle-daemon-jvm.properties:L12](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/gradle/gradle-daemon-jvm.properties#L12), [.github/workflows/release.yml:L44](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L44). No se validó disponibilidad del proveedor ni la matriz AGP/Gradle/JDK |
| Gradle Wrapper | 9.7.1, bin distribution | [gradle/wrapper/gradle-wrapper.properties:L3](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/gradle/wrapper/gradle-wrapper.properties#L3). Se declara URL, no se descargó ni verificó su resolución |
| AGP | 9.3.1 en raíz y buildSrc | [build.gradle:L9](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L9), [buildSrc/build.gradle.kts:L21](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L21). No se afirma que esa combinación compile |
| Kotlin | AGP integrado en app; buildSrc usa kotlin-dsl y app configura JVM 21 | [build.gradle:L38](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L38), [buildSrc/build.gradle.kts:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/buildSrc/build.gradle.kts#L1). No aparece un plugin Kotlin Android con versión independiente en los cuatro scripts versionados; no inventar una versión de compilador |
| compileSdk | 37 | [build.gradle:L24](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L24) |
| targetSdk | 36 | [build.gradle:L48](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L48). No equivale a target 37 |
| minSdk | 24 | [build.gradle:L47](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L47). La compatibilidad efectiva también depende de nativos y librerías |
| Build Tools | 36.0.0 | [build.gradle:L25](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L25) |
| NDK | 27.2.12479018 | [build.gradle:L26](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L26) |
| Plataforma nativa | `-DANDROID_PLATFORM=android-27` | [TMessagesProj/build.gradle:L191](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L191). Revisar diferencia con minSdk 24 para API 24–26; sin fallo demostrado |
| CMake | selector `3.31.6+`; CMakeLists mínimo 3.16 | [TMessagesProj/build.gradle:L217](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L217), [TMessagesProj/jni/CMakeLists.txt:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L1). Un selector abierto no fija exactamente una instalación |
| C/C++ | C11 y C++17, con targets wallet en C++20 | [TMessagesProj/jni/CMakeLists.txt:L3](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L3), [TMessagesProj/jni/CMakeLists.txt:L138](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L138) |
| Python/Chaquopy | Python 3.11; plugin Chaquopy 17.0.0; runtime nativo personalizado | [build.gradle:L17](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/build.gradle#L17), [TMessagesProj/build.gradle:L136](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L136), [TMessagesProj/build.gradle:L299](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L299) |
| ABI | arm64-v8a y x86_64 en selección normal; `NATIVE_TARGET=arm64-v8a` para objetivo principal | [TMessagesProj/build.gradle:L99](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L99). El env admite otras cadenas; no significa que esas ABI estén soportadas |
| Splits | Desactivados; filtro ABI en defaultConfig | [TMessagesProj/build.gradle:L121](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L121) |
| Nombre/versión heredados | `APP_PACKAGE=com.exteraless.app`, `APP_VERSION_NAME=13.0.2`, APP_VERSION_CODE 7175; versión efectiva del módulo con `verCode=1261` | [gradle.properties:L18](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/gradle.properties#L18), [TMessagesProj/build.gradle:L26](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L26). Son valores de la base, no una APK FlexyGram 1.0 |
| R8 | Staging/release minificados y con shrinkResources; reglas amplias para reflexión/JNI | [TMessagesProj/build.gradle:L252](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L252), [TMessagesProj/proguard-rules.pro:L9](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/proguard-rules.pro#L9) |

Las versiones de artefactos, herramientas y SDK se registran como hechos del repositorio. Verificar disponibilidad y compatibilidad oficial exacta antes de autorizar la instalación del entorno; no sustituir silenciosamente versiones por otras.

## Módulos y dependencias

`settings.gradle` incluye `:TMessagesProj`, aplica `TMessagesProj_Modules/media/core_settings.gradle` y redirige common-ktx a una ruta local. El árbol del superproyecto solo contiene `.gitkeep` en common-ktx; la inclusión real y resolución de módulos debe revisarse en el submódulo media fijado, no deducirse de un placeholder. [settings.gradle:L29](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/settings.gradle#L29).

La aplicación declara media-lib-exoplayer, dash, hls, decoder-ffmpeg y session. Usa dependencias AndroidX/Material, CameraX, Google/Firebase, red, traducción/IA, Room, mapas, pagos, renderizado y plugins. El [inventario](inventory.md) transcribe las coordenadas de los scripts sin resolver transitivas. **No constituye SBOM final**: faltan grafo resuelto, hashes y licencias transitivas.

Repositorios de resolución: Google, Maven Central y Maven de Aliucord; portal de plugins en pluginManagement. Se prohíben repositorios por proyecto mediante FAIL_ON_PROJECT_REPOS. [settings.gradle:L1](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/settings.gradle#L1), [settings.gradle:L18](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/settings.gradle#L18).

No se encontraron `gradle.lockfile` ni `verification-metadata.xml` en el árbol inspeccionado. Los paquetes pip en build.gradle se piden sin versión. Los workflows usan actions con tags, no SHA completo. Son riesgos de reproducibilidad y cadena de suministro, no evidencia de compromiso. Antes de cambios, diseñar un procedimiento de verificación/lock específico y auditar compatibilidad.

## Nativos y submódulos

Hay 16 gitlinks registrados con SHA completo; véase inventario. La presencia de un gitlink no demuestra por sí sola que participe en todas las variantes: por ejemplo jlatexmath está registrado, pero no hay un include Gradle explícito para ese submódulo en los scripts del superproyecto; confirmar su uso efectivo al inspeccionar media y el grafo resuelto. `media` y Chaquopy son necesarios desde la propia configuración: sus fuentes ausentes afectan incluso antes de obtener una APK. El build de runtime Chaquopy invoca `bash` sobre el script del submódulo, resuelve target ZIP y copia `chaquopy.so`/`libchaquopy_java.so` generados a salidas de tareas internas. La dependencia con nombres internos de tareas es un riesgo de integración al actualizar AGP/Chaquopy. [TMessagesProj/build.gradle:L299](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L299).

CMake importa `.a` por ABI desde ffmpeg, boringssl/lib, tde2e, tlottie_lib y prebuild/lib. Esos binarios incluidos en el árbol no se regeneran necesariamente con cambiar el NDK. Hay 68 archivos `.a` y un `.aar` versionados; no se auditaron sus símbolos, procedencia reproducible, alineación ni licencias internas. CMake compila los puentes y otros componentes del superproyecto. [TMessagesProj/jni/CMakeLists.txt:L54](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L54), [TMessagesProj/jni/CMakeLists.txt:L125](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L125).

Scripts presentes para ffmpeg/libvpx/dav1d, opus, tlottie, Prisma, wallet, WAMR y tde2e muestran que regenerar nativos es una actividad independiente. No se ejecutaron. Rust/Cargo u otras herramientas pueden ser necesarios para regenerarlos; no son una exigencia verificada para toda construcción que consuma prebuilts. Para x86_64 CMake habilita ASM_NASM; la CI de release instala nasm. [TMessagesProj/jni/CMakeLists.txt:L15](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L15), [.github/workflows/release.yml:L66](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/.github/workflows/release.yml#L66).

`NATIVE_TARGET=SKIP` deshabilita tareas cuyos nombres contienen cmake/jni/test. **No sirve como validación de una APK funcional ARM64** ni de la integración nativa; podría omitir precisamente verificaciones necesarias. [TMessagesProj/build.gradle:L66](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L66).

## Credenciales y firma

| Requisito | Mecanismo heredado | Acción posterior antes de distribución |
| --- | --- | --- |
| Telegram APP_ID/APP_HASH | local.properties o LOCAL_PROPERTIES base64; fallbacks codificados. El else sin properties solo aplica env para maps/glyph, no appId/appHash | Obtener valores propios y comprobar resolución efectiva; no depender de fallbacks |
| Firma | `TMessagesProj/release.keystore`, KEYSTORE_PASS/ALIAS_NAME/ALIAS_PASS por properties/env | Custodia y backup de clave propia; verificar certificado y continuidad de actualizaciones |
| Sin firma propia | debug, staging y release pueden usar signingConfigs.debug si hasReleaseKeystore es falso | No confundir `release` con firma de producción |
| Firebase | google-services.json presente y plugin Google Services/Crashlytics aplicado | Revisar proyecto y coincidencia con package/firma; no asumir que es configuración propia |
| Maps/Glyph | placeholders y valores de reserva | Revisar restricciones y valores propios cuando correspondan |
| CI de distribución | LOCAL_PROPERTIES, RELEASE_KEYSTORE y variables TG_* | No solicitar ni cargar secretos de publicación en esta etapa |

Evidencia: [TMessagesProj/build.gradle:L40](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L40), [TMessagesProj/build.gradle:L151](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L151), [TMessagesProj/build.gradle:L223](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L223), [TMessagesProj/build.gradle:L245](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/build.gradle#L245), [TMessagesProj/src/main/AndroidManifest.xml:L109](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/src/main/AndroidManifest.xml#L109). Se evita reproducir los valores de credenciales que están en el código; su presencia no demuestra validez, privilegios ni explotación. No se inspeccionaron valores de secretos privados en GitHub.

Antes de una distribución FlexyGram se deberá decidir applicationId, configuración de servicios, certificado y canal de actualización propios. **No cambiarlos ahora**, porque el objetivo inmediato es conservar la base para una comparación válida. El actualizador heredado apunta a releases de Exteraless. [TMessagesProj/src/main/java/app/exteraless/updater/GitHubUpdater.java:L47](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/src/main/java/app/exteraless/updater/GitHubUpdater.java#L47).

## Compatibilidad con el dispositivo indicado

El usuario declara Poco X8 Pro, MediaTek 8500 Ultra, ARM64, Android 17/API 37, HyperOS 4 y pantalla de alta frecuencia. No se consultó ni conectó el hardware; esos datos no fueron verificados físicamente.

Hechos compatibles con el objetivo: el filtro incluye ARM64, compileSdk es 37, se declara aceleración HW y back moderno; existe un flag de flexible page sizes y el target tmessages recibe opciones de enlace max/common-page-size=16384. Evidencia adicional: [TMessagesProj/jni/CMakeLists.txt:L308](https://github.com/Jose22Yt/FlexyGram/blob/db1bea24b7b705de33f8ff8c8e174011c153cac7/TMessagesProj/jni/CMakeLists.txt#L308). **No prueban** instalación, arranque, estabilidad, page size, soporte de cada SDK ni tasa de refresco sostenida. targetSdk continúa en 36.

Pruebas futuras necesarias: carga de todas las `.so` transitivas (incluidas AAR y Python), requisitos ELF/page size, arranque frío, JNI/reflexión/hidden API hooks, multimedia/cámara, permisos y back predictivo. minSdk frente a ANDROID_PLATFORM debe analizarse aparte para dispositivos antiguos; el Poco no constituye cobertura API 24–26.

La [documentación oficial de Android sobre páginas de 16 KB](https://developer.android.com/guide/practices/page-sizes), consultada el 18-10-2026, exige revisar binarios nativos y probar en ese entorno: un flag de construcción no certifica todas las librerías. El tamaño real de página del Poco queda pendiente.

## Pendientes para un entorno reproducible

1. Verificar matriz oficial y disponibilidad de Gradle/AGP/JDK/SDK/CMake declarados.
2. Obtener submódulos exactamente en los SHA fijados; revisar también recursivos y sus instrucciones antes de ejecutarlas.
3. Examinar `media/core_settings.gradle`, common-ktx y runtime Chaquopy fijados.
4. Inventariar/checksum de prebuilts y su procedencia; no regenerarlos todos sin necesidad.
5. Definir configuración de prueba y firma identificable, sin introducir claves en Git.
6. Solo tras autorización del Paso 3: preparar entorno y decidir qué comprobaciones/compilación mínima se permiten. No se ha construido ni ejecutado nada en este paso.
