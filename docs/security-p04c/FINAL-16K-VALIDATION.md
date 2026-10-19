# P0.4c — validación final de cuatro ELF en experimento aislado

Base aprobada recuperada y verificada: `a25295a9d567a626e008fc55ca97d80112c5f65b`. PR17 continúa en borrador, sin fusión. Esta continuación añade herramientas, pruebas y documentación; **no reemplaza las dependencias activas del Diagnostic aprobado**. La APK anterior conserva SHA256 `40cac89aeb2087e9a467b04fc6a6fad2d7b1651482f8ed65fa053665e9d491d1`. Los informes/evidencias anteriores de155 pruebas permanecen en Git. Identidad @Lukhou23, GPL y créditos originales conservados.

## Resultado verificable

- **175 pruebas de proyecto aprobadas,0 fallos,0 omisiones**: las155 conservadas y ejecutadas de nuevo (102 regresiones +53 controles P0.4c), más20 regresiones nuevas. La puerta actual73/73 pasa también con `python -O`, sin contar esa repetición dos veces.
- **12/12 funcionales Linux**,0 fallos/omisiones: bibliotecas reconstruidas para host y fixtures manylinux lxml5.3.0/Pillow11.0.0. No son pruebas de los ELF ARM64 ni de Android.
- PR19 HEAD `103e9e6b1fada37254ce788d0cb2c19e65891c36`: **15/15**, strict **11/11 señales**, sin errores de import/retorno booleano; pasan los negativos de comentarios, métodos vecinos, esperas ajenas y mutaciones. No se modifica navegación ni se deduce latencia medida. No se fusiona PR19.
- Build completo del checkout experimental: **BUILD SUCCESSFUL en8m35s**,249 tareas (113 ejecutadas,136 cacheadas), incluyendo JNI y Chaquopy sin NATIVE_TARGET=SKIP. Tras finalizar los wheels, reinstalación Python forzada31s/7 tareas y assemble final **BUILD SUCCESSFUL en1m27s**,249 tareas (15 ejecutadas,234 up-to-date). La compilación nativa del primer paso se reutiliza porque sus fuentes/políticas no cambian; no se afirma que el último empaquetado recompiló cada C++.
- APK final: **96/96 ELF ARM64 compatibles estáticamente con4KB/16KB**,0 DT_NEEDED ausentes,0 imports fuertes sin resolver,0 discrepancias de versión,0 imports fuertes fuera de su closure y0 solapamientos RELRO escribibles. Total97 ELF:96 objetivo y1 payload auxiliar x86_64 heredado debugpy, visible y sin eliminar. Estado **STATIC_CLEAN_PENDING_ANDROID**, distribución **false**.

## Contratos de las cuatro bibliotecas

| Biblioteca | Nombres exportados original/nuevo | GNU tipos/datos/versiones | SONAME y DT_NEEDED (incluido orden) | Reproducción idéntica A/B |
|---|---:|---|---|---|
| libfreetype.so | 199 / 199 | Igual | Igual | Sí |
| libxml2.so | 1846 / 1846 | Igual | Igual | Sí |
| libxslt.so | 273 / 273 | Igual | Igual | Sí |
| libexslt.so | 24 / 24 | Igual | Igual | Sí |

Se preservan también las tablas .hash/.gnu.hash y las funciones/opciones revisadas. Se mantienen FreeType2.9.1, XML2.9.8, XSLT1.1.32/EXSLT y XZ/LZMA5.2.4 estático. zlib sigue siendo dependencia de plataforma; no aparece liblzma.so ni una biblioteca host en el APK. Los cuatro ELF empaquetados coinciden **byte a byte** con los candidatos fuente finales.

Eliminadas las diferencias estáticas detectadas de exportaciones, objetos absolutos, etiquetas de límites, tipos/binding/visibilidad/tamaños públicos, padres GNU y DT_NEEDED. No se relaja `acceptance.py`, no se parchea p_align ni se eliminan funciones. GNU ld2.42 se construye de fuente fijada para las tres bibliotecas XML; FreeType sigue con NDK/LLD. La receta conserva todos los objetos, reconstituye límites desde el layout real y controla orden de enlace. Detalle en [receta y decisiones](EXPERIMENTAL-16K.md).

