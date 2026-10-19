# Laboratorio Android obligatorio: API24 y páginas de 16 KB

Esta continuación **no ejecutó Android**. La alineación ELF, la resolución contra stubs API24, un build Gradle y los tests Linux no certifican carga ni funcionamiento en Android.

## Dos entornos separados, aislados y autorizados

1. Android API24 real, ARM64, páginas de 4096 bytes. Usar una máquina de laboratorio dedicada, nunca un teléfono personal. Un emulador solo es válido si existe una imagen ARM64 API24 compatible con el host y el emulador; comprobar disponibilidad con `sdkmanager --list`, no sustituirla por x86_64 ni por una API más nueva. Si no existe esa imagen, se necesita un dispositivo ARM64 API24 de laboratorio o una imagen AOSP API24 reproducida y documentada.
2. Android ARM64 con soporte real de páginas de 16384 bytes. Seleccionar una imagen/dispositivo expresamente preparado para 16 KB. No deducir el tamaño de página por la versión Android, el nombre de un AVD ni el éxito de zipalign.

Registrar host, imagen y su hash/origen, compilación Android, API, ABI, configuración AVD/hipervisor, versión de emulator/ADB y comandos. Arrancar sin snapshots ni datos anteriores. No activar cuentas, plugins, Firebase, push, traductores, red o Production. Ninguna cuenta o dato personal. ADB únicamente local; sin WiFi/telefonía/datos/SIM. Aplicar aislamiento de red también en el host/laboratorio; la ausencia de INTERNET de la app no prueba por sí sola ausencia de todo tráfico del sistema.

## Puertas previas (abortar ante discrepancia)

```sh
adb devices -l
adb -s "$LAB_SERIAL" shell getprop ro.build.version.sdk
adb -s "$LAB_SERIAL" shell getprop ro.product.cpu.abilist
adb -s "$LAB_SERIAL" shell getconf PAGE_SIZE
adb -s "$LAB_SERIAL" shell pm list packages io.github.jose22yt.flexygram
```

El serial debe corresponder al laboratorio verificado. API24 exige exactamente24 y ARM64; el segundo entorno debe devolver16384. No instalar sobre un cliente existente. Reproducir primero la receta de fuentes/wheels, overlay y build descrita en `EXPERIMENTAL-16K.md`; comparar SHA256, firma propia de laboratorio, API0/hash vacío, políticas Java/JNI, manifiesto sin INTERNET y los96 ELF objetivo. No usar APK de terceros o publicada como beta.

## Instalación y arranque offline (solo laboratorio)

Obtener la actividad lanzable de `aapt2 dump badging` de **esa APK**, sin adivinarla. Capturar logcat limpio, memoria de inicio, salida de PackageManager, errores del enlazador y de Python. Mantener los logs locales hasta revisar que no contengan valores sensibles; P0.1 continúa vigente.

```sh
adb -s "$LAB_SERIAL" logcat -c
adb -s "$LAB_SERIAL" install --no-streaming "$EXPERIMENTAL_APK"
adb -s "$LAB_SERIAL" shell am start -W -n "$VERIFIED_COMPONENT"
adb -s "$LAB_SERIAL" shell pidof io.github.jose22yt.flexygram.diagnostic
adb -s "$LAB_SERIAL" shell dumpsys package io.github.jose22yt.flexygram.diagnostic
adb -s "$LAB_SERIAL" logcat -d -v threadtime > lab-startup.log
```

Verificar proceso vivo, pantalla original, arranque frío y caliente, detener/reabrir, ausencia de crash/ANR, permisos concedidos y ninguna solicitud de autenticación. No pulsar flujos autenticados ni habilitar proveedores. Confirmar INTERNET ausente en el paquete instalado, API0/hash vacío y capacidades falsas del build realmente probado. Examinar `dlopen failed`, `cannot locate symbol`, versiones GNU, `UnsatisfiedLinkError`, relocalizaciones/RELRO, excepciones Chaquopy y fallos de importación. Comprobar `/proc/<pid>/maps` mediante `run-as`/instrumentación de laboratorio para identificar las cuatro bibliotecas reales y evitar confundirlas con copias del sistema.

## Carga JNI/Python y funcionalidad: harness pendiente, no prueba realizada

Preparar posteriormente un APK **androidTest de laboratorio**, firmado con la misma clave local, que arranque Chaquopy con el contexto objetivo y ejecute `tests/native_compatibility/runtime_cases.py` desde assets androidTest copiados al directorio privado temporal. No habilitar el motor de plugins para ejecutar el test. No añadir el harness a la aplicación activa ni liberar capacidades. Se necesita implementar/revisar ese runner antes de usarlo; este documento no afirma que ya exista una tarea connectedAndroidTest operativa.

Ejecutar los12 casos en el intérprete Python3.11 **empaquetado** y con las rutas reales de extracción Chaquopy. El argumento `--libdir` debe apuntar a las cuatro bibliotecas del wheel experimental, `--freetype` a esa libfreetype y `--font` a una fuente de fixture con licencia y hash registrados. El runner no debe seleccionar librerías host/sistema ni descargar paquetes. Archivar versiones lxml/Pillow, `LIBXML_VERSION`, `LIBXSLT_VERSION`, FreeType y hashes de cada `.so` cargado. `runtime_cases.py` rechaza eventos socket de Python, además de los controles Android; no es un cortafuegos de código C.

Casos incluidos: XML UTF8/entidades y rechazo de XML malformado; soporte zlib/LZMA; lectura gzip/XZ; XSLT1.0; EXSLT matemáticas; creación/renderizado de glifos FreeType; PNG RGBA y JPEG; texto Unicode Pillow; XPath/HTML/XSLT lxml con acceso externo denegado. Añadir corpus autorizado de TTF/OTF, Type1, PCF/BDF y fuentes comprimidas, valores límite, repetición y fallos de memoria/cancelación; registrar opciones efectivas. Comparar baseline original en API24/4KB, donde pueda cargar, con el experimento. No rebajar las aserciones si falta un formato.

Las extensiones Android no se validan instalándolas con pip en Linux. Los12 casos Linux de esta continuación utilizan bibliotecas fuente host y wheels manylinux de lxml/Pillow; deben repetirse sobre las bibliotecas ARM64 empaquetadas. Probar carga JNI y operaciones locales del cliente sin MTProto. Verificar que las guardas nativas continúan denegando inicialización/socket. Conservar resultados y trazas por entorno y commit, incluidos fallos, sin omisiones contabilizadas como aprobadas.

## Condición de salida

Antes de certificar API24/16KB: instalación y arranque, carga JNI/Python de los ELF reales, casos funcionales y estabilidad repetida aprobados en ambos entornos, más revisión de licencias/procedencia y del overlay. No basta un scanner verde. Cualquier permiso inesperado, fallback de proveedor, conexión, importación fallida o crash mantiene bloqueada la certificación. El laboratorio no autoriza beta, Production, distribución ni fusión del PR17.
