# Integración revisada Work 1 y gate offline combinado

Proyecto FlexyGram 1.0, responsable @Lukhou23. Se verificaron por GitHub:
PR17 `c7302da16082a30f39d8ef41886427cbf1edbe6c` y PR22
`0ffcf81bd1aaba2512ff1b0ef09472e612c45d1c`, ambos draft/open/unmerged.

## Integración temporal y cambios

Se calculó `git merge-tree --write-tree` sobre ambos HEAD, sin modificar refs
remotos. Resultado exit0, árbol `7a510644fb2045aeb4502545f1adbfbb2c0c7721`:
sin conflictos textuales. Se materializó ese árbol en una rama local temporal,
con checkout completo y sin iniciar submódulos o reconstrucciones.

Se incorporan el arreglo de salida/puertos de `run_lab.Adb`, el preflight de
SDK/JDK/AVD/almacenamiento/entorno y las 34 regresiones de PR22. Los archivos de
`docs/lab-readiness` conservan su historial de validación anterior: sus cifras
no son ejecuciones nuevas de esta sesión. Este informe y su directorio de
evidencias documentan las ejecuciones nuevas.

La revisión semántica produjo correcciones adicionales:

1. **Inventario de alcance**: la primera corrida dio 317 PASS y 1 fallo porque
   `scope_native.py` rechazaba documentación/herramientas/tests nuevos de PR22.
   Se registraron archivos exactos y hashes en `reviewed_changes.json`.
   No se amplió un prefijo genérico permitido ni se desactivó el verificador.
2. **Partición temporal**: el preflight rechazaba el marcador `<temp>` de las
   recetas, mientras `empty_avd_boot.check_fresh_avd` lo aceptaba. Ahora ambos
   permiten vacío/`<temp>` y rechazan rutas explícitas de datos/cache/SD hasta
   revisión separada, incluso si son privadas. Dos regresiones nuevas.
3. **AVD incoherente con launcher**: el preflight podía aceptar AVD ya arrancado,
   alias de directorio o symlink interno de config que el launcher rechazaba.
   Se comprueban nombre de directorio, symlinks y señales de datos/snapshots
   previos; tres regresiones nuevas cubren estos rechazos.
4. **Gate combinado**: `tools/lab_readiness/run_combined_gate.py` ejecuta el
   `run_gate.py` nativo original y la suite externa por separado. Comprueba
   mínimos, exit status, todos los contadores, inventarios de IDs sin duplicados
   y hashes de fuentes antes/después. Diez regresiones sintéticas comprueban
   rechazo de skips, xfail, falta de inventario/contadores, conteos booleanos,
   descubrimiento parcial y PASS falsificado. No altera los gates anteriores.

`empty_avd_boot.py` sigue usando los mismos objetos reales `Adb/preflight` de
`run_lab.py`. Sus 14 regresiones están dentro de las 318: no se suman otra vez.
No se modifican contratos históricos, Gradle, manifiestos, policies Java/JNI,
Production, autenticación ni código de interfaz, animación o rendimiento.

La publicación se prepara como commit con **un solo padre PR17**, incorporando
los cambios revisados sin convertir el HEAD de PR22 en ancestro. Esto mantiene
PR22 abierto/en borrador para revisión en vez de marcarlo fusionado por
ascendencia. No se fusiona ningún PR a develop/main.

## Resultados nuevos, sin dobles conteos

| Momento | Normal Python 3.11 | Python 3.11 `-O` |
|---|---|---|
| Primer intento temporal | 318 ejecutadas, 317 PASS, 1 fallo de inventario | No aplicable |
| Base revisada PR17 + PR22 tras inventario | 318 nativas + 34 readiness = **352 PASS** | **352 PASS** |
| Cierre con regresiones nuevas | 318 nativas + 49 readiness = **367 PASS** | **367 PASS** |

En las ejecuciones finales: 0 fallos, 0 errores, 0 skips, 0 expected failures,
0 unexpected successes, 367 IDs distintos por modo. Las 15 adicionales son
10 del gate, 2 de partición y 3 de frescura/coherencia AVD. Las repeticiones y
los intentos previos no se suman: **367 pruebas distintas, no 734**.
Los hashes de fuentes Python coinciden al inicio/final de cada gate.

Entorno: CPython3.11.17, pyelftools0.33 y Temurin JDK21.0.12.1+1 preparado fuera
del checkout. Se recuperaron fuentes exactas PR20/21 con hashes fijados por el
adaptador; no se actualizaron ni repinaron. No hubo SKIP ni dependencia de cuentas
reales. La única compilación es el pequeño harness Java ya existente en una
regresión histórica; no es una compilación Android.

