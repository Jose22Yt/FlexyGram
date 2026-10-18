# FlexyGram 1.0 — Paso 3: preparación y primera construcción de referencia

> **Continuación y nueva entrega:** la APK original de este registro no se recuperó. Se reconstruyó desde el mismo commit de fuente. Consultar [la verificación actual y el nuevo SHA-256](continuation/README.md), los límites de 16 KB y las pruebas Android pendientes. Los hashes históricos siguientes no identifican la APK nueva.


Responsable y creador de FlexyGram: **@Lukhou23**. Cuenta propietaria: **Jose22Yt**. Base funcional y autoría original: **Exteraless y sus contribuyentes**, sin atribuir su código a FlexyGram. Se conserva GPL-3.0 y los avisos originales.

Fecha de la sesión: 18 de octubre de 2026. Alcance exclusivo: integrar documentación aprobada, preparar entorno y comprobar una construcción ARM64 Debug. No se autoriza avanzar al Paso 4 desde este informe.

## Fuente y control Git

Se comprobó que el PR #1 tenía exactamente seis Markdown bajo `docs/audit-step-2/`, con head `7b6200b508b6b5aa710ff6eeaac6b67836449040`, sin cambios nuevos inesperados. Se fusionó a **develop** usando merge commit:

`082aff3d0fc57ce90b0154fe76d9d7c796ed45a2`

La [verificación de fuente](evidence/source-verification.json) registra el estado local y el diff. El diff desde `db1bea24b7b705de33f8ff8c8e174011c153cac7` contiene únicamente esos documentos. El merge conserva el código de origen `1ad6a60a6834ffca722b1a22f4fba27ecb29a061` sin cambios funcionales.

Se creó **build/paso-3-clean-debug** desde ese merge y un worktree limpio separado. No se reutilizaron parches ni salidas de versiones antiguas. `main` permanece en `db1bea24b7b705de33f8ff8c8e174011c153cac7`, con `protected=true`; develop está sin protección y no recibió cambios funcionales. La documentación de este paso se propone por PR a develop.

Se verificó directamente Settings → Actions → General: **Disable actions seleccionado**. La API seguía mostrando **cero ejecuciones**. No se habilitaron workflows, no se publicó Release y no se enviaron APK a Telegram.

## Entorno realmente preparado

| Componente | Versión y comprobación | Límite |
| --- | --- | --- |
| JDK usado por daemon | JetBrains Runtime SDK 21.0.11+10-b1163.116, `java -version` exit 0 | Satisface vendor JETBRAINS del archivo de criterios; Temurin 21.0.12.1+1 también se descargó y verificó, pero no sustituye ese criterio |
| Gradle Wrapper | 9.7.1, `--version` exitoso; ZIP contrastado con SHA-256 oficial | La ejecución de versión no certifica el build completo |
| Android Gradle Plugin | 9.3.1 declarado en raíz/buildSrc; artefactos descargados por Gradle | Configuración y construcción Debug completadas; no implica compatibilidad de ejecución de todos los servicios |
| SDK aplicación | Android 37.0 r2, extensión 22; android.jar presente | compileSdk 37 no equivale a targetSdk 37: el target del proyecto sigue siendo 36 |
| SDK Media3 | Android 35 r2, extensión 13 | Requisito adicional observado en el submódulo fijado |
| Build Tools | 36.0.0, source.properties | Firma/empaquetado solo se acreditan examinando una APK |
| Android NDK | 27.2.12479018, clang 18.0.3 ejecutable | La versión del compilador no certifica todos los prebuilts |
| CMake | 3.31.6 ejecutable | Dentro del selector original `3.31.6+`; no se cambió el selector |
| Python host | CPython 3.11.17 instalado mediante uv; ejecutable verificado | Difiere del patch del runtime Android, que lo resuelve Chaquopy; misma versión menor 3.11 requerida |
| Chaquopy | 17.0.0 resuelto; target Android Python 3.11.14-0 y fuentes personalizadas en SHA fijado | Runtime personalizado compilado; no sustituir por uno stock |
| Platform Tools | 37.0.1; ADB operativo | Sin dispositivos conectados |

El JAR del Wrapper también coincide con el SHA-256 oficial: [wrapper-verification.json](evidence/wrapper-verification.json). `aapt`, `aapt2` y `apksigner` se ejecutan con exit 0: [build-tools-check.json](evidence/build-tools-check.json).

Evidencia: [environment.json](evidence/environment.json), [tool-downloads.json](evidence/tool-downloads.json), [jbr-install.json](evidence/jbr-install.json).