**No quedan discrepancias ABI en los controles estáticos ejecutados.** Esto no garantiza paridad total de comportamiento: formatos de fuentes, todos los encoders/decoders, dlopen/dlsym, weak imports, namespaces, constructores, ART y carga JNI/Python requieren Android. No se afirma que el código fuente reconstruido sea binariamente igual al original de4KB; sí que conserva los contratos comprobados y es reproducible consigo mismo.

## Wheels y procedencia

Dos construcciones separadas producen los mismos cuatro ELF y tres wheels. Se mantienen los26 originales verificados por hash/CRC y18 versiones; el overlay ARM64 conserva15 wheels y sustituye3. METADATA, licencias, cabeceras, créditos y demás contenido permanecen idénticos; solo cambian cuatro ELF, WHEEL y RECORD. Build tag distinto, plataforma android_24_arm64_v8a y hashes nuevos:

- `chaquopy_freetype-2.9.1-3flexygram16k-py3-none-android_24_arm64_v8a.whl`: `f4308f6ad71eefca3cd9def87ee8c2673499b6dd10810daa23c1a22e805fc937`.
- `chaquopy_libxml2-2.9.8-3flexygram16k-py3-none-android_24_arm64_v8a.whl`: `2b47fe307311e932c4502ad9eec108f070eec6f36c03d4d97a2d22222387badb`.
- `chaquopy_libxslt-1.1.32-3flexygram16k-py3-none-android_24_arm64_v8a.whl`: `f8d9b05b17dfbc498c9edf22d24b65c37f9c3ad92a10a49e61b267130548d70f`.

El requirements experimental exige los18 hashes, `--no-index --only-binary :all: --require-hashes`. Instalación cruzada offline18/18 y la instalación real de build Chaquopy pasan; no equivalen a ejecutar Python en Android. Los locks activos mantienen SHA256 `3b256cf2e29614bf33d3115a0a84a80f4df4097bb529cdd5d7dc977e579462a6` y `2473f225e52f03d9de4e52b524f341c9ba1066118528f82425ecda20be9a70c9`. No hay sustitución x86_64 propuesta.

## APK interna y protecciones

- SHA256 **`17c32ab39e3ac88213241a6bd643637469a4a4d47311a920b357a2e7b3128230`**, 125488383bytes; **no adjunta, instalada ni distribuida**.
- `io.github.jose22yt.flexygram.diagnostic`, FlexyGram Diagnostic,13.0.2/1261, ARM64. Firma propia de laboratorio RSA3072, v2 verificada; certificado SHA256 `27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83`. No claves privadas/contraseñas en Git.
- Manifiestos fusionado/binario sin INTERNET; permisos limitados a ACCESS_NETWORK_STATE y permiso propio de receptor. API ID0/hash vacío, seis capacidades falsas. Autenticación, MTProto, Firebase/push, restauración, plugins y traducción continúan denegados. No se habilita ningún servicio remoto.
- Scope Java/JNI `0f92362819e8a4973909188235d68012a364c974d8e430ce61370e88da8ed181:diagnostic`. Tres entradas JNI de inicialización/socket verificadas solo RET, .text empaquetado igual al enlazado; compilador real target aarch64-none-linux-android24.
- Scanner final de APK/DEX/IMY/recursos, dependencias y JAR fuente pasa con el registro de claves/marcadores retirados; sin clases duplicadas ni transporte ficticio. No es una auditoría universal de secretos ni prueba de tráfico.
- zipalign16KB y firma pasan, separados del resultado ELF. Production se rechaza realmente con FLEXYGRAM_PRODUCTION_INCOMPLETE/exit1; no APK productiva.

## Entorno y errores resueltos

Python3.11.17/pyelftools0.33, JDK21, Wrapper/Gradle9.7.1, AGP9.3.1, SDK37, BuildTools36.0.0, NDK27.2.12479018, CMake3.31.6 y Chaquopy17 conservados. Los16 submódulos siguen fijados. Kotlin incremental se desactiva solo por argumento local ya documentado, sin cambiar gradle.properties.