## Reproducir sin tocar dispositivos

Preparar Python3.11, pyelftools0.33, JDK21 y fuentes PR20/21 verificadas fuera
del checkout. Las pruebas no las descargan automáticamente.

```sh
export JAVA_HOME=/ruta/privada/jdk21
export FLEXYGRAM_TEST_PR20=/ruta/privada/pinned-aux/pr20.py
export FLEXYGRAM_TEST_PR21=/ruta/privada/pinned-aux/pr21.py
python3.11 -B tools/lab_readiness/run_combined_gate.py --output /ruta/privada/evidencia-normal-nueva
python3.11 -B -O tools/lab_readiness/run_combined_gate.py --output /ruta/privada/evidencia-optimized-nueva
```

El output debe ser un directorio nuevo fuera del checkout. Se preservan los
logs de cada suite, sus informes, IDs y hashes de fuentes en combined.json.
Los subprocesos reciben el mismo modo `-O` que el proceso padre. Continúa siendo
posible ejecutar por separado el gate nativo y `unittest discover` readiness.
Para esta sesión se usaron rutas bajo `/workspace/scratch/1f84b79e43f3/` y ambos
comandos finalizaron exit0. Los JSON y logs completos se conservan en
[evidence-work1-integration](evidence-work1-integration/), con índice SHA-256.

## Laboratorio: alternativas comprobadas de nuevo

Host x86_64, página host4096. Espacio libre observado **26458017792 bytes**;
la comprobación real por volumen pasa el presupuesto conjunto SDK/AVD de12GiB.
JDK21 PASS. No hay SDK/imágenes/AVD, ADB, Emulator o QEMU ARM64 preparados aquí.
Se crearon solamente directorios vacíos privados; no se descargaron imágenes.
El suplemento real, con entorno de proxies limpiado sólo para ese subproceso,
registra PREBOOT_BLOCKED por metadatos/herramientas/imágenes ausentes.

| Alternativa real | Resultado nuevo |
|---|---|
| `unshare --user --map-root-user --net true` | exit1, `/proc/self/uid_map: Operation not permitted` |
| `unshare --net true` | exit1, `Operation not permitted` |
| `unshare --user --net true` | exit0; crear un namespace sin configurarlo no acredita el laboratorio |
| `unshare --user --net ip link set lo up` | exit1, `Cannot open netlink socket: Operation not permitted` |
| Bubblewrap user/net, montaje raíz sólo lectura y true | TimeoutExpired a15s, sin acreditar aislamiento operativo |

No hay KVM, TUN ni USB detectados; Docker/Podman tampoco están disponibles.
Falta KVM no demuestra por sí solo imposibilidad de TCG ARM64, pero descargar
varios GiB no resuelve el bloqueo demostrado de aislamiento/loopback. No se
relajó el launcher para utilizar la red del host. **0 arranques Android** y
0 instalaciones de aplicaciones; no se presentan los fixtures como guest real.

## APK y siguiente puerta

No se recuperó, recompiló, firmó, instaló o distribuyó la APK en esta sesión.
La referencia privada continúa siendo
`291881863ea81418fa6cb12104b6eaea4aee2403822894da2143a51f3030bdd5`;
este trabajo no constituye una nueva comprobación física de esos bytes.
Tampoco se reconstruyeron los cuatro ELF ni los wheels.

El siguiente paso bloqueante es proporcionar host/VM Linux de laboratorio sin
USB passthrough, con namespace nuevo configurable y aislamiento verificable,
herramientas/imágenes revisadas y margen de almacenamiento posterior a extracción.
Ejecutar el suplemento y gate de imágenes existentes antes de `empty_avd_boot.py`.
Primero **API24 ARM64/4KB vacío** y **API35 ARM64/16KB estricto vacío**; registrar
API/ABI/PAGE_SIZE reales, native bridge y compatibilidad16KB desactivada.
El procedimiento externo de LAB-V2-EXTERNAL-PROCEDURE sigue aplicando.

Después, con custodia recuperable y autorizaciones independientes de firma e
instalación, adaptar/activar v2 sin repuntar v1 y ejecutar los 12 casos por perfil.
Diagnostic offline no es la futura beta autenticable. Identidad/credenciales
propias, transporte, push/backup/actualización y servicios autorizados requieren
sus revisiones y aprobaciones posteriores. No se habilita ninguna capacidad ni
se afirma rendimiento, fluidez o compatibilidad Android real con estas pruebas.
