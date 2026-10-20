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
