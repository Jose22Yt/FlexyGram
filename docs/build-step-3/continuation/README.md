# FlexyGram 1.0 — continuación verificable del Paso 3

Fecha: 18 de octubre de 2026. Responsable: @Lukhou23. Repositorio: Jose22Yt/FlexyGram. Alcance: recuperación/reconstrucción, análisis estático y entrega de una referencia Debug. El Paso 4 no se ha iniciado.

## Resultado y alcance

**Se ha reconstruido una APK real y se ha verificado estáticamente. Instalación y arranque NO probados. No se certifica compatibilidad completa con páginas de 16 KB.**

El directorio original `/workspace/scratch/1f84b79e43f3` ya no estaba disponible en el host accesible. Las búsquedas de archivos guardados no devolvieron la APK. GitHub Actions devolvió cero ejecuciones, por lo que tampoco había artefactos de esos workflows. Se usaron el commit, los submódulos, las herramientas y las evidencias del PR #2 para una reconstrucción; no se reutilizó una APK antigua o de origen desconocido.

El archivo entregado es **nuevo**. El hash anterior identifica otro artefacto que no se ha recuperado. No se afirma una reproducción bit a bit.

| Identidad comprobada en esta entrega | Resultado |
| --- | --- |
| Archivo | `FlexyGram-1.0-Clean-Baseline-arm64-debug.apk` |
| Tamaño | 111994391 bytes |
| SHA-256 calculado sobre los bytes entregados | `1ca683e5e4ef924ca9e7636afcd0c0b2c54de5064a46603ac5ae7b4f811278fe` |
| Fuente compilada exacta | `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2` |
| Código original conservado | `1ad6a60a6834ffca722b1a22f4fba27ecb29a061` |
| Package | `com.exteraless.app` |
| Versión | `13.0.2` / versionCode `1261` |
| Etiqueta y comportamiento | Base original Exteraless; no se renombra la interfaz |
| ABI instalable | arm64-v8a |
| ELF instalables bajo lib/arm64-v8a | 18 |
| Firma | Android Debug, apksigner verify exit 0; detalles de esquemas y certificado en evidence/apk-signature.txt |
| Certificado SHA-256 | `ba687de28eaaaa20bc77898f5520ba1b544216c6a3b88c333a96e593b3e94456` |
| SDK | min 24, target 36; compile 37 |
| Gradle | `BUILD SUCCESSFUL in 18m 34s`, exit 0; 247 actionable tasks: 39 executed, 208 up-to-date |
| Integridad ZIP | CRC correcto en APK y 6 archivos anidados |
| Alineación ZIP | zipalign `-c -P 16 -v 4`, exit 0 |
| Android ejecutado | Ninguno; ADB sin dispositivos; sin emulador instalado o ejecutándose |

## Fuente, herramientas y diferencias respecto al registro anterior

Se comprobaron los 16 submódulos frente a sus gitlinks y los 69 prebuilts registrados: todos coinciden con sus revisiones/hashes. `git diff --exit-code` de la fuente compilada no mostró cambios versionados. No se aplicaron parches de FlexyGram 0.39 ni se modificaron UI, navegación, animaciones, tacto, plugins, reproductor, burbujas o funciones nativas.

Se mantuvieron JBR 21.0.11+10-b1163.116, Gradle Wrapper 9.7.1, AGP 9.3.1, SDK 37 r2 y SDK 35 r2, Build Tools 36.0.0, NDK 27.2.12479018, CMake 3.31.6, Python host 3.11.17, Chaquopy 17.0.0 y target Android Python 3.11.14-0. Las descargas se contrastaron con los hashes oficiales o documentados. El Wrapper JAR también coincide con el hash oficial registrado.

