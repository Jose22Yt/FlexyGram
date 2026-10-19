# P0.4c — ejecutor Android de laboratorio

FlexyGram, creado y dirigido por @Lukhou23. Preparación sobre PR #17,
HEAD revisado `867e1178719ff0bda8d9b5381b17ecc3ae8391e5`.
**Android sigue pendiente. No fusionar, distribuir ni promover el overlay.**

## Alcance y resultado real de esta continuación

Se añade exclusivamente código de pruebas y documentación. No cambia ningún archivo
activo Android, JNI, Gradle, manifiesto de Diagnostic, lock Python, traducción, política,
recurso o icono. Las evidencias anteriores y los doce casos permanecen intactos.

El ejecutor es una APK de instrumentación independiente, sin permisos ni bibliotecas
nativas propias, fuera de settings.gradle y de la APK normal. Se compiló realmente con
JBR21, javac target8, D8 min24, AAPT2 SDK37 y Build Tools36.0.0: **unsigned,
no instalable**. No es otro build de Diagnostic ni una prueba ART/JNI/Android.
El recibo y el manifiesto binario están en `evidence-android-lab/`.

Se reejecutaron las 175 regresiones existentes y se añadieron 32 pruebas sintéticas:
**207/207, cero fallos u omisiones**. Desglose:102 históricas y105 del gate nativo
(73 existentes+32 nuevas). El gate105 se repitió con Python3.11 `-O`; no se cuenta
dos veces. Los 12 casos funcionales preparados **no se ejecutaron en Android** aquí.
La suite auxiliar PR19 se cuenta por separado,15/15 y11/11 señales estáticas.

El inventario real registra host x86_64/página4096, sin adb, emulator,
qemu-system-aarch64, launch_cvd, imágenes de sistema, KVM, TUN, CAP_NET_ADMIN o
CAP_SYS_ADMIN. No se ha instalado ninguna APK ni usado dispositivo o cuenta.
No se repiten builds completos del cliente ni reconstrucciones de ELF/wheels.

**Limitación adicional de conservación:** los binarios experimentales y la clave privada
de firma del entorno previo no están presentes en este espacio recuperado. Se buscaron
los artefactos disponibles sin encontrar esos objetos exactos. Se conservan en Git los
hashes, fuentes, recetas, overlay y evidencias originales; no se afirma conservar físicamente
los binarios ni se sustituye la APK por otra antigua. Si no se recuperan APK,18 wheels y
clave exactos, esta ejecución está bloqueada. Una reconstrucción posterior necesitaría
su propia trazabilidad y aprobación de cualquier nuevo hash/certificado; no se flexibiliza
el contrato automáticamente y no se genera otra clave para fingir continuidad.

## Contrato inmutable de entrada

`tests/native_compatibility/android_lab/contract.json` fija:

- APK experimental SHA256 `17c32ab39e3ac88213241a6bd643637469a4a4d47311a920b357a2e7b3128230`,125488383 bytes.
- Certificado laboratorio `27ef63ae50546c0af28c0ac54ef66a0c00614934cda86c6bea42d9d2759e7b83`.
- Los18 wheels ARM64 del overlay, de ellos3 reconstruidos; inventario exacto, CRC,
  SHA256, cuatro ELF y JNI idénticos a los incluidos en la APK.
- Los cuatro ELF experimentales y su PT_LOAD ARM64/16KB, sin parchear p_align.
- Código de los12 casos SHA256 `cabd6335f2711fd7b189a14ad535429481b611ee9b7be72bc526a87b7a012ad6`.
- Fuente tipográfica Oswald ya presente en el repositorio y licencia OFL, fijadas por
  hash y copiadas únicamente a assets del test. No se añaden fuentes a la aplicación.
  Comprueba renderizado sintético, no cobertura completa de glifos ni todos los formatos.
- Huellas de build.gradle, locks y política activos: cualquier modificación bloquea el runner.

Los96/96 ELF aptos estáticamente para4/16KB siguen siendo **evidencia histórica de
esa APK**, no una nueva lectura de un binario recuperado ni certificación de carga.
Se conservan las tres distribuciones originales activas y sus dependencias sin cambios.

## Componentes del ejecutor

