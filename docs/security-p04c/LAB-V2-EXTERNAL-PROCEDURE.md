# Laboratorio v2 en Linux — procedimiento externo

**Continuación del 20 de octubre:** disponible un lanzador de infraestructura vacío
`tests/native_compatibility/empty_avd_boot.py`. Reutiliza la inspección del runner existente;
no instala APK. Los304 tests del HEAD aprobado y318 tras añadir14 regresiones pasaron
normal y `-O`. Véase `LAB-EXECUTION-2026-10-20.md`; las instancias SDK/AVD del scratch
anterior fueron retiradas por mantenimiento, no confundir las recetas con instancias vivas.

Preparación de infraestructura; no habilita instalación, firma, autenticación ni distribución.
El ejecutor funcional continúa siendo `tests/native_compatibility/android_lab/run_lab.py`.
Su contrato v1 sigue congelado: **no ejecutarlo con el candidato nuevo hasta revisar y activar v2**.

## Recursos y estructura

Host de laboratorio sin cuentas/datos personales, Linux con namespaces de usuario/red
permitidos, `iproute2`, Python3.11, JDK21 y espacio suficiente para imágenes y escrituras
de dos particiones de datos2GB (se recomienda margen libre de10GB después de materializar).
No usar teléfonos personales ni subir la APK a un proveedor externo.

Herramientas comprobadas: Emulator37.2.12/build16428233, ADB37.0.1, CLI Tools19,
Build Tools36.0.0. CLI Tools debe estar bajo `$SDK/cmdline-tools/19.0/`; una ubicación
externa hizo inferir una raíz SDK incorrecta en la ejecución real. Se conserva el aviso de
XML SDK37 v4 con CLI19; no equivale a un fallo de los AVD API24/API35 creados.

Crear fuera del checkout directorios privados para SDK, archivos originales de imágenes,
Android user home, AVD y logs. No cambiar HOME ni reutilizar `.android` personal.
Exportar `ANDROID_HOME`, `ANDROID_SDK_ROOT`, `ANDROID_USER_HOME` y `ANDROID_AVD_HOME`
hacia esos directorios nuevos. En los ejemplos, `$REPO` es el checkout revisado,
`$SDK` su SDK privado y `$LAB` el directorio privado de evidencias.

URLs/hashes de imágenes exactos están en `lab_host_preflight.IMAGES`:

- API24 r09: `https://dl.google.com/android/repository/sys-img/android/arm64-v8a-24_r09.zip`
- API35 ps16k r05: `https://dl.google.com/android/repository/sys-img/google_apis/arm64-v8a-ps16k-35_r05.zip`

Los recibos del informe JNI fijan los SHA-256 completos. Se verificaron ambos ZIP completos
con CRC, ABI, API y cabeceras de kernel, incluyendo gzip. No sustituir por x86-64 ni por API37.
Adquirir herramientas/imágenes en la fase online de preparación; la APK privada nunca se sube.

## Materializar y registrar imágenes sin arrancar Android

```bash
python3.11 "$REPO/tests/native_compatibility/materialize_lab_images.py" \
  --archive "$LAB/archives/arm64-v8a-24_r09.zip" --profile api24-4k \
  --destination "$SDK/system-images/android-24/default/arm64-v8a" \
  --output "$LAB/image24.json"
python3.11 "$REPO/tests/native_compatibility/materialize_lab_images.py" \
  --archive "$LAB/archives/arm64-v8a-ps16k-35_r05.zip" --profile arm64-16k \
  --destination "$SDK/system-images/android-35/google_apis_ps16k/arm64-v8a" \
  --output "$LAB/image35.json"
```

Exige destinos nuevos; copia dispersa con hash de lectura posterior, sin cambiar bytes.
Un fallo no autoriza reutilizar un directorio parcial. Los metadatos públicos registrados
proceden de los catálogos oficiales y están preservados en `lab-v2-recipes/sdk-metadata/`.
Tras comprobar los hashes del índice de evidencias, copiar cada `*-package.xml` como
`package.xml` al directorio Emulator o imagen correspondiente. Esto resuelve el error
real `emulator package must be installed` sin cambiar de versión ni descargar otra imagen.
Conservar los avisos y los recibos; los metadatos no son una autorización de licencia adicional.

## Crear exclusivamente los perfiles nuevos