La preparación local necesitó confianza TLS para el proxy autorizado, registro/licencias del SDK y corrección de estructura, permisos y enlaces simbólicos de los archivos de herramientas extraídos. Hubo intentos fallidos anteriores a la ejecución final: quedaron sus logs depurados. Un error en el script local de permisos omitía ELF y se corrigió. No se desactivó TLS ni se cambiaron versiones o fuentes de la aplicación para resolverlos. Las tareas y cachés reutilizadas durante los reintentos se generaron en esta reconstrucción con la misma fuente; no eran salidas de otra versión de FlexyGram. No se autenticaron cuentas ni servicios de terceros.

- SHA-256 histórico, **no entregado de nuevo**: `bd18650181e4201813900c98aff0d1c7f5d19cfe6e1fa659fb131e592dcf15f0`.
- SHA-256 nuevo: `1ca683e5e4ef924ca9e7636afcd0c0b2c54de5064a46603ac5ae7b4f811278fe`.
- Certificado histórico: `7bf6a9b5c4a701d3cb018d875f70bfed9ba0d3498b9ad58c85f73ca36977906b`.
- Certificado nuevo: `ba687de28eaaaa20bc77898f5520ba1b544216c6a3b88c333a96e593b3e94456`.
- Bibliotecas ELF con hashes iguales al inventario anterior: 96/97; con hashes diferentes: 1. El detalle identifica cada archivo en `evidence/baseline-comparison.json`.
- Las versiones de los paquetes Python coinciden con el inventario anterior: **True** (18 distribuciones de requirements; el inventario completo del APK también registra pyelftools 0.26 y setuptools 68.2.2 en bootstrap, fuera del alcance del inventario anterior).

La única biblioteca ELF con hash distinto es libtmessages.49.so. Se encontraron 447 apariciones de la ruta del workspace actual en sus bytes; las rutas de compilación son una fuente de variación identificada. Sin la biblioteca anterior no se puede atribuir toda la diferencia a esas rutas. Un certificado Debug nuevo cambia el bloque de firma y basta para distinguir los archivos. También se comparan los hashes de las bibliotecas empaquetadas; sin los bytes del APK anterior no es posible comparar todos los DEX, recursos, metadatos ZIP o atribuir cada diferencia. No se afirma que los APK solo difieran en la firma ni que la construcción sea reproducible bit a bit. Los inventarios de dependencias no equivalen a un lock transitivo.

## Bibliotecas nativas, Python y JNI

Se inspeccionaron **97 ELF**, de los que **96 son AArch64**. GNU readelf `-W -h -l -d -S` terminó con exit 0 en todos. El JSON conserva PT_LOAD completos, alineación, congruencia `p_vaddr - p_offset`, límites de archivo/memoria, DT_NEEDED, SONAME, RELRO, secciones, tamaños y SHA-256. No se ejecutaron binarios Android en el host Linux como sustituto de una prueba Android.

Los 18 ELF instalables de `lib/arm64-v8a` cumplen la comprobación de alineación PT_LOAD de 16 KB. Las siguientes bibliotecas en `assets/chaquopy/requirements-common.imy` tienen PT_LOAD de 4096 bytes y no cumplen el criterio estructural de 16 KB:

- `chaquopy/lib/libexslt.so`
- `chaquopy/lib/libfreetype.so`
- `chaquopy/lib/libxml2.so`
- `chaquopy/lib/libxslt.so`

Son incompatibilidades estructurales confirmadas para soporte nativo de 16 KB; no son cierres observados en un dispositivo. Un modo de compatibilidad del sistema no acredita soporte nativo pleno. Cambiar zipalign no corrige los ELF extraídos de los assets Python.

Empaquetado observado: 18 bibliotecas raíz comprimidas y 0 sin comprimir. La alineación ZIP se evalúa aparte de la ELF; las bibliotecas comprimidas se extraen y no se cargan directamente por mmap desde sus offsets comprimidos.

Se leyeron todas las entradas de los contenedores Python y sus CRC son correctos. Hay 1261 archivos .pyc con magic de Python 3.11 `a70d0d0a`, sin cabeceras truncadas; esto no ejecuta ni valida semánticamente los módulos. El runtime personalizado se compiló desde su submódulo fijado y fue empaquetado; su carga real, los imports Python y la invocación JNI siguen pendientes.