| Archivo en tests/native_compatibility/android_lab | Función |
|---|---|
| AndroidManifest.xml | Instrumentación de `.diagnostic`; paquete `.diagnostic.labtests`; cero permisos/componentes de app |
| build_runner.py | javac/D8/AAPT2/zipalign; firma opcional exclusivamente con la clave de laboratorio revisada |
| contract.json / contract.py | SHA,18 wheels,4 ELF,JNI,ABI,API,página,certificado,caps y12 IDs; rechazos explícitos también bajo -O |
| java/.../LabInstrumentation.java | Preflight dentro del proceso objetivo, arranque Activity, NativeLoader y Chaquopy test-only |
| assets/probe.py | Ejecuta los12 casos originales y verifica las rutas/hash realmente mapeados en /proc/self/maps |
| run_lab.py | Inventario, comprobación de inputs, instalación limpia, aislamiento UID, arranque, instrumentación, logs y matriz |
| offline-receipt.template.json | Atestación manual que comienza denegada; procedencia/hash de imagen e aislamiento del host |

La instrumentación lee las seis capacidades Java antes/después, API ID0/hash vacío,
INTERNET ausente y firma/bytes instalados exactos. Nunca llama ensureStarted del motor
de plugins ni modifica sus guardas. Inicia explícitamente Chaquopy desde el **test**, no
desde el motor deshabilitado. Inspecciona el estado del motor sin crearlo; verifica JNI
cargado y su función pública de atestación de política, sin invocar MTProto.

Importa lxml/Pillow para cargar las dependencias, exige una única ruta mapeada para cada
ELF reconstruido y verifica sus bytes antes/después. No extrae bibliotecas sustitutivas,
no admite native bridge, host Linux o ELF x86 como evidencia ARM64.

Dos detalles cubiertos por regresión: `sys.getandroidapilevel()` es el mínimo de
**compilación de Python**, no la API real del sistema; se usa Build.VERSION.SDK_INT.
En Chaquopy PyObject.get equivale a getattr, no a acceso a un dict: se usa __getitem__
para recuperar run_probe, comprobado con el helper Java real y un doble sintético.

El resultado exige exactamente los12 IDs originales,12 ejecutados y cero fallos,
errores, skips, expectedFailure o unexpectedSuccess; protocolo de instrumentación
único y nonce distinto por entorno. Los reports sintéticos de unittest no son evidencia Android.

## Entornos investigados

Los catálogos oficiales se consultaron realmente y se conservan en `sdk-catalog.json`.
Las imágenes no se descargaron ni arrancaron. La existencia de un paquete en catálogo
no prueba que el motor del host pueda ejecutarlo ni que su página sea la esperada.

| Perfil requerido | Candidato oficial | Estado |
|---|---|---|
| A:ARM64/API24/4096 | system-images;android-24;default;arm64-v8a, r09 | En catálogo AOSP; falta motor ARM64 compatible y boot real |
| B:ARM64/16384 | system-images;android-35;google_apis_ps16k;arm64-v8a, r05; también API36 r07 | En catálogo Google APIs, no Google Play; requiere root y comprobar página/compat |
| B alternativo | Cuttlefish aosp_cf_arm64_phone_pgagnostic y kernel_aarch64_16k_dist | Ruta documentada AOSP; falta host/imagen coherente y ejecución |

Las imágenes `google_apis_ps16k` están en el catálogo **google_apis**, no en una URL
independiente ps16k (esa consulta devolvió404). Procedencias/checksums de catálogo
se registran; se debe calcular además SHA256 del archivo realmente descargado.

**Alternativas por software:** la fuente Cuttlefish fijada más abajo selecciona
qemu-system-aarch64 y contempla ARM cruzado con GICv2/TCG; no exige KVM para toda
combinación. Es una posibilidad técnica, no una prueba realizada ni una receta API24
certificada. Necesita host packages, QEMU, imágenes/kernel ARM64 coherentes y permisos
TUN/red/aislamiento. El contenedor actual no los tiene; no se intentó un build AOSP
masivo ni se descargaron imágenes incapaces de arrancar aquí.

El Emulator SDK moderno x86 tampoco garantiza ARM64 con `-accel off`: el código
emu-35-3 contiene rechazo de ARM64 API>=28 en x86 y condiciona la selección ARM64 a
host aarch64. Para API24 también se debe cualificar un motor que incluya ese backend;
no basta disponer de la imagen. Preferir host laboratorio ARM64 compatible o un motor
ARM64/TCG fijado y arrancado previamente. SwiftShader solo cambia GPU, no la CPU.
Ningún emulador x86_64 ni traducción binaria satisface estos dos perfiles.