```bash
printf 'no\n' | "$SDK/cmdline-tools/19.0/bin/avdmanager" create avd \
  -n flexygram-api24-offline-v2 -d pixel_2 \
  -k 'system-images;android-24;default;arm64-v8a' \
  -p "$ANDROID_AVD_HOME/flexygram-api24-offline-v2.avd"
printf 'no\n' | "$SDK/cmdline-tools/19.0/bin/avdmanager" create avd \
  -n flexygram-api35-offline-v2 -d pixel_2 \
  -k 'system-images;android-35;google_apis_ps16k;arm64-v8a' \
  -p "$ANDROID_AVD_HOME/flexygram-api35-offline-v2.avd"
"$SDK/emulator/emulator" -list-avds
```

No usar `--force` sobre perfiles existentes. Las configuraciones de referencia están en
`lab-v2-recipes/*-config.ini`; actualizar claves existentes, sin duplicarlas. Se comprobaron
ARM64,2GB RAM,2 núcleos y configuración gráfica sin GPU física. Es configuración de host,
no una modificación de las políticas/animaciones del cliente. Registrar hashes de config.

```bash
python3.11 "$REPO/tests/native_compatibility/lab_host_preflight.py" \
  --sdk "$SDK" --archives "$LAB/archives" --output "$LAB/preflight.json"
```

**Comprobación de espacio añadida tras el informe Work (2026-10-20):**
`lab_host_preflight.py` exige ahora **10 GiB libres como mínimo** en el
filesystem de `ANDROID_AVD_HOME` (si está definido; en caso contrario
comprueba el filesystem del SDK). Incluye `storage.target`,
`storage.free_bytes`, `storage.required_free_bytes` y `storage.status`
en el recibo, sin publicar rutas privadas. Un directorio AVD inexistente,
una lectura de filesystem fallida o espacio insuficiente devuelven BLOCKED.
Esto es un **margen operativo conservador** para los 2 AVD y sus datos/logs,
no una certificación de arranque ni una sustitución de aislamiento de red.
El host anterior quedó con solo **265818112 bytes** libres tras materializar
ambas imágenes. Se añadieron cuatro regresiones sintéticas y el nuevo gate
espera **304 pruebas mínimas**; esta cifra todavía debe reejecutarse desde
un checkout real. Las **300/300** del informe anterior son evidencia de Work
para el HEAD previo.

Exit1/BLOCKED significa **no arrancar**. Un READY solo permite comprobar después un boot
offline; no certifica que el emulador acepte ARM64/TCG. KVM ausente no implica por sí solo
que TCG sea imposible; la opción `-accel off` tampoco demuestra que funcione.

## Arranque vacío dentro de red aislada, sin APK

Solo en un host donde el preflight y los permisos de laboratorio sean válidos. Ejecutar
**todas** las operaciones de Emulator y ADB dentro del mismo namespace, nunca en la red
normal del host. Desactivar proxies heredados para esta fase y usar un user home Android
nuevo. El namespace debe contener únicamente loopback, sin veth/tun/uplinks ni rutas externas.

```bash
export SDK LAB REPO
env -u HTTP_PROXY -u HTTPS_PROXY -u ALL_PROXY -u http_proxy -u https_proxy -u all_proxy \
  unshare --user --map-root-user --net -- bash --noprofile --norc
# Dentro del namespace:
ip link set lo up
ip -o link show
ip route show table all
ip -6 route show table all
```

Abortar si aparece una interfaz distinta de loopback o una ruta externa. Conservar estas
salidas y la identidad del namespace. La ejecución de Work no pudo superar este punto.
Mantener las variables `$SDK`, `$LAB` y Android user/AVD home hacia los directorios privados.
Arrancar **un perfil cada vez**, con logs separados, sin instalar APK:

```bash
"$SDK/emulator/emulator" -avd flexygram-api24-offline-v2 -port 5554 \
  -no-window -no-audio -no-snapshot -no-boot-anim -gpu swiftshader -accel off \
  > "$LAB/api24-emulator.log" 2>&1 &
timeout 600 "$SDK/platform-tools/adb" -s emulator-5554 wait-for-device
"$SDK/platform-tools/adb" -s emulator-5554 shell getprop sys.boot_completed
"$SDK/platform-tools/adb" -s emulator-5554 shell getprop ro.build.version.sdk
"$SDK/platform-tools/adb" -s emulator-5554 shell getprop ro.product.cpu.abi
"$SDK/platform-tools/adb" -s emulator-5554 shell uname -m
"$SDK/platform-tools/adb" -s emulator-5554 shell getconf PAGE_SIZE
```

