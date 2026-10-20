# Validación ejecutada en esta misión

2026-10-20. CPython3.11.17, Temurin JDK21.0.12.1+1, host Linux x86_64.
Python stdlib, sin nuevas dependencias. Base inicial19200e843cc9bf31c27a99e7b6775494627b131e;
base publicada actualizándose a b637c290c4514f158196ae7e5db3ba7daf7ed4c2
(documentación concurrente; NotificationCenter intacto entre ambas).

| Suite nueva | Casos distintos |
|---|---:|
| Logcat/frames/eventos/comparación | 53 |
| Captura con subprocess dobles | 22 |
| CLI Python con fixtures locales | 9 |
| Método real Java original/corregido | 1 |
| Total | **85** |

**85/85 PASS normal y85/85 PASS con `-O`**, cero fallos, errores, skips,
expected failures o unexpected successes. No sumar las repeticiones ni los dos
compilados del harness como pruebas distintas. Las367 anteriores no se
repitieron ni se agregan como nuevas ejecuciones de esta misión.

```sh
JAVA_HOME=/workspace/scratch/1f84b79e43f3/jdk21 \
  ../python311/bin/python -B tests/beta_diagnostics/run_gate.py \
  --output ../beta-evidence/gate-normal.json
JAVA_HOME=/workspace/scratch/1f84b79e43f3/jdk21 \
  ../python311/bin/python -B -O tests/beta_diagnostics/run_gate.py \
  --output ../beta-evidence/gate-optimized.json
```

Los JSON en evidence/ incluyen IDs, conteos, modo, límites y hashes de fuentes
Python/NotificationCenter antes y después; los logs conservan cada resultado.
Los scripts de ejemplos también se ejecutaron: análisis de JSONL sintético y
plan con una ruta ADB inexistente. El último devolvió PLAN_ONLY sin dispositivos.
Ejemplos/resultados son explícitamente synthetic, sin datos Android reales.

Defectos corregidos durante implementación: el callback Java no ejecutado,
el uso inicial incompatible de Path.open(opener=...) en el nuevo collector y
la posibilidad de sesgo de supervivientes al comparar sólo los requests que
terminaban. Las regresiones finales prueban escritura privada, pérdida de eventos,
timeouts, falta de muestras, errores argparse sin secretos y controles offline.
Se conservaron además dos negativos que fallaban al clasificar texto citado como crash/ANR: 53 casos de analizadores,51 PASS y2 fallos antes de restringir tags/estructura. Tras corregirlo, los85 del gate pasan. No se presenta un error de desarrollo del collector/analizador como fallo heredado de la app.

Límites: **0 pruebas Android,0 capturas ADB,0 mediciones reales de rendimiento**.
JDK prueba un cuerpo de método con dobles, no la compilación Android completa.
No se arrancó, instaló, firmó o distribuyó APK. No se repitieron intentos de
namespace bloqueados ni se reconstruyeron ELF/wheels/APK. La corrección runtime
no está en la APK privada anterior. No se alteraron hashes/contratos congelados.

Work2 puede usar los analizadores inmediatamente sobre capturas privadas o
fixtures, revisar el commit Java separado y preparar un productor del contrato
nuevo de eventos. Aún requiere laboratorio autorizado y una compilación futura
revisada para verificar la corrección Java y medir chats, frames, cambios de tema,
JNI/Python y posible ANR. Ningún resultado aquí demuestra mejora de fluidez.