DT_NEEDED no encontrado entre los nombres empaquetados y la lista explícita de bibliotecas comunes de Android: **0 hallazgos**. Consultar los nombres/rutas en el JSON; una lista de nombres no prueba símbolos, versiones ni dlopen dinámicos. No es una certificación de cierre completo de dependencias.

El aviso de strip de libjnidispatch muestra archivos intermedios de ABIs retiradas (`armeabi`, `mips`, `mips64`) sin herramienta de strip. Esos ABIs no aparecen en el APK final. El libjnidispatch ARM64 empaquetado tiene readelf válido, PT_LOAD de 16 KB y el mismo hash que el inventario anterior. No se eliminaron componentes para ocultar el aviso.

El auxiliar de debugpy `attach_linux_amd64.so` sigue siendo x86-64 dentro de assets; no convierte la APK en una aplicación instalable x86-64. No puede cargarse como biblioteca ARM64. No se ha ejecutado la función de attach ni demostrado que la ruta normal de arranque lo seleccione. Se conserva sin eliminarlo.

## Revisión de GNU_RELRO y páginas de 16 KB

El chequeo numérico `(VirtAddr + MemSiz) % 0x4000` detecta **73 ELF ARM64** con final RELRO no alineado. No se etiquetan automáticamente como 73 fallos de ejecución.

Se revisó además el rango de páginas que podría quedar protegido como solo lectura y su intersección con secciones SHF_ALLOC/SHF_WRITE fuera del rango RELRO exacto. **3 ELF** presentan solapamientos con secciones escribibles que no son `.relro_padding`. Los solapamientos ARM64 están en libexslt, libxml2 y libxslt; en los otros 70 avisos de final RELRO este chequeo no encontró secciones escribibles no padding fuera de RELRO dentro de las páginas protegidas. Esto reduce falsos positivos, pero no certifica ejecución. Estos son riesgos estructurales adicionales a revisar; el JSON conserva cada sección y rango. Para afirmar un crash concreto faltan el linker/versiones/modo de compatibilidad efectivos y una escritura real sobre la zona afectada. El análisis estático no ejecuta ese código.

Ejemplos observados (valores hexadecimales; todos los detalles en JSON y readelf):

| ELF | VirtAddr RELRO | MemSiz | Resto 16 KB | Secciones escribibles fuera de RELRO en las mismas páginas |
| --- | --- | --- | --- | --- |
| `chaquopy/lib/libexslt.so` | `0x1a8f0` | `0x710` | `0x3000` | .data |
| `chaquopy/lib/libxml2.so` | `0x2064e0` | `0x7b20` | `0x2000` | .bss, .data |
| `chaquopy/lib/libxslt.so` | `0x541a8` | `0xe58` | `0x1000` | .bss, .data |