## Procedimiento reproducible externo

### 1. Preparación privada, sin APK en proveedores

Usar un host local dedicado/autorizado y dos emuladores desechables. No teléfonos
personales, snapshots con datos, cuentas, Telegram instalado ni proveedores externos.
Descargar SDK/imagen/herramientas oficiales antes del aislamiento y aceptar sus licencias.
Fijar revisión, URL y SHA256 de cada archivo/motor/kernel/imagen; mantener ese inventario
junto al recibo. Los SHA1 de catálogo sirven de comprobación adicional, no sustituyen SHA256.

Herramientas del runner: Python3.11, JBR/JDK21, Android platform37, Build Tools36.0.0,
platform-tools adb reciente. El build standalone no necesita Gradle, NDK ni pip.
Las regresiones previas sí requieren los recursos descritos en evidence-completion:
API24 android.jar, Gradle/Groovy9.7.1, CMake3.31.6, pyelftools0.33, Gson y referencia ABI.
No ejecutar scripts heredados de publicación.

Recuperar privadamente los bytes originales y los18 wheels en un directorio sin enlaces,
y la clave de laboratorio en su almacén privado; nunca incorporarlos al PR. Desde raíz:

```sh
python3.11 tests/native_compatibility/android_lab/run_lab.py inventory
python3.11 tests/native_compatibility/android_lab/run_lab.py verify-inputs \
  --apk /private/artifacts/reviewed-experimental.apk \
  --wheelhouse /private/artifacts/overlay-arm64
```

Cualquier error es bloqueo; no editar hashes para que un artefacto distinto pase.
El último comando se ejecutó aquí contra rutas ausentes: devolvió BLOCKED/exit1
antes de ADB. Eso prueba el rechazo, no valida artefactos que faltan.

### 2. Construir exclusivamente la APK de tests

```sh
export JAVA_HOME=/private/tools/jdk21
python3.11 tests/native_compatibility/android_lab/build_runner.py \
  --android-jar /private/sdk/platforms/android-37/android.jar \
  --build-tools /private/sdk/build-tools/36.0.0 \
  --output /private/results/runner-unsigned
```

Sin clave produce BUILT_UNSIGNED_NOT_INSTALLABLE. Para la ejecución, usar un directorio
nuevo y añadir `--keystore /private/keys/reviewed-lab.jks --alias LAB_ALIAS`; suministrar
FLEXYGRAM_LAB_STORE_PASSWORD y FLEXYGRAM_LAB_KEY_PASSWORD desde un gestor privado,
no argumentos ni archivos versionados. La clave se comprueba por certificado **antes**
de firmar. No generar otra ni usar firma productiva. El recibo fija fuentes/assets y
el runner host vuelve a comprobarlos, la firma y el manifiesto antes de instalar.

### 3. Cualificar y aislar cada emulador antes de instalar

Boot desde imagen nueva y sin snapshots. Registrar comandos completos, revisión del
motor, kernel y hash de imagen. Para SDK Emulator, solo si el motor ARM64 fue cualificado:

```sh
avdmanager create avd --name fglab24 --package 'system-images;android-24;default;arm64-v8a'
avdmanager create avd --name fglab16 --package 'system-images;android-35;google_apis_ps16k;arm64-v8a'
# Dentro del aislamiento del host, un perfil cada vez:
emulator -avd fglab24 -wipe-data -no-snapshot -no-audio -no-boot-anim -port 5554
# Segundo perfil: fglab16; descartar por completo el userdata anterior.
```

Estos comandos preparan AVD, **no garantizan soporte del motor del host**. Si el motor
rechaza ARM64, detener esa ruta; no cambiar a x86. Para Cuttlefish, seguir la receta
AOSP ARM64/16KB citada, `--resume=false` y userdata nuevo. API24 queda separado: una
imagen Cuttlefish moderna no sustituye Android24.

Aislar también el host, no solo activar modo avión. Ejemplo Linux en host dedicado con
permisos, antes de iniciar Emulator y sin crear veth/rutas/LAN:

```sh
sudo ip netns add fglab24
sudo ip -n fglab24 link set lo up
# Ejecutar Emulator y adb/python en ESA misma netns con usuario de laboratorio,
# por ejemplo: sudo ip netns exec fglab24 runuser -u labuser -- <comando>
# No añadir interfaces, forwarding, proxies, DNS externo ni servidor adb remoto.
```

La red loopback permite ADB local; no conectar un USB ni reutilizar un adb server del
host personal. La red interna del emulador puede existir, pero no tiene salida del host;
el runner añade bloqueo UID IPv4/IPv6 antes del primer arranque para detectar intentos.
Cuttlefish puede necesitar su propio aislamiento/TUN: un operador debe verificarlo,
no dar por aplicado este ejemplo. Guardar evidencia de netns/interfaces/rutas/reglas
sin datos personales. El runner exige atestación; **no verifica por sí solo el firewall
exterior al emulador**. No es una sandbox contra un operador que falsifique evidencias.

En el ADB local dentro del namespace, verificar:

```sh
adb -s emulator-5554 shell uname -m
adb -s emulator-5554 shell getprop ro.product.cpu.abi
adb -s emulator-5554 shell getprop ro.build.version.sdk
adb -s emulator-5554 shell getconf PAGE_SIZE
```

A exige aarch64/arm64-v8a/24/4096. B exige aarch64/arm64-v8a/API>=35/**16384**;
ningún native bridge. No inferir página por nombre de imagen. En el emulador16KB
userdebug autorizado, configurar modo estricto y comprobar lecturas efectivas:

```sh
adb -s emulator-5554 root
adb -s emulator-5554 shell setprop bionic.linker.16kb.app_compat.enabled false
adb -s emulator-5554 shell setprop pm.16kb.app_compat.disabled true
adb -s emulator-5554 shell getprop bionic.linker.16kb.app_compat.enabled
adb -s emulator-5554 shell getprop pm.16kb.app_compat.disabled
```

El gate también admite `fatal` para la primera propiedad en versiones que lo soportan.
Si las propiedades no pueden establecerse/verificarse, **bloqueado**, no certificar modo
estricto. No cambiar estos valores en dispositivos personales. Verificar cuentas vacías
sin guardar su contenido; no iniciar servicios Google ni añadir cuentas.

### 4. Ejecutar ambas pruebas

Copiar offline-receipt.template.json a un archivo privado por imagen; completar origen,
revisión y SHA256 real y marcar true solo después de comprobar cada condición. No hay
aceptación implícita. Con el emulador vacío, dentro del mismo namespace aislado:

```sh
python3.11 tests/native_compatibility/android_lab/run_lab.py run \
  --profile api24-4k --serial emulator-5554 \
  --adb /private/sdk/platform-tools/adb \
  --apk /private/artifacts/reviewed-experimental.apk \
  --wheelhouse /private/artifacts/overlay-arm64 \
  --runner-apk /private/results/runner-signed/flexygram-lab-signed.apk \
  --runner-receipt /private/results/runner-signed/build-receipt.json \
  --build-tools /private/sdk/build-tools/36.0.0 \
  --offline-receipt /private/lab/api24-offline.json \
  --output /private/results/api24-4k
```

Repetir con emulador16KB limpio, `--profile arm64-16k`, recibo e output diferentes.
El runner rechaza paquetes objetivo/tests ya instalados, otros clientes Telegram,
cuentas no verificablemente vacías, USB/ADB remoto, ABI/API/página incorrecta, bridge,
inputs sustituidos, runner sin firma y cualquier caso omitido. No desinstala aplicaciones
ni borra sesiones. Usa únicamente datos sintéticos y caché nueva por nonce.

La observación del primer arranque es60s por defecto (30..300 configurable); después,
instrumentación inicia el proceso objetivo y ejecuta Chaquopy separadamente. Se exigen
Activity exitosa, JNI cargado,4 mapeos coincidentes,12 PASS, guardas intactas y cero
paquetes/bytes en ambos contadores UID antes/después. Logcat/crash se inspeccionan
por fallos críticos; ruido crítico del sistema también bloquea para revisión, no se oculta.

Al terminar conserva los DROP por UID, fuerza detención de la app de laboratorio y
guarda resultados/logs. **Descartar el emulador completo**, no volver a conectarlo a
Internet ni usarlo para cuentas. El host operador gestiona su namespace después del descarte.

### 5. Gate conjunto y evidencias

```sh
python3.11 tests/native_compatibility/android_lab/run_lab.py matrix \
  /private/results/api24-4k/result.json /private/results/arm64-16k/result.json
```

Solo devuelve PASS_BOTH_ANDROID_LABS con ambos perfiles distintos, nonces distintos,
12 casos por perfil, logs presentes/coincidentes por SHA y cero intentos IPv4/IPv6.
Conservar build-receipt, contrato/commit del runner, SHA de APK/wheels/ELF, imagen/motor,
API/página reales, firma, permisos, cold-launch, instrumentation, logcat/crash y contadores.
Publicar únicamente evidencias revisadas sin secretos ni datos personales, nunca los APK,
wheels o claves. Los hashes detectan mezcla/alteración accidental; no son firmas de un
laboratorio independiente. Los contadores no prueban ausencia universal de IPC, servicios
delegados o actividad fuera del intervalo. Este gate no certifica restauración ni todo el corpus.

## PR19 y auxiliares

PR19 conserva `103e9e6b1fada37254ce788d0cb2c19e65891c36`, borrador hacia develop.
Se ejecutaron15/15 tests y auditor strict con11/11 señales; merge-tree de solo lectura
contra HEAD revisado PR17, base develop ab063..., no detectó conflictos textuales.
**Recomendación favorable al contenido de auditoría**, sin inferir latencia/FPS.
Antes de integrarlo junto a P0.4c debe actualizarse de forma explícita/revisada el alcance
congelado para sus3 rutas de tools/tests/docs navigation_performance y ejecutar gates
combinados. Sin eso la política de alcance debe rechazar la integración; no ampliar
allowlists globalmente. No se fusionó ni modificó PR19.

PR16 `fe3b8973b44a74fcbba3aedc92a514f3b1462e80` y PR18
`44f9826e2d5d74634a85374962da07b068f39efa` continúan separados, abiertos/borrador;
icono candidato no activado. Main/develop y PR2 permanecen intactos; Actions no se habilita.

## Condiciones pendientes antes de integrar P0.4c

1. Recuperar privadamente APK/wheels exactos y misma clave de laboratorio, o revisar
   por separado una reconstrucción trazable con hashes nuevos. No actualizar contrato a ciegas.
2. Disponer de motores/imágenes ARM64 cualificados para A y B con aislamiento host
   demostrado, root para contadores y modo16KB estricto real.
3. Firmar test APK con certificado correcto; ejecutar de verdad ambos perfiles,12/12
   cada uno, JNI/Chaquopy/4 ELF, permisos/caps y logs/contadores sin fallos; gate matrix PASS.
4. Revisar resultados y bloqueos de restauración sintética/Android y compatibilidad
   ampliada todavía pendientes en los issues/informes existentes. No certificarlos con estos12casos.
5. Revisión/aprobación explícita posterior. No hay autorización de merge de PR17,
   promoción de wheels, beta, Production, servicios remotos ni Paso4.

## Fuentes primarias consultadas

- Catálogos SDK: https://dl.google.com/android/repository/repository2-3.xml,
  https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml,
  https://dl.google.com/android/repository/sys-img/google_apis/sys-img2-3.xml.
- Android Emulator/CPU y GPU: https://developer.android.com/studio/run/emulator-acceleration.
- Emulator fuente emu-35-3: https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-35-3-release/android/emulator/main-emulator.cpp.
- Cuttlefish QEMU/TCG, fuente fijada: https://android.googlesource.com/device/google/cuttlefish/+/8b75d1f30a7611e5fbcd03146889d7e20a174120/host/libs/vm_manager/qemu_manager.cpp.
- Cuttlefish local: https://source.android.com/docs/devices/cuttlefish/get-started.
- Cuttlefish ARM64/16KB: https://source.android.com/docs/core/architecture/16kb-page-size/getting-started-cf-arm64-pgagnostic.
- Compatibilidad16KB: https://developer.android.com/guide/practices/page-sizes.
- Python build API: https://docs.python.org/3.11/library/sys.html#sys.getandroidapilevel.
- Chaquopy PyObject: submódulo fijado d47b4a1e1817b4590b9c56dfd4ee5fcfdd6f0cbd,
  product/runtime/src/main/java/com/chaquo/python/PyObject.java (get=getattr).