Esperar `sys.boot_completed=1` con límite total explícito; timeout no es PASS. Repetir con
el nombre API35, otro puerto y logs nuevos. Si el frontend rechaza ARM64 en ese host o TCG
no arranca, conservar el error y cambiar de host/infraestructura; no sustituirlo por x86-64.
No se probó este comando de boot en Work: está bloqueado por aislamiento y espacio.

Exigir API24/arm64-v8a/aarch64/4096 para A; API35/arm64-v8a/aarch64/16384 para B,
sin native bridge. Para B leer también `bionic.linker.16kb.app_compat.enabled` y
`pm.16kb.app_compat.disabled` y exigir los valores estrictos que valida el runner existente.
Una imagen etiquetada ps16k no sustituye la medición real ni verifica el modo estricto.
Conservar fingerprint, kernel, página real, propiedades y logs, sin cuentas ni datos de usuario.

## Puerta posterior, todavía no autorizada

### Lanzador automatizado de infraestructura (sin aplicación)

Después de materializar/verificar las imágenes fijadas y crear AVD nuevos con las recetas
anteriores, ejecutar **uno por vez**, en VM dedicada sin USB passthrough:

```bash
python3.11 "$REPO/tests/native_compatibility/empty_avd_boot.py" \
  --profile api24-4k --sdk "$SDK" --archives "$LAB/archives" \
  --avd-home "$ANDROID_AVD_HOME" --user-home "$ANDROID_USER_HOME" \
  --output "$LAB/empty-api24-new" --timeout 600
python3.11 "$REPO/tests/native_compatibility/empty_avd_boot.py" \
  --profile arm64-16k --sdk "$SDK" --archives "$LAB/archives" \
  --avd-home "$ANDROID_AVD_HOME" --user-home "$ANDROID_USER_HOME" \
  --output "$LAB/empty-api35-new" --timeout 600
```

El lanzador crea y valida su propio namespace: no pasarlo por un túnel, proxy ni contenedor
con red compartida. No usar el argumento interno `--inside` manualmente. Exige salida nueva,
bytes materializados iguales al ZIP fijado, configuración INI sin rutas de datos externas,
namespace distinto del padre, solo loopback activo y rutas locales antes de boot. Rechaza
AVD ya arrancados; no borra datos ni fuerza perfiles existentes. Usa datos privados nuevos.
`disk.dataPartition.path=<temp>` es el marcador normal admitido; temporales se confinan
a la salida privada. Cámaras/audio y mDNS de ADB quedan desactivados.

Guardar `preflight.json`, `namespace.log`, `emulator.log` y `empty-boot.json` cuando existan.
Un bloqueo inicial no genera logs de procesos que nunca se crearon. El único éxito posible
es `EMPTY_ANDROID_BOOT_VERIFIED_NO_APP_TEST`, que **no** acredita pruebas de FlexyGram.
Si falla TCG/frontend, conservar el mensaje exacto en emulator.log y revisar otro host;
no repetir indefinidamente ni sustituir ARM64. Si falta margen/islamiento, no hay boot.

### Firma e instalación siguen fuera de esta autorización

Antes de instalar: revisión del candidato29188186…, custodia recuperable de clave exclusiva
Diagnostic, autorización independiente de generación/firma/instalación, certificado medido,
post-sign gate v2 y runner firmado/contrato v2 revisados. El borrador privado actual tiene
esos campos nulos/falsos y no es ejecutable. No copiarlo sobre el contrato v1.

Después se reutilizará el runner actual para los12 casos en ambos perfiles: arranque,
NativeLoader/JNI, Chaquopy, cuatro ELF, XML/XSLT/EXSLT/lxml/Pillow, permisos, restauración
sintética, errores y contadores de tráfico por UID. Rechazar pruebas omitidas o datos faltantes.
No se incluyen comandos de firma o instalación en este procedimiento. No habilita beta,
Production, Telegram, Firebase, traducción remota, plugins ni distribución.
