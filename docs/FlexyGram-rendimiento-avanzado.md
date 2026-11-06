# Rendimiento avanzado de FlexyGram

## Cambios activos en el código normal

- **Blur:** cada `DownscaledRenderNode` graba su pase primario una sola vez por actualización. Antes lo grababa dos veces con el mismo contenido. Conserva los pases secundarios, matrices, calidad y recortes existentes. Los tamaños vacíos no generan divisiones inválidas; los buffers reducidos mantienen al menos un píxel por eje.
- **Geometría GPU:** `BlurredBackgroundSourceRenderNode.setSize` evita repetir la llamada nativa cuando el tamaño no cambió.
- **Texto:** `TextLayoutPrecompute` prepara métricas de párrafo en un trabajador de baja prioridad. Solo interviene en solicitudes del hilo principal con texto de 160–8192 caracteres sin spans. Una ausencia de caché devuelve inmediatamente el texto original; no espera un Future ni invalida una pantalla al terminar. Los trabajos que ya llegan desde un hilo de fondo conservan su ruta existente.
- **Memoria:** la caché de texto admite hasta 32 entradas y 32768 caracteres, con un solo trabajador y dos trabajos en cola. Copia el `TextPaint` y usa los parámetros nativos de métricas como clave, para distinguir cambios de fuente, tamaño, idioma y demás propiedades métricas. Las señales de memoria borran caché/cola e invalidan publicaciones anteriores. No almacena mensajes en disco ni retiene vistas o cuentas.
- Emojis, spoilers, código, enlaces con spans y spans personalizados conservan el layout nativo. El fallback con estrategia de salto de línea SIMPLE usa el texto original, sin métricas HIGH_QUALITY incompatibles. No cambia la geometría de burbujas, horas ni ticks.

La reducción de grabaciones es una comprobación de trabajo ejecutado, no una medición de FPS. La caché también debe compararse en dispositivo para confirmar el balance entre CPU, memoria y relecturas.

## Diagnóstico interno opcional

Se activa únicamente con `-PflexyPerformanceBuild=true -PflexyFrameDiagnostics=true`. No añade una pestaña ni se inicia en una beta normal.

`FrameDiagnostics` conecta JankStats a la ventana principal mientras la actividad está reanudada. Guarda contadores de duración **UI** y jank heurístico en categorías fijas: inicio/lista, chat, scroll, ajustes y otros. No registra títulos, usuarios, mensajes, identificadores ni un log por frame. Al pausar, resume los contadores localmente y desactiva el seguimiento. Los identificadores de transición evitan que una animación anterior cierre la traza de otra.

Las trazas `Flexy.chat.open` y `Flexy.chat.close` usan los callbacks existentes. No añaden animadores, requestLayout ni un bucle de Choreographer. Los contadores de JankStats no equivalen a FPS, latencia táctil ni tiempo GPU; para esos análisis deben usarse FrameTimeline y las trazas.

- **ProfilingManager:** en Android 15 admite una captura solicitada con `-PflexySystemTrace=true`; en Android 16 se registran disparadores ANR y en API37, OOM. Las solicitudes respetan las cuotas del sistema. La captura manual se cancela al pausar. Los resultados permanecen en el almacenamiento privado del sistema/app; no hay subida, FileProvider público ni publicación de trazas.
- Registro y cierre de servicios se agrupan en un trabajador separado; no bloquean el hilo principal ni la cola global de mensajería.
- El permiso REQUEST_PROFILING y `profileable shell=true` están en un overlay utilizado solo por debug/connectedAlpha con el modo de rendimiento. No se añaden al manifiesto normal de Beta.
- **MemoryBudgetManager:** el adaptador comprueba la presencia de la API pública 37.2 y escucha sus eventos cuando está disponible. No declara límites de memoria inventados ni accede a APIs ocultas. Los eventos liberan cachés mediante el callback existente, con limitación de frecuencia y cierre del listener. En sistemas anteriores siguen funcionando los callbacks normales. Esta API no contabiliza buffers gráficos.

Para generar perfiles o medir benchmarks, dejar `flexyFrameDiagnostics` y `flexySystemTrace` apagados: sus capturas y callbacks alterarían el experimento.

## Baseline Profiles, Startup Profiles y benchmarks

El módulo independiente `:performance` se incluye solamente con `-PflexyPerformanceTools=true`. Usa AndroidX Benchmark 1.5.0 y UIAutomator 2.4.0, y apunta al paquete Alpha existente `io.github.jose22yt.flexygram.alpha`. No modifica la identidad Beta ni sus claves. Requiere un dispositivo API33+ con una cuenta y conversaciones sintéticas previamente preparadas; no inicia sesión, envía mensajes, limpia datos ni cambia la frecuencia de pantalla.

