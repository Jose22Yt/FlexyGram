# Inicio, conectividad y scroll — candidato P0

Base: PR #131, `feat/official-identity-beta-preparation`, `0030904ae2e41d7720f43b7906c6a302ed339839`, descendiente exacto del PR #130 / Alpha 1286. Rama de misión: `perf/startup-connectivity-scroll-p0`. El PR se apila sobre #131 para mostrar solo la optimización; no fusiona ni acepta #130/#131. Paquete, certificado oficial, Gradle, recursos, firma Alpha y JNI permanecen intactos.

## Diagnóstico y código

| Área | Trabajo encontrado | Cambio comprobable |
| --- | --- | --- |
| Inicio | El bucle solicita controladores de las 10 ranuras, incluso vacías, y vuelve a llamar loadConfig para cuenta cero | Configura todas las ranuras en el mismo orden; mantiene controladores para cero, seleccionada/login y sesiones activas. Las demás siguen lazy. Contactos cero mantiene reconciliación global; todas las cuentas activas conservan servicios y mensajes pendientes |
| Caché local | La base ya encola SQLite para la cuenta seleccionada antes de servicios secundarios | Gate y loadDialogs nativos byte-idénticos; no se añade caché paralela, espera a Internet ni estado de conexión simulado |
| Conectividad | Broadcast llama checkConnection, que enumera interfaces, desde UI; eventos pendientes repetidos duplican ese trabajo | Solo ese punto de entrada se deriva a stageQueue y coalesce una tarea por cuenta. Un evento durante ejecución programa una nueva comprobación, sin temporizador ni backoff nuevo |
| Red cacheada | Cada consumidor actualiza lastNetworkCheck, pudiendo aplazar indefinidamente la consulta real con lecturas frecuentes; onLost no invalida | Marca monotónica de la consulta efectiva, no de la lectura. Invalida snapshot/tipo al disponer/cambiar/perder red y hace visibles campos compartidos |
| Lista principal | Las barras de previews de voz repiten conversiones dp en cada dibujo | Cache de siete alturas, ancho, paso e inset por densidad, con las mismas operaciones de redondeo y geometría. No cambia textos, avatares, adaptador, reciclado ni indicadores |
| Navegación | La lente reconstruye su Path aunque sus seis parámetros sean idénticos | Reutiliza Path para geometría idéntica; cualquier parámetro distinto lo reconstruye. Política óptica se actualiza incluso con cache hit |
| Conversación | Cada muestra de borde parcial recalcula centro y dimensiones de la misma RectF | Normaliza límites una vez por reconstrucción, conservando divisiones/decisiones idénticas y shaders originales |
| Interacción | reset invalida celda y padre incluso estando en reposo | Reset en reposo es no-op; si existe presión, spring o escala distinta, conserva cancelación y recuperación originales |
| Frecuencia | Lectura de refresh rate ligada a configuración de pantalla; scroll no expresa voto propio ARR | Monitor de frecuencia real registrado solo entre resume/pause y retirado también en destroy. Lista solicita categoría HIGH en drag/fling (API35+), restaura la preferencia al terminar/detach y respeta otra solicitud posterior |

No se modifica MTProto, cifrado, sesiones, reintentos, timeouts ni el estado visible de conexión. checkConnection/getIpStrategy/getConnectionState siguen idénticos. No se aplaza inicialización de plugins ni recuperación transaccional de Studio: existen dependencias de hooks/ajustes y su trabajo pesado ya se deriva al worker. No se reinstala ningún motor retirado ni se eliminan animaciones, blur, colas, bordes, multimedia o funciones Signature presentes en la base.

El voto HIGH es una sugerencia oficial y no garantiza una frecuencia ni FPS. No fija preferredDisplayModeId, no desactiva ARR, no altera ahorro/temperatura ni añade render loop o ajustes FPS. Android decide la frecuencia real. La actualización del presupuesto usa el refresco observado, incluidos modos fraccionarios; no presupone 60 o 120 Hz.

## Evidencia disponible

`device-baseline.json` registra antes/después físicos como **NOT_MEASURED**. No hay dispositivo/ADB disponible en esta sesión. No se ha compilado una APK de esta misión, no se dispone de medidas de TTID/TTFD, latencia de conexión, jank, energía, memoria o toque-a-visible. No se afirma 120 FPS ni superioridad sobre Exteraless.

`operation-results.json` contiene conteos deterministas de código base y candidato ejecutados con dobles aislados, no métricas del POCO:

| Fixture aislada | Antes | Después |
| --- | ---: | ---: |
| Llamadas del bucle a controladores, una sesión en cuenta cero | 10 | 1 |
| Reconstrucciones de lente en 1000 preparaciones iguales | 1000 | 1 |
| Lecturas de límites para 400 bordes parciales sintéticos | 259328 | 1600 |
| Invalidaciones de celda en 1000 resets en reposo | 1000 | 0 |
| Conversiones dp de siete barras en 1000 dibujos a densidad constante | 22000 | 10 |

Estos conteos no equivalen a ahorros de milisegundos, memoria, energía o instancias totales: otras rutas nativas pueden inicializar controladores. Los 308755 asserts recorren matrices/iteraciones, no son 308755 casos de prueba independientes. Los bucles reales extraídos de ApplicationLoader se ejecutaron antes/después en 10240 combinaciones de cuenta seleccionada y sesiones activas, con dobles de configuración/servicios. Todas las cuentas cargan su configuración, se mantienen usuarios y unsent work de cuentas activas y el cache load seleccionado. Las consultas de caché con intervalos de 100 ms ya no impiden caducidad. Geometría y muestras de spring se comparan exactamente con la fuente base para 60/90/120/144 Hz sintéticos. No es una prueba de GPU, SQLite o sesiones reales.

