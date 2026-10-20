# Herramientas de estabilidad y rendimiento de la futura beta

FlexyGram 1.0, responsable @Lukhou23. Implementación independiente, inicialmente
basada en PR17 `19200e843cc9bf31c27a99e7b6775494627b131e`, actualizada a
`b637c290c4514f158196ae7e5db3ba7daf7ed4c2` tras verificar que el avance concurrente
sólo añadió documentación. No se actualiza PR17 ni se fusionan ramas.

## Entrega ejecutable

| Archivo | Responsabilidad real |
|---|---|
| `tools/beta_diagnostics/analyze.py` | Analiza Logcat, CSV framestats y eventos JSONL; compara cohortes emparejadas |
| `tools/beta_diagnostics/capture.py` | Plan sin dispositivos por defecto; captura de sólo lectura con autorización y guardas offline |
| `tests/beta_diagnostics/run_gate.py` | Gate propio Python3.11 sin skips, fuentes/IDs y compilación del método Java real con dobles |
| `NotificationCenter.java` | Una línea: reprogramar el método de expiración, conservando referencia para cancelarlo |

Los scripts Python usan sólo stdlib, sin nuevos paquetes Android/Python ni
servicios. JDK21 se necesita para la regresión Java, no para analizar capturas.

```sh
export JAVA_HOME=/ruta/privada/jdk21
python3.11 -B tests/beta_diagnostics/run_gate.py --output /ruta/privada/gate-normal.json
python3.11 -B -O tests/beta_diagnostics/run_gate.py --output /ruta/privada/gate-optimized.json

python3.11 -B tools/beta_diagnostics/analyze.py analyze \
  --metadata docs/beta-diagnostics/examples/metadata.template.json \
  --package io.github.jose22yt.flexygram.diagnostic \
  --events docs/beta-diagnostics/examples/events.synthetic.jsonl

python3.11 -B tools/beta_diagnostics/capture.py \
  --adb /ruta/privada/sdk/platform-tools/adb \
  --serial emulator-5554 --package io.github.jose22yt.flexygram.diagnostic
```

Último comando: **PLAN_ONLY** sin invocar ADB, incluso si no existe el binario.
Los ejemplos contienen observaciones inventadas **sólo para demostrar el
analizador**; `source=synthetic`, APK digest cero y condiciones null. Sus números
no describen FlexyGram ni otra aplicación.

## Semántica de las mediciones

### Estabilidad y privacidad

Logcat soporta `epoch` y `threadtime`. La atribución utiliza PIDs conocidos del
objetivo o identificadores explícitos `ANR in`, `Process:` y tombstone del
paquete exacto, incluyendo subprocesos. No atribuye por una mera subcadena del
nombre. PID reutilizado fuera de su ventana puede atribuir mal: usar ventanas
cortas y los PIDs supervisados de esa ejecución. Los PIDs de procesos ya muertos
pueden suministrarse en el recibo; no se deducen todas sus vidas automáticamente.

Se cuentan **señales**, no incidentes únicos: Java fatal, ANR/input timeout,
señales nativas, carga de `.so`, JNI, Chaquopy/Python y ciertos errores de
animación. Una sola caída puede producir varias líneas/categorías. El contador
Choreographer conserva la cantidad que el propio log comunica, sin convertirla
en FPS. No se infiere un ANR sólo por durar 5 segundos o por un evento incompleto.
No encontrar errores en una captura parcial no prueba estabilidad.

Sin líneas atribuibles: `NO_ATTRIBUTED_DATA` y contadores null. Si se exige una
ventana epoch, las líneas threadtime sin epoch se excluyen. Los informes no
copian mensajes, excepciones, URLs, nombres de ventanas ni textos de chats;
conservan categorías, cantidades y hashes de entradas. Entradas JSON con
credenciales/campos no reconocidos se rechazan. Errores CLI no imprimen el valor
privado causante, ni siquiera en errores de argparse.

### Fotogramas