Disponibilidad y compatibilidad se contrastaron con las notas oficiales de [Gradle 9.7.1](https://docs.gradle.org/9.7.1/release-notes.html), [AGP 9.3](https://developer.android.com/build/releases/agp-9-3-0-release-notes) y la [matriz Chaquopy](https://chaquo.com/chaquopy/doc/current/versions.html). AGP 9.3 documenta API máxima 37, Gradle mínimo 9.5.0, Build Tools 36.0.0 y JDK mínimo 17. Chaquopy 17 contempla Python 3.11 y AGP 9.3. Estas matrices no prueban que todos los scripts antiguos del proyecto sean compatibles con esas herramientas: esa conclusión depende del build real.

## Inventario y procedencia

- **Disponibles previamente en el host:** runtime Java 17 y Python 3.12, que no se utilizaron como sustitutos de los requisitos declarados. No había SDK/NDK/CMake Android ni JDK 21 preparados para esta referencia.
- **Descargados en este paso:** herramientas de la tabla, distribuciones verificadas y dependencias que Gradle fue resolviendo en una caché nueva. Las versiones de la aplicación no se actualizaron arbitrariamente.
- **16 submódulos:** todos los HEAD coinciden exactamente con los gitlinks fijados; [inventario completo](evidence/submodules.json). Incluye media, jlatexmath, Chaquopy y componentes nativos. No se detectaron gitlinks anidados activos adicionales.
- **68 `.a` y un `.aar` del checkout:** [rutas, tamaños y SHA-256](evidence/prebuilts-sha256.json). Los 68 `.a` tienen cabecera de archivo ar, no son punteros LFS pendientes. La coincidencia con Git y el hash identifican entradas; no son una certificación de procedencia reproducible ni de todas sus licencias internas.
- **Python Android y paquetes pip:** se preservan las declaraciones originales, varias sin versión fija. Se instalaron 18 paquetes observados en [python-packages-observed.json](evidence/python-packages-observed.json). No se afirma una SBOM transitiva completa ni reproducibilidad bit a bit mientras no se obtenga y registre el grafo realmente resuelto.

El [inventario de entradas Maven descargadas](evidence/maven-cache-observed.json) incluye artefactos y metadatos observados, con SHA-256; no representa por sí solo el grafo seleccionado ni una SBOM.

El script de Chaquopy y los scripts de configuración Media3 se leyeron antes de permitir su participación en el build. No se ejecutaron scripts de publicación/Telegram ni regeneraciones masivas de bibliotecas nativas.

## Incidencias del entorno resueltas

1. El launcher más reciente de command-line tools intentaba descargar otra CLI y falló la conexión. Se utilizó SDK Manager Java oficial 19.0 para instalar los paquetes declarados, sin cambiar versiones de la app.
2. La descarga automática de JDK mediante el endpoint Foojay falló; se obtuvo JBR 21 desde el proveedor oficial y se verificó su SHA-512, manteniendo el vendor original del daemon.
3. El ZIP oficial de Gradle se descargó y contrastó con el SHA-256 oficial; se sembró en la caché del Wrapper porque su primera descarga directa no conectaba.
4. El SDK 37 quedó inicialmente anidado en el directorio instalado. Se volvió a extraer del ZIP oficial con SHA-1 contrastado con el manifiesto Google, corrigiendo exclusivamente la estructura del SDK local.
5. Las primeras comprobaciones `gradlew help` fallaron antes de resolver Foojay porque el proxy guardado apuntaba a un puerto temporal ya cerrado. El log de diagnóstico confirmó `Connection refused`. Leer el proxy vigente en cada ejecución permitió resolver Foojay y compilar buildSrc. No se desactivó TLS ni se parcheó el plugin.

Estos errores del host no demuestran un defecto del código Android ni una regresión de rendimiento.

## Resultado de Gradle y de la APK

**Construcción exitosa**, no validación de funcionamiento en dispositivo. `:TMessagesProj:assembleDebug` terminó con exit code **0**, `BUILD SUCCESSFUL in 12m 44s`; 247 tareas accionables: 191 ejecutadas, 52 desde caché y 4 up-to-date. La caché y las salidas se crearon en este paso; no provienen de versiones antiguas de FlexyGram.

| Dato examinado en el artefacto | Resultado |
| --- | --- |
| Archivo entregado | `FlexyGram-1.0-Clean-Baseline-arm64-debug.apk` |
| Tamaño | 111995915 bytes |
| SHA-256 | `bd18650181e4201813900c98aff0d1c7f5d19cfe6e1fa659fb131e592dcf15f0` |
| Package / label | `com.exteraless.app` / `exteraless`, identidad interna original conservada |
| versionName / versionCode | `13.0.2` / `1261` |
| SDK | min 24, target 36, compile 37 |
| Variante | application-debuggable; Debug con JNI original |
| ABI instalable | Solo `arm64-v8a`; 18 ELF bajo `lib/arm64-v8a`, todos ELF64 AArch64 |
| Firma | apksigner exit 0, un firmante Android Debug; esquema v2 verificado |
| Certificado Debug SHA-256 | `7bf6a9b5c4a701d3cb018d875f70bfed9ba0d3498b9ad58c85f73ca36977906b` |
| Integridad ZIP | Sin errores CRC en APK y seis archivos IMY anidados inspeccionados |
| zipalign | `-c -P 16 -v 4`, exit 0 |
| Nativos | CMake Debug ARM64 completado, `libtmessages.49.so` generado y empaquetado; runtime Chaquopy personalizado compilado |
| Dispositivo/emulador | Ninguno conectado/disponible para ensayo; instalación y arranque pendientes |

Evidencias: [resultado Gradle](evidence/assemble-arm64-original-result.json), [log Gradle depurado](evidence/assemble-arm64-original.log), [verificación de APK y ELF](evidence/apk-verification.json), [manifest/badging](evidence/apk-badging.txt), [firma](evidence/apk-signature.txt), [zipalign](evidence/apk-zipalign.txt), [comprobaciones llvm-readelf](evidence/elf-readelf-checks.txt) y [runtime Chaquopy](evidence/chaquopy-runtime.json). La APK se entrega como archivo de diagnóstico, sin Release GitHub ni envío Telegram. El nombre del archivo FlexyGram no implica renombrar la aplicación ni modificar su interfaz.

### Alertas verificadas del artefacto

| Prioridad | Hecho observado | Riesgo o comprobación pendiente |
| --- | --- | --- |
| Alta | En `assets/chaquopy/requirements-common.imy`, `chaquopy/lib/libexslt.so`, `libfreetype.so`, `libxml2.so` y `libxslt.so` son ARM64 con segmentos PT_LOAD alineados a 4096 bytes | No cumplen el criterio estructural de carga ELF de 16 KB. Validar carga y procedencia de los wheels; no se ha demostrado un crash real ni se han actualizado paquetes para ocultar el hallazgo |
| Alta | 73 de los 96 ELF ARM64 inspeccionados tienen algún segmento GNU_RELRO cuyo final `(VirtAddr + MemSiz)` no es múltiplo de 16384; lista individual en JSON | Es un resultado de comprobación estática según la guía Android consultada, que exige revisión antes de certificar soporte de 16 KB. No es una prueba de que esos 73 archivos fallen al ejecutarse en el Poco |
| Media | `debugpy/_vendored/pydevd/pydevd_attach_to_process/attach_linux_amd64.so` dentro de requirements-common.imy es ELF64 x86-64 | Auxiliar vendorizado de attach a procesos, fuera de `lib/arm64-v8a`; no añade una ABI instalable x86-64 al manifest. Revisar `get_target_filename()` en `add_code_to_python_process.py` antes de usar attach en Android. No se probó esa función ni se eliminó el archivo |
| Baja | Gradle no pudo retirar símbolos de `libjnidispatch.so` y lo empaquetó tal cual | llvm-readelf confirma ELF64 AArch64 y PT_LOAD de 16 KB. No se ha identificado la causa exacta del aviso de strip; no bloqueó build ni firma |

La [guía oficial Android de páginas de 16 KB](https://developer.android.com/guide/practices/page-sizes), consultada el 18-10-2026, trata por separado alineación ELF, ZIP, RELRO y pruebas de ejecución. **Que zipalign pase no valida las bibliotecas extraídas desde los assets Python.** Todos los ELF de `lib/arm64-v8a` superan el chequeo PT_LOAD de 16 KB; esto no elimina las alertas de RELRO y de los assets. Los campos globales `all_elf_aarch64=false` y `elf_load_alignment_at_least_16k=false` del JSON incluyen todo lo inspeccionado en assets y archivos anidados, no solo las bibliotecas que instala Android.

**No se certifica compatibilidad completa con Android 17 ni páginas de 16 KB.** Debe comprobarse primero el tamaño real de página y el arranque/carga Python/plugins en un dispositivo autorizado. Esta primera APK conserva íntegra la referencia original y sus riesgos para permitir una revisión controlada.


## Advertencias observadas, sin cambios improvisados

- Gradle: sintaxis Groovy de asignación mediante espacio obsoleta, con retirada prevista en Gradle 10. No se actualizó Gradle ni se ocultó el aviso.
- Media3: source/target Java 8 obsoletos para JDK 21, anotaciones no disponibles en classpath de compilación y APIs obsoletas. No equivalen por sí solos a un fallo de ejecución.
- Kotlin: constructores Locale obsoletos en `tw/nekomimi/nekogram/translate/Translator.kt`.
- Java: APIs obsoletas y operaciones unchecked; la compilación Java terminó sin errores.
- Recursos: sustituciones múltiples no posicionales en `CloudConfigSyncDate`; recursos localizados sin default eliminados por aapt. Requieren revisión de formatos/localización y pruebas, sin inventar un crash confirmado.
- Manifest: `supportsRtl` tiene una regla de replace sin otra declaración que reemplazar.
- C++/VoIP: aviso de formato `%d` para un `jlong` en `TMessagesProj/jni/voip/org_telegram_messenger_voip_Instance.cpp:1339`; también arrays de longitud variable como extensión Clang y anotaciones guarded_by ignoradas. Son hallazgos estáticos que merecen revisión; no se ha demostrado un crash en el dispositivo.
- CMake/NDK: avisos de compatibilidad futura con CMake anterior a 3.10; C++ muestra campos sin uso y APIs marcadas deprecated. No se modificaron fuentes para eliminar advertencias.

Estos avisos se conservan para revisión. No constituyen mediciones de lentitud, fugas, ANR o estabilidad en el Poco.

## Cambios y seguridad

No se modificaron archivos funcionales versionados. Solo documentación en `docs/build-step-3/` y configuración local ignorada (`local.properties`, permisos 600, con rutas SDK/Python). Se conserva el comportamiento, package y recursos originales. No se tocaron navegación, UI, animaciones, plugins, renderizado ni reproductor.

No se proporcionaron credenciales Telegram propias ni firma release. El código tiene fallbacks heredados para servicios; no deben considerarse configuración definitiva de FlexyGram. No se publican sus valores aquí. Antes de entregar una referencia destinada a uso real, configurar credenciales propias de forma privada y verificar su resolución. La firma Debug se selecciona por el código cuando falta `release.keystore`, pero solo la inspección del artefacto puede confirmarla.

## Continuación controlada

[Procedimiento reproducible y verificación de APK](reproduction.md). [Preparación de mediciones](measurement-plan.md).

No se certifica instalación, arranque ni rendimiento en el Poco X8 Pro. No hay mediciones ni pruebas físicas en Android 17/HyperOS 4. La declaración del dispositivo del usuario no sustituye una lectura del dispositivo real. La APK Debug será una referencia de diagnóstico; una futura evaluación de rendimiento necesita una variante controlada y comparable, teniendo en cuenta el coste de Debug.

## Requisitos antes de comenzar el Paso 4

1. Revisar este PR documental y los hallazgos de la APK; mantener la referencia por SHA-256 y fuente recuperable.
2. Verificar el Poco real: sistema/API, ABI, tamaño de página, frecuencia y navegación; resolver posibles conflictos de package, firma o versionCode sin borrar instalaciones ni datos existentes.
3. Configurar Telegram API ID/API Hash propios en un archivo privado y revisar los servicios heredados antes de usar cuentas reales o declarar una configuración definitiva. No se necesitan claves release para Debug.
4. Validar instalación, arranque, carga de todas las bibliotecas, motor Python/plugins y multimedia. Revisar específicamente las cuatro bibliotecas PT_LOAD de 4 KB, los avisos RELRO y la función de attach de debugpy. Cualquier corrección futura requiere un cambio separado y una nueva APK/hash; conservar esta base sin alterarla.
5. Aprobar escenarios, tolerancias y recogida privada de logs para las mediciones de [measurement-plan.md](measurement-plan.md). Debug no proporciona por sí solo una cifra representativa de rendimiento final.
6. Resolver la reproducibilidad de dependencias dinámicas mediante una propuesta revisable de locks/artefactos, sin actualizaciones arbitrarias ni cambios silenciosos. El inventario observado no equivale a una reproducción bit a bit acreditada.
7. Obtener aprobación expresa del propietario para la siguiente etapa. **El Paso 4 no se ha iniciado.**

Estado: entorno preparado y APK de diagnóstico construida/verificada estáticamente; pruebas de dispositivo, configuración propia y compatibilidad de 16 KB pendientes. No hay mediciones de latencia, fluidez, consumo, crashes o ANR.

