# Cierre de ciclo de vida durante commit local

Código probado: `6d0f97154e4cc151af19744d44fd411d3e2fd33d`. Continuación del PR #35 desde `cb80bf6ffa80c9ec3c82c6bec5c48cd0a4ff9020`; PR #34 comprobado sin cambios en `36e27309bee4e6c27e3850321fa0c6c44e2acf42`.

## Defecto reproducido y corrección

Antes, `AuthenticationController.close()` retornaba durante COMMITTING sin recordar el cierre. Un almacén local que solicitara el cierre reentrantemente podía terminar el commit conservando el relay y su observador. Seis casos host fallaron contra el código anterior (`before-fix.log`), incluidos éxito, conflicto, error antes/después de escribir, resultado nulo y entrega UI pendiente. No son fallos observados en Android.

Ahora un indicador de commit independiente del estado UI protege todo el intervalo de guardado/publicación. El cierre solicitado se recuerda y se ejecuta en finally después de limpiar las copias temporales. El resultado booleano del commit no cambia; el cierre conserva el fault, no borra datos escritos, no reintenta ni revoca sesiones. Los callbacks UI encolados dejan de entregarse al cerrar y se libera el observador. No hay cambios de contratos públicos.

Nueve regresiones nuevas: seis casos anteriores, cierre desde observador COMMITTING, cierre desde observador LOCAL_COMPLETE y cierre desde otro hilo. Se comprueban también liberación de observador, limpieza de arrays, escritura única, ausencia de reintento y conservación de resultado incierto. Los hilos tienen límites de espera y propagan errores al test.

## Ejecuciones reales

| Ejecución | Pruebas | Fallos | Errores | Omitidas |
|---|---:|---:|---:|---:|
| Reproducción anterior al fix, selección CloseDuring | 6 | 6 | 0 | 0 |
| Primer intento completo, checkout incompleto | 108 | 0 | 1 de setUpClass | 0 |
| Final Python 3.11 normal | 110 | 0 | 0 | 0 |
| Final Python 3.11 -O | 110 | 0 | 0 | 0 |

**110 pruebas distintas, 220 ejecuciones finales**. No se suman las ejecuciones preliminares al total final. El error intermedio fue una plantilla original `VariantPolicy.generated.h.in` no materializada en el checkout parcial: se recuperó sin modificar desde la base fijada y se repitió toda la suite. No se relajaron pruebas. Los logs se conservan por separado.

Comandos completos y rutas de herramientas en `commands.json`; versiones en `environment.json`; inventario de métodos, hashes de fuentes y logs en `results.json`. JDK 21 compila código real del módulo con --release 8; se prueban también los parches sobre copias temporales, el resolver API existente y las guardas C++ del host. Gradle solo aporta Groovy: no se ejecuta una compilación APK.

## Límites e integración

El módulo continúa sin registrar ni empaquetar. Este cambio toca exclusivamente su controlador, arnés y evidencias. No se aplicaron los cuatro parches al cliente, no se tocaron archivos compartidos de Work 2 y no hubo conexiones Telegram, credenciales, build Android, firma o instalación. Las políticas siguen cerradas.

Work 2 puede incorporar el commit de código tras revisar el módulo, sin aplicar los parches compartidos automáticamente. Siguen pendientes los adaptadores Android/JNI/almacenamiento, su revisión y pruebas reales de ciclo de vida. El PASS host no demuestra funcionamiento ni persistencia de sesiones Android.