`gfxinfo PACKAGE framestats`: se localizan columnas por nombre, soportando las
columnas adicionales/trailing comma habituales. Sólo Flags=0, timestamps válidos
y filas completas contribuyen al tiempo `FrameCompleted - IntendedVsync` en ns.
Se excluyen sentinelas, se contabilizan filas inválidas y se deduplican filas
iguales dentro del mismo stream. Se exige seleccionar `--stream` si hay varias
ventanas; no se agregan ventanas distintas como si fueran una animación única.

Se calculan p50/p95/p99 nearest-rank, máximo, cantidad por encima del presupuesto
`1000/refresh_hz` y muestras de más de 700ms. Si existe FrameDeadline válido se
cuentan sus excedencias. La tasa de refresco debe suministrarse medida; no se
asume 60Hz ni la frecuencia máxima anunciada del teléfono.

Esto NO mide la presentación real ni permite deducir FPS o frames efectivamente
perdidos. Esos campos quedan null. El buffer puede cubrir sólo los últimos
fotogramas; no es automáticamente una captura íntegra del escenario. Para
comparar se exige ventana `--frame-window INICIO_NS FIN_NS`, al menos30 muestras
por repetición y ninguna fila inválida. Verificar la cobertura con traza/vídeo
antes de usarla como evidencia del escenario completo.

### Apertura, cierre, pulsaciones y temas

El contrato JSONL de [eventos](OBSERVER-CONTRACT.md) no está conectado todavía
a la app. Debe producirlo instrumentación revisada o un observador equivalente
en las tres aplicaciones. No se estima la apertura de un chat con `am start` ni
con la línea `Displayed` de una Activity.

Se empareja cada ID: request, accepted y presented/cancelled/timeout. Se admiten
interacciones solapadas, sin remapear IDs. Las duraciones de aceptaciones,
presentaciones y cancelaciones quedan separadas; incompletos y timeouts no se
tratan como finalizaciones rápidas. Sin observaciones hay null, nunca 0ms.
`presented` sólo significa el endpoint declarado (p.ej. callback de frame), no
necesariamente el instante de luz visible en pantalla.

Relojes: eventos `android_monotonic_ns` (System.nanoTime/CLOCK_MONOTONIC),
framestats CLOCK_MONOTONIC y Logcat epoch por separado. Nunca restar epoch de
monotonic ni sustituirlo por elapsedRealtimeNanos, que incluye suspensión.

## Comparar FlexyGram, Exteraless y Exteragram justamente

[Protocolo reproducible](PROTOCOL.md). El comparador recibe informes:

```sh
python3.11 -B tools/beta_diagnostics/analyze.py compare \
  --baseline /privado/base-r0.json /privado/base-r1.json /privado/base-r2.json /privado/base-r3.json /privado/base-r4.json \
  --candidate /privado/nuevo-r0.json /privado/nuevo-r1.json /privado/nuevo-r2.json /privado/nuevo-r3.json /privado/nuevo-r4.json
```

Exige al menos5 repeticiones emparejadas, IDs de ejecución distintos, un único
cliente/APK por cohorte y condiciones iguales y conocidas (dispositivo, API,
página, Hz, resolución, build type, escenario, dataset, caché, estado térmico,
carga, ahorro, escalas, navegación, tema, endpoint, protocolo). Eventos perdidos
del observador deben ser0. Las condiciones son declaraciones de procedencia:
el analizador por sí solo no certifica su veracidad.

Por operación, se requieren al menos10 observaciones completas por repetición,
sin timeouts/incompletos ni sesgo de supervivientes. Para interrupciones se
compara request→cancelled; para las demás request→presented. Si falta evidencia
sale `INSUFFICIENT_OBSERVATIONS`, no “mejoró”. Si todos los pares exceden a la
base más del10% y más de5ms se señala un empeoramiento observado consistente.
En frames: umbral >10% y >2ms para p95; >5 puntos porcentuales para over-budget.
Son umbrales de investigación, no SLA, significancia estadística ni causalidad.

Se puede comparar clientes distintos, sin declarar ganador. Mezclar Debug con
Release, endpoints diferentes o condiciones unknown produce INCOMPARABLE.
Con datos sintéticos siempre SYNTHETIC_COMPARISON_ONLY, aunque haya diferencias.