El primer intento paralelo de Production no alcanzó la política por timeout del lock de caché Gradle. La repetición secuencial final sí llega a FLEXYGRAM_PRODUCTION_INCOMPLETE (exit1,12s); ambos logs se conservan. No se contabiliza el timeout como prueba del bloqueo.

Se resolvieron: checkout experimental inicialmente sin acceso a media; makeinfo ausente en el build del linker (se omite solo generación de manuales); stubs NDK con DWARF zstd incompatibles con ese GNU host (se descomprimen copias y se comprueba ABI idéntica); CFLAGS no heredado por FreeType/CMake (prefix-map explícito); metadatos GNU omitidos por LLD; classpath de scanner inicialmente solo Java (se incorporan las clases Kotlin reales). Una regeneración en un directorio reutilizado falló por inventario/hash; los conjuntos finales se generaron en directorios nuevos e inmutables y se verificaron completos, sin aceptar el fallo como éxito ni relajar verificadores.

Se liberaron1824 objetos temporales de la caché CMake de la base por falta de disco, conservando APK, bibliotecas enlazadas, fuentes, compile_commands, wheels y evidencias; hash de APK antes/después idéntico. No se borraron funciones o bibliotecas. Advertencias heredadas de C++ (tipos de formato, deprecaciones, campos sin uso) y deprecaciones Gradle permanecen registradas; no se parchean sistemas ajenos.

## Android y decisiones pendientes

Host x86_64, sin /dev/kvm, binario emulator, imágenes Android, QEMU ARM64 ni dispositivos ADB. **0 instalaciones/arranques/pruebas reales Android**. No se prueba ni se accede a un teléfono personal. [Procedimiento API24 y16KB](ANDROID-LAB-16K.md) detalla preparación, aislamiento, instalación controlada futura, permisos, arranque, carga de las bibliotecas reales y12 fixtures. El runner androidTest aún necesita implementación/revisión en el laboratorio; no se presenta como herramienta ya ejecutada.

Pueden revisarse las herramientas, contratos y evidencias de esta continuación; **no promover los wheels a las dependencias activas ni certificar API24/16KB/beta hasta probar ambos laboratorios y recibir aprobación**. No hay permiso de fusión del PR17. Main/develop se conservan. PR2 abierto; PR16 y18 continúan pendientes, sin integración ni icono activado. PR19 resulta favorable para revisión documental separada, previa autorización y actualización explícita de límites de alcance; no se fusiona aquí. Actions no se activa y se verifican0 ejecuciones; ese contador no sustituye una lectura administrativa de permisos.

## Evidencias y comandos

Los logs publicados normalizan únicamente espacios finales; log-normalization.json conserva los hashes raw y normalizados.

Todo en [evidence-16k-experimental](evidence-16k-experimental/), con SHA256 individual, versiones, inputs y comandos de enlace. `test-inputs.json` liga hashes del código probado al commit que contiene este informe; el APK usa la base a252 más el overlay exacto de `overlay.json`. El código Android original no se modifica en este commit. Las evidencias anteriores siguen en evidence-completion como historia, no se reutilizan como ejecución nueva.

Comandos de pruebas: `python3.11 tests/native_compatibility/run_gate.py`; repetición con `-O`; unittest discover de security26, translation_safety27, translation_runtime4, translation_dependency/test_prototype12 y test_facade14, translation_staging10 y build_variants9. PR19: `python3.11 -m unittest discover -s tests/navigation_performance -v` y `python3.11 tools/navigation_performance/audit.py --strict`, ejecutados con Python3.11.17 en su checkout HEAD103e9e6b. Las15 pruebas incluyen negativos y no prueban ausencia universal de falsos positivos.

Compilación: NATIVE_TARGET=arm64-v8a, `:TMessagesProj:assembleDiagnosticDebug`, JNI/Chaquopy completos; reinstalación selectiva `:TMessagesProj:installDiagnosticDebugPythonRequirements --rerun-tasks` antes del assemble final para impedir que se reutilizasen wheels intermedios. Estado estático final no autoriza paso4, beta ni servicios reales.