`ProfileGeneration` registra reglas reales de ART para inicio, chat/scroll/entrada y ajustes. La prueba de inicio marca sus reglas como Startup Profile. `DeviceBenchmarks` repite veinte veces los recorridos y obtiene tiempos de inicio y FrameTimingMetric; no convierte la duración de un gesto en FPS o TTFD. El recorrido de entrada enfoca el editor y solicita el teclado, no mide por sí solo toda la latencia del IME. La etiqueta del chat y las de navegación se suministran como argumentos de prueba. Un fixture ausente falla o se omite explícitamente; no se sustituye por medir la pantalla de login.

**No se han generado perfiles de dispositivo ni datos de velocidad en esta sesión.** El proyecto no incluye listas de métodos inventadas.

En la siguiente ejecución de dispositivo, con la configuración privada de Alpha ya disponible:

```bash
NATIVE_TARGET=arm64-v8a ./gradlew \
  -PflexyPerformanceTools=true -PflexyPerformanceBuild=true \
  -Pandroid.testInstrumentationRunnerArguments.class=com.flexygram.performance.ProfileGeneration \
  -Pandroid.testInstrumentationRunnerArguments.flexy.fixtureChat='Chat sintético de pruebas' \
  -Pandroid.testInstrumentationRunnerArguments.flexy.menuDescription='Descripción localizada del menú' \
  -Pandroid.testInstrumentationRunnerArguments.flexy.settingsLabel='Ajustes' \
  :performance:connectedConnectedAlphaAndroidTest
```

Este comando **no se ejecutó**: requiere construir e instalar artefactos de prueba. No incluye credenciales en la línea de comandos.

Tras recoger las salidas de AndroidX y el XML JUnit:

```bash
python tools/performance_profiles/import_profiles.py \
  --baseline <perfiles-baseline-del-dispositivo> \
  --startup <perfil-startup-del-dispositivo> \
  --junit-results <resultado-junit.xml> \
  --source-commit <hash-completo-del-código-construido> \
  --version-code <version-real-alpha> --api-level <api-del-dispositivo>
```

El importador exige éxito de los tres recorridos, valida reglas ART y conserva el orden de captura, importante para DEX. Solo entonces escribe en `TMessagesProj/src/main/generated/baselineProfiles`. AGP consume esos perfiles; ProfileInstaller se añade cuando hay un perfil o al preparar una build de rendimiento. Antes de importar, registrar un commit reproducible del candidato construido. No generar las reglas de fuente desde la variante R8 experimental minificada.

Los benchmarks se ejecutan por separado con la clase `DeviceBenchmarks`. `flexy.compilation=none` y `flexy.compilation=baseline` comparan ART sin/con el perfil en una misma APK. El segundo modo exige un perfil presente. Para aislar Startup Profiles se necesitan artefactos con/sin ese layout DEX, manteniendo iguales el resto de las condiciones. Repetir condiciones de caché, fixture, red, temperatura y refresco, sin forzar 120 Hz. Reportar medianas, p95/p99 y datos no clasificados; la generación de un perfil no demuestra una mejora.

## R8 con compatibilidad controlada

`-PflexyPerformanceBuild=true -PflexyR8Optimization=true` prepara un experimento de optimización exclusivamente para `connectedAlpha`. Genera una copia de las reglas eliminando solo `-dontoptimize`; conserva `-dontobfuscate` y todas las reglas existentes de JNI, reflexión y plugins. No cambia la Beta ni elimina sus protecciones de compatibilidad. La tarea de minificación depende de la preparación de esas reglas.

Antes de activar R8 en distribución, ejecutar la regresión real de plugins, clases accesibles por nombre, hooks, JNI, multimedia, importación y rollback. Compilar las reglas no demuestra esa compatibilidad. La habilitación normal queda pendiente de esa prueba con una build real.

## Verificaciones sin APK

```bash
python -m pytest -q tests/test_advanced_performance.py tests/test_render_work_reuse.py
python tools/performance_profiles/check_android_apis.py --sdk <sdk> --libraries <jars-extraídos>
```

El comprobador de API usa Android API37 y clases reales de AndroidX; únicamente duplica BuildConfig y el callback de aplicación. Los jars esperados son `metrics`, `kotlin`, `annotation`, `junit`, `macro`, `benchmark`, `benchmarkcommon`, `testmonitor` y `uiautomator`. Son las clases extraídas de los artefactos publicados, no clases fabricadas para simular sus APIs. La suite se omite explícitamente si esos inputs no están disponibles.

Se comprobó también la configuración mediante `gradlew help` con el módulo opcional habilitado y se ejecutó `:TMessagesProj:prepareFlexyOptimizedRules`, sin ensamblar Android. La salida conserva exactamente las reglas originales salvo la única línea `-dontoptimize`. Las ocho pruebas específicas pasaron y todos los Java modificados superaron el análisis de sintaxis. Las verificaciones JVM y de tipos no sustituyen aceptación visual, energía, memoria nativa/GPU ni fluidez a 60/90/120 Hz. No se ha compilado una APK ni se han publicado cambios durante esta sesión.