## Captura futura autorizada: sólo lectura

Todavía **no se ejecutó**. Requiere `--execute`, metadatos, recibo y salida nueva
fuera del checkout. La plantilla de recibo tiene todas las autorizaciones false.
No convertirlas en true sin aprobación y comprobación real del laboratorio.

1. El recibo ata paquete/serial, metadatos canónicos SHA-256 y namespace actual.
2. Antes de ADB, inspección `ip -j`: sólo loopback activo, sin gateways/default
   ni interfaces externas. Rechaza USB expuesto. No crea namespaces ni redes.
3. Sólo serial emulator local con rango válido; verifica conexión, propiedad
   QEMU, API>=24, ABI ARM64 y página4KB/16KB contra metadatos observados.
4. `pm path` y `sha256sum` verifican que la APK única instalada corresponde al
   digest declarado. Split APKs se bloquean explícitamente hasta soporte revisado.
   Esto no verifica certificado ni sustituye verificadores previos a instalación.
5. `dumpsys account`: sólo conserva la comprobación de contadores cero, sin volcar
   cuentas. **AccountManager vacío no prueba que no haya sesiones privadas de
   Telegram**: también se exige AVD desechable sin datos y atestación del operador.
6. Captura acotada: pidof, Logcat main/system/crash (últimas5000 líneas, epoch)
   y gfxinfo. Sin reset de buffers, root, input, launch, install ni settings.
7. Sólo report.json (directorio0700, archivo0600), sin logs crudos. Las lecturas
   ADB tienen timeout y límite de salida; fallos no se convierten en métricas.

`metadata_sha256` del recibo se calcula sobre JSON canónico
`json.dumps(metadata,sort_keys=True,separators=(',',':'),allow_nan=False)` UTF-8.
Los límites epoch/ns y stream del recibo deben corresponder al escenario, sin
mezclar relojes. El collector no genera eventos de interacción, no confirma
páginas16KB estrictas ni reemplaza la validación del laboratorio v1/v2.

No se habilitan autenticación, INTERNET, Firebase, plugins, servicios ni
Production. Una futura evaluación autenticada necesitará autorización y revisión
separadas; este collector está limitado al laboratorio sin cuentas/datos reales.

## Evidencias e integración

[Validación](VALIDATION.md) y [hallazgos de código](ARCHITECTURE.md).
La corrección Java es un commit separado para que Work2 pueda revisarla o tomar
las herramientas sin mezclar un cambio runtime. No se repinan hashes ni contratos
históricos. **El cambio Java no está en la APK Diagnostic ya construida** y
requiere revisión, compilación Android e integración futura por Work2.

No se repitieron las367 pruebas ni la investigación de bloqueo del host. El gate
anterior conserva su alcance congelado; estos directorios y el cambio Java no se
introducen en su inventario ni se presentan como nueva certificación P0.4c.
La integración futura debe revisar el alcance en su rama beta, sin alterar las
referencias históricas para hacer pasar estos cambios. PR17/main/develop intactas.

Fuentes primarias consultadas el2026-10-20:
[dumpsys](https://developer.android.com/tools/dumpsys),
[Logcat](https://developer.android.com/tools/logcat),
[CTS framestats](https://android.googlesource.com/platform/cts/+/master/hostsidetests/dumpsys/src/android/dumpsys/cts/GfxInfoDumpsysTest.java),
[renderizado](https://developer.android.com/topic/performance/issues/render),
[trazas](https://developer.android.com/topic/performance/tracing).

Códigos CLI:0 significa que se procesaron los inputs, **no** que la app sea
estable o rápida;2 señala argumentos/inputs inválidos, captura bloqueada o
comparación sin evidencia suficiente. Los errores conservan códigos fijos sin
imprimir el payload ni stderr del dispositivo. Revisar cada status de métrica;
“NO_CONSISTENT_SLOWDOWN_AT_THRESHOLD” no equivale a equivalencia demostrada.