Referencias técnicas: [guía oficial Android de páginas de 16 KB](https://developer.android.com/guide/practices/page-sizes) y [Bionic: protección de GNU_RELRO](https://android.googlesource.com/platform/bionic/+/master/linker/linker_phdr.cpp). La guía separa alineación ELF, empaquetado y pruebas. Bionic redondea el rango RELRO a páginas; el comportamiento del teléfono debe verificarse directamente.

**Conclusión limitada:** este APK no acredita compatibilidad nativa completa con 16 KB. El host Linux usa páginas de 4096 bytes; no es un dispositivo Android de pruebas. El tamaño de página del Poco X8 Pro sigue desconocido.

## Propuesta controlada, sin modificar la referencia

1. Conservar esta APK/hash y sus fuentes como referencia. No sustituir ni eliminar bibliotecas para ocultar avisos.
2. Para los cuatro ELF de 4 KB, revisar las fuentes/wheels exactos de chaquopy-freetype 2.9.1, chaquopy-libxml2 2.9.8 y chaquopy-libxslt 1.1.32 (incluye libexslt). Preparar por separado su reconstrucción ARM64 con alineación de 16 KB y RELRO adecuado, manteniendo ABI Python, símbolos y funcionalidades. Para NDK r27, la propuesta debe contrastar `-Wl,-z,max-page-size=16384` y `-Wl,-z,common-page-size=16384` con el build de cada wheel y revisar el layout RELRO resultante; no basta con cambiar un flag de la aplicación.
3. Revisar individualmente los productores de los ELF con solapamientos RELRO y su configuración del linker. No reemplazarlos indiscriminadamente ni cambiar versiones de todas las dependencias.
4. Presentar el diff de configuración/fuentes y la procedencia de los binarios para revisión antes de integrarlo. Emitir una APK distinta con hash propio y contrastar ABI, DT_NEEDED y símbolos.
5. Probar carga y uso de las rutas afectadas en Android de 4 KB y de 16 KB. No aprobar compatibilidad solo porque el menú inicial abra o porque exista un modo de compatibilidad.

Esta propuesta no se implementó en el Paso 3 ni inicia el Paso 4.

## Instalación, arranque y próximos ensayos

`adb devices -l` no mostró dispositivos. No había emulador Android instalado o ejecutándose ni /dev/kvm. **No se ejecutaron instalación, primer arranque, carga nativa, inicialización Python, apertura de la pantalla principal ni Logcat. No existen logs de ejecución Android en esta entrega.** Los logs incluidos son de compilación y verificaciones estáticas.

Seguir [INSTALL-POCO.md](INSTALL-POCO.md). `com.exteraless.app` puede entrar en conflicto con Exteraless existente. No desinstalar ni borrar datos para forzar la instalación; pueden perderse sesiones, chats secretos, ajustes y archivos locales. Usar un dispositivo separado vacío si el package ya está instalado. Otro perfil no garantiza aislar firmas del mismo paquete. La referencia mantiene la configuración heredada: no introducir cuentas reales ni autenticar servicios antes de preparar configuración propia privada.

Pendientes exactos en un Android compatible autorizado:

1. Leer modelo, Android/API, HyperOS, ABI y `adb shell getconf PAGE_SIZE` del Poco real.
2. Comprobar conflicto de package/firma/versionCode sin reemplazar ni borrar una instalación con datos.
3. Instalar el archivo cuyo hash coincide con esta entrega y conservar el resultado exacto.
4. Capturar primer arranque y Logcat depurado, comprobar ausencia de cierres inmediatos y registrar la pantalla alcanzada.
5. Probar carga de JNI, inicialización del runtime Python e imports controlados de dependencias nativas.
6. Ejercitar los ELF afectados por PT_LOAD/RELRO y registrar el modo de compatibilidad del sistema si existe.
7. Comprobar pantalla principal con cuenta de prueba propia solo tras preparar servicios propios de forma privada. Llegar a la pantalla de acceso sin autenticar no demuestra este punto.

Un Poco de 4 KB no certifica 16 KB; hacen falta pruebas en ambos tamaños. No hay mediciones de rendimiento ni afirmación de funcionamiento perfecto.

## GitHub y entrega

La documentación se incorpora únicamente a `build/paso-3-clean-debug` en el mismo [PR #2](https://github.com/Jose22Yt/FlexyGram/pull/2), que debe seguir abierto y sin fusionar. La fuente compilada es el commit 082aff indicado arriba; el commit de documentación posterior no es otra compilación. Main y develop no se modifican. No se habilita Actions, no se ejecutan workflows heredados y no se publica Release.

La versión de las evidencias en GitHub contiene extractos identificados de logs extensos; el archivo descargable conserva los logs depurados completos.

Entregables: APK descargable, SHA256SUMS.txt, este informe, instrucciones de instalación y archivo de evidencias con logs depurados, análisis ELF y comparaciones. Las claves privadas y configuraciones privadas no se incluyen. El Paso 3 conserva pendientes de ejecución y compatibilidad; el Paso 4 permanece sin iniciar.
