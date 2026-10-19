# Compatibilidad Android — hallazgos y experimento propuesto

No se cambia configuración nativa y no se compila/instala en esta etapa. Fuentes oficiales consultadas 2026-10-19; el inventario local y las evidencias históricas tienen prioridad para describir lo realmente construido.

## Matriz actual

| Componente | Valor del proyecto/evidencia P0.3g | Consecuencia / revisión necesaria |
|---|---|---|
| SDK | compileSdk37, targetSdk36, minSdk24 | Compilar con 37 no activa automáticamente comportamientos target37 ni prueba ejecución en Android17 |
| Toolchain | Gradle9.7.1, AGP9.3.1, JDK21, Build Tools36.0.0 | Mantener referencia reproducible; evaluar Build Tools37.x recomendado para SDK17 en experimento separado, no actualizar todo por reflejo |
| NDK/CMake | NDK27.2.12479018, CMake ejecutado3.31.6 | Declaración CMake `3.31.6+` no fija exactamente la versión; registrar ruta/hash/versión efectiva antes de comparar |
| Plataforma JNI | `-DANDROID_PLATFORM=android-27`, minSdk24 | Inconsistencia real del contrato mínimo; ejecución API24–26 no acreditada |
| Página nativa | ANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON | No reconstruye prebuilt ni wheels; no certifica 16KB |
| Chaquopy/Python | Plugin17.0.0, runtime fuente propio de submódulo, Python3.11; host registrado3.11.17 | Examinar versión efectiva de targets y submódulo, no inferirla del plugin ni de comentarios que mencionan3.12 |
| Python wheels | lxml, pillow, etc. declarados sin versión en pip.install | Un caché offline conserva una resolución, pero no garantiza resolución futura idéntica; faltan hashes/versiones por ABI/Python y repositorio de wheels reproducible |
| Empaquetado | useLegacyPackaging=true; ARM64 solicitado con NATIVE_TARGET | Compresión/ZIP y alineación ELF son comprobaciones distintas; Python contiene ELF dentro de assets/anidados |

### API24 frente a plataforma27

