# FlexyGram Diagnostic — preflight del laboratorio Android (solo lectura)

**Rama auxiliar independiente de P0.4c.** Este entregable no incorpora wheels experimentales, no modifica la APK, ni implementa androidTest. Su objetivo es rechazar un entorno equivocado **antes** de que un técnico autorizado valore cualquier procedimiento posterior de instalación. No ejecuta adb install, am start, logcat, ninguna escritura ADB ni una solicitud externa de red.

El script tools/android_lab_preflight/preflight.py usa **solo Python estándar** y ejecuta, como mucho, estas lecturas explícitas:

- adb devices -l y adb -s SERIAL shell getprop para identificar el emulador, API y ABI
- adb -s SERIAL shell getconf PAGE_SIZE para comprobar el tamaño **real** de página
- adb -s SERIAL shell pm path io.github.jose22yt.flexygram.diagnostic para detenerse si ya está instalada Diagnostic
- aapt2 dump badging y aapt2 dump permissions sobre una APK **local** para comprobar el ID Diagnostic y la ausencia del permiso INTERNET
- apksigner verify --verbose --print-certs y SHA-256 del archivo para cotejar firma v2 y certificado de laboratorio

No se admite un serial de teléfono físico: se requiere emulator-NNNN y propiedad QEMU, kernel aarch64, ABI primaria arm64-v8a y native bridge deshabilitado. No basta con arm64-v8a como ABI secundaria de un guest x86. Las pruebas de hardware dedicado precisarán revisión y autorización independientes. No deducir ARM64 ni páginas16KB del modelo o del nombre de AVD.

## Entornos previstos

| Perfil | Requisitos obligatorios |
| --- | --- |
| api24 | API **exactamente 24**, ABI arm64-v8a, páginas **4096** bytes |
| 16k | API **35 o superior**, ABI arm64-v8a, páginas **16384** bytes |

La exigencia API≥35 en 16k es una política conservadora del verificador, no una afirmación de que ninguna imagen experimental anterior pueda soportar esas páginas.

## Pruebas sin Android

Desde la raíz del repositorio:

~~~sh
python3.11 -m unittest discover -s tests/android_lab_preflight -v
python3.11 -O -m unittest discover -s tests/android_lab_preflight -v
python3.11 -m py_compile tools/android_lab_preflight/preflight.py
~~~

Las pruebas usan fixtures y mocks de ADB, aapt2 y apksigner; el ZIP ficticio no es un APK válido para Android. El conjunto tiene ahora 29 casos sintéticos: están pendientes de repetición en Python 3.11. **No ejecutan Android ni certifican carga JNI/Python.**

## Uso de solo lectura en laboratorio autorizado

adb, aapt2 y apksigner deben estar en PATH. Primero se comprueba únicamente el emulador, sin APK:

~~~sh
python3.11 tools/android_lab_preflight/preflight.py --serial emulator-5554 --profile api24
~~~

El resultado será EMULATOR_CHECKS_ONLY_APK_NOT_VERIFIED, que NO autoriza ninguna instalación.

Con una APK experimental **local** y previamente revisada por el propietario, solo se comprueban identidad, hash, permisos y firma, sin instalación:

~~~sh
python3.11 tools/android_lab_preflight/preflight.py \
  --serial emulator-5554 --profile 16k \
  --apk /ruta/local/controlada/flexygram-diagnostic-experimental.apk \
  --expected-apk-sha256 17c32ab39e3ac88213241a6bd643637469a4a4d47311a920b357a2e7b3128230 \
  --expected-cert-sha256 27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83
~~~

Esas huellas fueron informadas por Work en P0.4c HEAD 867e1178719ff0bda8d9b5381b17ecc3ae8391e5. La herramienta **no incluye la APK ni garantiza que ese artefacto exista**. Para otra APK o firma debe existir una nueva autorización y nueva revisión.

La salida JSON indica las condiciones comprobadas y un hash abreviado del serial, no el serial original. **Esta herramienta no es el gate final**: el único controlador de instalación y ejecución es el runner de PR #17. Los hashes suministrados como argumentos deben cotejarse por separado contra su contrato revisado: no se permiten pins elegidos arbitrariamente para certificar un experimento. Estados:

- BLOCKED (exit1): falla alguna condición del entorno, herramienta, APK o firma.
- EMULATOR_CHECKS_ONLY_APK_NOT_VERIFIED (exit0): únicamente verificaciones previas del emulador.
- READY_FOR_HUMAN_REVIEW_NOT_RUNTIME_VALIDATED (exit0): verificaciones previas de entorno/identidad/firma, **sin instalar ni ejecutar**.

**Exit 0 nunca certifica** arranque, carga JNI/Chaquopy, ELF16KB, API ID/hash en DEX, ausencia universal de secretos, tráfico, seguridad de app ni distribución.

## Conteo privado de errores de un log local

Opcional: --log-file /ruta/local/lab-startup.log. Se revisa únicamente un log local existente, previamente depurado y de hasta 16 MiB. **Cualquier indicador crítico de linker, Python, crash/ANR o memoria ahora bloquea (exit1).** Si no se aporta log, la ausencia de indicadores es desconocida, no cero. El script **no ejecuta logcat**, no imprime líneas, rutas, números ni datos del log; solo devuelve conteos de categorías (cargador nativo, Python, crash/ANR, memoria). No subir el log original ni copiar valores privados a GitHub.

## Corrección tras revisión de Work

Work detectó dos situaciones problemáticas mediante pruebas sintéticas: aceptar un guest x86 que anuncia ARM64 como ABI secundaria y reportar preflight favorable pese a indicadores críticos en un log opcional. El código se endureció sin añadir instalaciones, escritura ADB ni captura de logs.

Se añadieron siete regresiones: kernel x86, ABI primaria x86, native bridge activo, flag de ejecución bridge, kernel traducido, log crítico y log limpio. **Los 29 casos corregidos todavía requieren ejecución en el checkout de Work con Python 3.11 y -O.** No se declara nueva certificación Android.

El resultado READY_FOR_HUMAN_REVIEW_NOT_RUNTIME_VALIDATED sigue siendo solo un control previo. El PR #21 no acepta directamente el formato de PR #17 y requiere adaptación explícita sin perder evidencias primarias.

## Límites y siguientes pasos

- El entorno de Work no disponía de emulador ARM64/KVM/ADB; **no se ha ejecutado ninguna prueba real Android** en esta contribución.
- No hay cambios en gradle, JNI, Python de producción, firmas, permisos, Production, wheels ni el PR #17.
- No se reemplaza el runner androidTest pendiente ni se demuestra la carga de las cuatro bibliotecas 16KB.
- El procedimiento de laboratorio completo continúa descrito en el [PR #17, Android lab](https://github.com/Jose22Yt/FlexyGram/blob/867e1178719ff0bda8d9b5381b17ecc3ae8391e5/docs/security-p04c/ANDROID-LAB-16K.md).
- Antes de fusionar, Work debe ejecutar la suite con Python3.11 y comprobar las opciones reales de ADB/aapt2/apksigner de su SDK.
- Dejar este PR en borrador; no fusionar main/develop sin revisión. No habilitar Actions, Production, Telegram ni red de aplicación.