Los helpers, lente, borde y spring compilan también contra `android.jar` original API37, con únicamente dos dependencias internas mínimas simuladas. Es comprobación de APIs, no compilación de aplicación, DEX, recursos ni APK. La capa de auditoría nueva restaura exactamente los bytes previos para contratos históricos y rechaza modificaciones desconocidas; sus manifiestos anteriores permanecen intactos.

## Reproducir sin Android instalado

```bash
python3 tools/performance_p0/run_checks.py
python3 tools/performance_p0/check_wiring.py
python3 -m unittest discover -s tools/performance_p0 -p test_capture_gate.py -v
python3 tools/identity/check_identity.py
```

Con SDK disponible, añadir `--android-jar /ruta/al/sdk/platforms/android-37.0/android.jar` al primer comando. Requiere JDK con módulo jdk.compiler. No ejecuta Gradle ni construye Android. Las salidas van a build/performance-p0 y no contienen cuentas, mensajes, tokens, sesiones o claves.

## Validación física pendiente

Usar exclusivamente identidad Alpha existente y una entrega privada autorizada. No solicitar el PKCS12 Beta. Medir primero el Alpha 1286 existente con procedencia `258dd359…` o una baseline Alpha de `0030904a…`; instalar después el candidato con la misma identidad de pruebas, sin limpiar sesiones. No se ha ejecutado ese flujo durante esta misión. El primer lanzamiento que crea bases puede diferir de uno con datos existentes: separar ambas condiciones.

1. Capturar al menos 20 repeticiones por condición: inicio frío, proceso existente con recreación de actividad, regreso desde segundo plano. Registrar TTID/primera superficie por Android/Perfetto y el instante de lista útil por observación/eventos de prueba explícitos. No llamar TTFD a `am start -W` ni inventar reportFullyDrawn.
2. Preparar listas de 20/1000 diálogos y chats de texto/multimedia de prueba; scroll lento, fling, inversiones, frenado con dedo, tap durante fling, abrir/Back/multitap, previews interrumpidas, cambio de carpetas/tema, recepción durante scroll, blur frío/caliente/off y wallpapers nativos/personalizados. Verificar el mismo aspecto y estado reciclado mediante comparación física.
3. Repetir Wi-Fi, datos, handover, offline, red lenta, reconexión, background, varias cuentas y login de ranura vacía. Separar tiempo de sincronización externo de respuesta de UI. Registrar si stageQueue ocupada retrasa el check; no afirmar menor RTT por el cambio de hilo.
4. Observar 60/90/120 y demás modos disponibles, energía/temperatura/ahorro, memoria y GC. Mantener fixture, tema, caché, red, modo de build, batería y orden ABBA equivalentes; no forzar frecuencia global, destruir datos ni mantener conexiones artificialmente activas.
5. Reutilizar `python3 -m tools.connected_alpha.performance.capture --help` para capturas locales de gfxinfo/estado y `python3 -m tools.connected_alpha.performance.perfetto --help` para plan acotado FrameTimeline, scheduling/GC y secciones startup existentes. Operar solo cuentas sintéticas autorizadas; guardar trazas sin publicar datos privados. FrameTimeline distingue jank de app/SF; ni gfxinfo ni una tasa de refresco son por sí mismos latencia táctil o FPS renderizados.
6. Comparar archivos mediante `python3 tools/performance_p0/compare_pair.py before.json after.json --out comparison.json`. Exige procedencia base conocida, Alpha, 20 repeticiones, condiciones iguales y distribución de refresh observada comparable. Rechaza los conteos aislados como evidencia de teléfono. No declara automáticamente superioridad. Analizar p50/p95/p99, colas, CPU/GPU cuando disponibles, memoria y energía; corregir regresiones antes de aceptar.

La suite histórica completa requiere el checkout/submódulos/objetos y laboratorio apropiados. Los datos de conexiones, permisos, push, llamadas, multimedia, persistencia y perfiles térmicos todavía necesitan regresión física. No se da por cerrado P0 físico ni se promociona a Beta.

## Referencias primarias

- https://developer.android.com/develop/ui/views/animations/adaptive-refresh-rate
- https://developer.android.com/reference/android/view/View#setRequestedFrameRate(float)
- https://developer.android.com/media/optimize/performance/frame-rate
- https://developer.android.com/topic/performance/issues/launch-time
- https://perfetto.dev/docs/data-sources/frametimeline

## Resultado de regresión en esta sesión

`verification.json` diferencia resultados: 8/8 métodos de Interaction1286, 144 pytest generales aprobadas y 31 omitidas por corpus externo/informe R8; gate de comparación, identidad y wiring aprobados. En la suite histórica test_startup pasan 4 métodos y 1 produce errores en dos subcasos (TMessagesProj/build.gradle y .github/workflows/pr.yml, byte-idénticos a la base). Inicialmente faltaba además el blob SQLite histórico; se recuperó desde GitHub y verificó por su SHA Git, tras lo cual esa prueba pasó. Las dos proyecciones históricas siguen pendientes; no se declara la suite completa verde ni se cambian sus asserts para silenciarlas. Requiere checkout histórico completo y revisión de esa cadena antes de una entrega. Ningún resultado aislado sustituye la aceptación física.
