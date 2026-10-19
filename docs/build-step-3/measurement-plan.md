# Preparación de mediciones posteriores

Proyecto FlexyGram 1.0; responsable @Lukhou23. Este documento no contiene resultados de rendimiento. Aplica la [metodología del Paso 2](../audit-step-2/navigation-performance.md). No se implementaron optimizaciones ni instrumentación funcional.

## Identidad de cada ensayo

Registrar SHA fuente y de submódulos, variante, APK SHA-256 y certificado, ABI, versión exacta Android/HyperOS, `ro.product.model`, API, tamaño de página (`adb shell getconf PAGE_SIZE`), resolución, frecuencia seleccionada y efectiva, navegación del sistema, escalas de animación, plugins activos y configuración visual. Los datos del Poco proporcionados por el usuario aún requieren comprobación física.

Conservar un escenario reproducible con cuenta y conversaciones de prueba: lista de chats, conversación corta y larga, multimedia, grupo/canal/foro y teclado abierto/cerrado. No guardar contenido ni identificadores personales en trazas públicas. Mantener brillo, temperatura, batería, modo de energía y frecuencia comparables; anotar throttling. Separar caché fría/caliente, primer arranque y estado estable. No comparar APK Debug con Release como si solo cambiara una función: Debug es diagnóstico y altera el coste de ejecución.

## Métricas y protocolo propuestos

| Caso | Inicio y fin que deben definirse | Instrumentos posteriores |
| --- | --- | --- |
| Apertura de conversación | ACTION_DOWN frente al primer fotograma visible y al fin de transición; medir ambos límites por separado | Perfetto: Input, Choreographer, FrameTimeline, main/RenderThread, scheduling; Macrobenchmark para repetibilidad |
| Cierre | Entrada de Back/botón o inicio de gesto frente a primer fotograma del listado y fin de transición | Perfetto y grabación con marcas correlacionadas |
| Toques rápidos | Secuencia reproducible con intervalos fijados, registrar entradas aceptadas, descartadas y pantalla final | InputDispatcher y rutas/gates descritos en auditoría; no inferir latencia solo del tiempo total de animación |
| Transiciones interrumpidas | Back y nueva apertura en instantes definidos de la transición | Trazas de entrada/animadores y estado final; comprobar ausencia de vistas o stacks inconsistentes |
| Desplazamiento | Mismo recorrido y velocidad en listas/conversaciones equivalentes | FrameTimingMetric, FrameTimeline, fotogramas fuera del plazo y p50/p90/p95/p99 |
| Memoria | Arranque estable, repetir abrir/cerrar, reposo y presión controlada | dumpsys meminfo, Android Studio Memory Profiler/heap dump en sesión privada; tendencia retenida y GC |
| Crashes/ANR | Arranque, navegación, multimedia y plugins controlados | logcat, Android vitals local cuando proceda, ANR traces/bugreport con revisión de privacidad |

Como punto de partida, cinco calentamientos y treinta repeticiones por escenario, con varias sesiones y orden alternado base/candidato. Ajustar el tamaño muestral después de observar dispersión. Conservar valores individuales y distribuciones, no solo promedios. El presupuesto de fotograma depende de la frecuencia real (aprox. 16,67 ms a 60 Hz y 8,33 ms a 120 Hz); no imponer al dispositivo una frecuencia no verificada.

## Criterios antes de integrar funciones

Acordar tolerancias con el propietario antes de evaluar candidatos. Primero obtener una base ejecutable y estable; después medir exactamente la misma variante con una sola función por cambio. Investigar regresiones reproducibles mediante trazas, incluyendo waits, cachés, blur y hooks señalados en el Paso 2. Correlación temporal no demuestra causa. Una fuga exige demostrar retención y su ruta de referencias; un riesgo estático no es una medición.

No hay emulador/dispositivo autorizado conectado en la comprobación ADB de este paso. La instalación y las mediciones sobre el Poco quedan pendientes; este plan no certifica Android 17, alta frecuencia ni compatibilidad de todas las bibliotecas nativas.
