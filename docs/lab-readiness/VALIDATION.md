# Evidencias de preparación paralela

Fecha de ejecución: 2026-10-20 UTC. Base PR17:
`a5459cf85c2c23e452bb09f38dfe0a28745ecda1`.
La suite principal de 304 pruebas sigue a cargo del otro Work: aquí no se
redeclara como ejecutada ni se reutilizan sus resultados.

Entorno: Linux x86_64, CPython 3.11.17 en entorno virtual privado.
Para el único harness Java de la suite existente se preparó Temurin JDK
21.0.12.1+1 desde el endpoint oficial de Adoptium:
`https://api.adoptium.net/v3/binary/latest/21/ga/linux/x64/jdk/hotspot/normal/eclipse`.
Archivo descargado SHA-256:
`ce79869e1307ed8ee1e2baa86a412b1eb5b75d10a01006d788a6f968bcfaee94`.
Ese hash registra los bytes usados; no sustituye una verificación independiente
de firma del distribuidor. Herramientas fuera del checkout, sin modificar
versiones Gradle/Android ni instalar SDK o imágenes. No se generaron claves.

| Ejecución | Resultado real | Registro |
|---|---|---|
| Regresiones nuevas antes del arreglo | 8 métodos, 6 fallos de aserción, 0 omisiones | `evidence/controller-before.log` |
| Suite nueva normal | 34 aprobadas, 0 fallos/errores, 0 omisiones | `evidence/tests-normal.log` |
| Suite nueva `-O` | Las mismas 34 aprobadas, 0 fallos/errores, 0 omisiones | `evidence/tests-optimized.log` |
| Suite histórica del controlador, primer intento | 31 aprobadas, 1 error: `/usr/bin/javac` ausente, 0 omisiones | `evidence/controller-initial-missing-javac.log` |
| Suite histórica con JDK21 | 32 aprobadas, 0 fallos/errores, 0 omisiones | `evidence/controller-jdk21.log` |

Resultado final: **66 pruebas distintas aprobadas**, 0 fallos/errores ni
omisiones en las ejecuciones finales. No sumar reintentos, subtests ni modo
optimizado como pruebas distintas. Las pruebas usan archivos sintéticos,
dobles de subprocess y, en un caso histórico, un harness Java de diccionario;
no son ejecuciones Android.

Comandos ejecutados desde la raíz del checkout (sustituir las rutas de entorno
local por Python/JDK disponibles en el laboratorio):

```sh
../python311/bin/python -B -m unittest discover -s tests/lab_readiness -v
../python311/bin/python -B -O -m unittest discover -s tests/lab_readiness -v
JAVA_HOME=/workspace/scratch/1f84b79e43f3/jdk21 \
  ../python311/bin/python -B -m unittest discover \
  -s tests/native_compatibility -p test_android_lab.py -v
../python311/bin/python -B tools/lab_readiness/preflight.py \
  --sdk ../absent-sdk --avd-home ../absent-avds --java-home ../absent-jdk
```

El último comando es una comprobación CLI negativa real (raíces inexistentes
intencionadas): código 2, `PREBOOT_BLOCKED`, sin creación de rutas. Comprueba
agregación de problemas y salida estructurada; no es un intento de acreditar
un SDK. `missing-roots-preflight.json` conserva el resultado, sin valores de
proxy. `host-inventory.json` es el inventario real de este host: no ADB,
emulador, QEMU ARM64, KVM, TUN ni capacidades NET_ADMIN/SYS_ADMIN detectados.
No se han probado namespaces ni instalado imágenes en esta tarea.

No hay nueva compilación Android ni artefactos APK/ELF/wheel generados o
modificados. No se firmó ni instaló nada; 0 pruebas Android ejecutadas.
El siguiente paso es incorporar por revisión estas mejoras al trabajo principal,
proveer laboratorio ARM64 aislado con herramientas/imágenes revisadas, ejecutar
ambos gates de preparación y obtener autorización de firma/instalación antes
de los 12 casos reales por perfil. Production sigue fuera del alcance.

## Comprobación concurrente posterior a publicación

Al publicar PR #22, el Work principal había avanzado PR #17 a
`c7302da16082a30f39d8ef41886427cbf1edbe6c`. Se recuperaron ambos refs sin
modificarlos. `git merge-tree --write-tree` (cálculo sin actualizar ninguna
rama) produjo `d9b0a21a6c7d1ac475fb331065faa606b76de628`, exit 0:
**sin conflictos textuales** entre ese HEAD y los primeros dos commits de esta
rama. El controlador compartido no cambió en el intervalo a5459cf..c7302da.
Esto no equivale a haber fusionado ramas o ejecutado el gate completo combinado.

El nuevo launcher `empty_avd_boot.py` del HEAD concurrente reutiliza precisamente
`Adb` y `preflight`. Por ese cambio nuevo de consumidor se ejecutaron sus
**14 pruebas sintéticas** contra el controlador corregido de esta rama. Fuentes
launcher/test obtenidas mediante `git show c7302da…:ruta`, en directorio temporal
separado; dependencias Python resueltas desde esta rama. Comando:

```sh
PYTHONPATH=tests/native_compatibility:tests/native_compatibility/android_lab \
  ../python311/bin/python -B -m unittest discover \
  -s ../concurrency-check -p test_empty_avd_boot.py -v
```

Resultado: **14/14 PASS**, 0 fallos/errores/omisiones, registro
`evidence/concurrent-launcher.log`. Ninguna ejecuta Android, ADB o unshare.
Son comprobaciones nuevas de esta sesión sobre ese consumidor, no una
reutilización del resultado publicado por el otro Work.

Conteo final ampliado de esta tarea: **80 pruebas distintas aprobadas** =
34 del suplemento + 32 del controlador histórico + 14 del consumidor concurrente.
El conteo de 66 anterior describe el punto previo a esta comprobación adicional.
Las 34 repeticiones con `-O` y los intentos iniciales no se vuelven a sumar.
No se ejecutaron aquí las 304/318 del gate principal.

La base de esta rama se conserva en a5459cf para no reescribir historia ni
mezclar el trabajo concurrente. PR #22 puede revisarse contra la rama de #17;
volver a comprobar conflictos si esa rama avanza antes de incorporar.

El cierre endurece también los subprocesos de versión: elimina opciones de
precarga/agentes y selección ADB heredadas, bloquea su presencia en el informe
y fija ANDROID_USER_HOME/ANDROID_HOME además de AVD_HOME/SDK_ROOT.
La regresión de entorno utiliza sólo marcadores sintéticos y prueba su ausencia
en los argumentos de entorno entregados a cada doble de subprocess. Tras ese
cambio se repitieron las 34 normales y las mismas 34 con `-O`: PASS/0 omisiones.
`host-jdk21-preflight.json` ejecuta únicamente la sonda real de JDK21 disponible,
con las raíces SDK/AVD ausentes: JDK PASS, preparación global BLOCKED.