La [guía NDK de versiones](https://developer.android.com/ndk/guides/sdk-versions) advierte que símbolos nativos se resuelven al cargar y que un mínimo nativo superior al anunciado puede fallar aunque no se invoque el API nuevo. No afirmar que todas las bibliotecas usan símbolos27 ni que toda instalación24 falla: hay que medirlo.

Experimento, pendiente de aprobación: conservar baseline; capturar compile_commands.json, argumentos finales y notas ELF de cada unidad/binario; inventariar símbolos indefinidos versionados, DT_NEEDED, dependencias transitivas y API de introducción contra stubs24/25/26/27. Revisar prebuilt y runtime Chaquopy, no solo libtmessages. Construir rama de prueba con plataforma24 y toolchain fijada, registrar fallos y guardas dlopen/dlsym/weak donde proceda. Ejecutar carga/imports en ARM64 API24,26,27. Si una dependencia exige27, reconstruir/sustituir con preservación de funciones o proponer elevar minSdk con impacto explícito; no ocultar incompatibilidad anunciando24. No modificar minSdk ni ANDROID_PLATFORM en este PR.

### 16 KB

La auditoría histórica confirmó PT_LOAD de 4096 para `libexslt.so`, `libfreetype.so`, `libxml2.so`, `libxslt.so` bajo assets/Chaquopy; no cumplen el criterio ELF16KB. Ver [informe nativo](../security-startup-review/NATIVE.md). P0.3g no aporta una nueva certificación integral de esos binarios; su comprobación de 18 ELF raíz AArch64 no cubre por sí sola wheels anidados. Reextraer TODO ELF del futuro artefacto y repetir inventario, sin transferir resultados de otra APK.

Plan: mapear wheel→biblioteca→versión→fuente/licencia→DT_NEEDED; guardar hashes, toolchain y receta; reconstruir o actualizar controladamente la pila lxml/XML/XSLT y Pillow/freetype sin eliminar funciones. Chaquopy17 soporta páginas16KB en su runtime, pero [su changelog](https://chaquo.com/chaquopy/doc/current/changelog.html) advierte que numerosos wheels antiguos no cargan y recomienda Python3.13+ para mejor cobertura. La [tabla de compatibilidad](https://chaquo.com/chaquopy/doc/current/versions.html) incluye API24 y AGP9.3 para17.0. Eso no certifica este fork runtime ni obliga a migrar a3.13: comparar primero disponibilidad de wheels, APIs de plugins y comportamiento. Mantener3.11 reconstruyendo wheels o migrar Python son alternativas sujetas a evidencia.

Para cada PT_LOAD revisar p_align>=0x4000 y congruencia p_offset/p_vaddr para16KB, DT_NEEDED y símbolos. Analizar GNU_RELRO y páginas compartidas por secciones escribibles: un aviso RELRO aislado no equivale a fallo confirmado. Revisar hardcodes4096/PAGE_SIZE y usar tamaño real donde corresponda. No editar metadatos ELF o borrar bibliotecas para silenciar alertas.

Aplicar [guía oficial16KB](https://developer.android.com/guide/practices/page-sizes): `llvm-readelf -lW/-dW`, `zipalign -c -P 16 -v 4` y carga efectiva. Con bibliotecas comprimidas la alineación ZIP de entrada no sustituye la de los ELF extraídos; con AAB comprobar APKs que produce bundletool. Ejecutar XML/XSLT/fuentes y JNI/Python en4KB y16KB sin modo de compatibilidad que oculte fallos. No asumir page size por marca/modelo/Android del teléfono.

### Android17 / API37

[Setup oficial](https://developer.android.com/about/versions/17/setup-sdk): SDK37 y revisión explícita de target37; no confundir target36 actual con soporte validado. Revisar por separado [cambios para todas las apps](https://developer.android.com/about/versions/17/behavior-changes-all) y [cambios al apuntar a37](https://developer.android.com/about/versions/17/behavior-changes-17). Priorizar arranque/memoria y ApplicationExitInfo, carga JNI/Python, reflexión sobre MessageQueue/static-final, OTP/receivers, red local/casting, componentes y servicios en segundo plano. No añadir permisos SMS/red local automáticamente ni alterar animaciones/rendimiento para declarar compatibilidad. Las pruebas distinguirán target36 ejecutado en17 de un futuro cambio target37. La configuración actual usa SDK37 y BuildTools36; no llamar a esa diferencia un fallo de compilación ya demostrado.

## Laboratorio reproducible pendiente

Conservar [procedimiento offline existente](../security-p03a/VALIDACION-ANDROID-PENDIENTE.md) y su bloqueo de beta. No repetir intentos de emulador inexistente en este entorno. Preparar otro host autorizado con aceleración/imagen ARM64 real compatible; si el host solo admite x86_64, puede aportar evidencia adicional, nunca sustituir ARM64. Fijar hashes de imágenes, emulator/platform-tools, SDK, NDK, CMake, JDK, Gradle, Python y submódulos. Sin cuentas, Telegram instalado, datos personales, credenciales o acceso de red del huésped/host durante Diagnostic. Snapshots limpios, sin restauraciones automáticas.

| Entorno | Comprobación de aceptación |
|---|---|
| API24 ARM644KB | Instalación, linker/JNI/imports requeridos; cero símbolos ausentes; no prometerAPI24 hasta superarla |
| API26/27 ARM644KB | Frontera plataforma27, restauración y componentes según versión |
| API35/36 ARM644KB y16KB | ELF y cargas reales por página, sin depender de modo compatibilidad; framework de backup/D2D con fixtures |
| API37 ARM64 | Arranque offline target36 y, tras cambio separado aprobado, target37; registrar página real, permisos y cambios de plataforma |

Comandos de recolección futura, solo dispositivo de laboratorio verificado: `adb devices -l`, `adb -s SERIAL shell getprop ro.kernel.qemu`, `getprop ro.build.version.sdk`, `getprop ro.product.cpu.abi`, `getconf PAGE_SIZE`; exigir serial del emulador autorizado. Inspeccionar APK con apkanalyzer/aapt2 y apksigner; registrar SHA/commit/certificado. Instalar y lanzar entrada obtenida del manifiesto, capturar logcat limpio filtrado por UID/proceso, dumpsys package, appops y servicios activos; comprobar INTERNET ausente y permisos sensibles no solicitados en Diagnostic. Repetir force-stop/cold start y restauración sintética; medir contadores por UID y captura host/guest, observando tráfico delegado a otros UID. Cero red con firewall no demuestra que no hubo intentos: combinar contadores/logs y bloqueos internos. Los imports necesarios que Diagnostic bloquea requieren arnés nativo/Python aislado específico, no abrir plugins/auth para probarlos.

Guardar evidencia por SHA/variante/API/ABI/página y resultado: manifiesto fusionado, APK hash, comandos/versiones, ELF/ZIP, logcat y lista de pruebas/omisiones. Capturar solo datos sintéticos; revisar y redactar identificadores antes de publicar. Rechazo: crash, restauración de fixture-token, permiso/servicio inesperado, sesión importada, tráfico o carga incompatible. Ninguna ejecución de esta matriz se afirma realizada aquí.
