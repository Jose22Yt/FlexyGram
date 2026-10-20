# Protocolo de comparación, pendiente de ejecución Android autorizada

## Preparación controlada

No se ejecuta en teléfonos personales, no se crean cuentas ni se habilitan
servicios. Primero laboratorio y autorización de instalación/firma por separado.
Las herramientas nuevas no realizan esas acciones. Diagnostic aislado carece de
conversaciones reales autenticadas: no sirve para comparar tiempos de chat sin
un dataset/harness offline revisado. Para clientes sin modo fixture equivalente,
la comparación de chat queda pendiente; no inventar datos para completar tablas.

Usar la misma unidad de laboratorio y una imagen/estado reproducibles. Registrar
API, ABI ARM64, página4KB/16KB, compilación Android, Hz observados, resolución,
densidad/fuente, navegación, tema, escalas de animación, carga/ahorro y estado
térmico. No fijar unknown a un valor supuesto. No cambiar las escalas ni
preferencias globales desde el collector. Conservar los snapshots de estado
fuera de Git y revisar ausencia de datos personales.

Preparar versiones identificadas por SHA-256 y condiciones comparables:
Debug/Debug o Release/Release no depurable cuando esté autorizada y disponible.
No comparar un Debug con un Release para atribuir diferencias al cliente. Fijar
plugins, opciones visuales, idioma y servicios equivalentes; registrar diferencias
inevitables y usar protocolo distinto/INCOMPARABLE. Comparar modos visuales de
producción puede ser otro experimento separado del coste puro de navegación.

Dataset local idéntico: misma cantidad de diálogos/mensajes, tipos de contenido,
medios precargados, tamaños de texto y posiciones de scroll, sin cuentas reales.
No importar sesiones ni preferencias de otras apps. No permitir red para
compensar un dato ausente. Se necesita revisión de fixture equivalente para
Exteraless y Exteragram, no sólo para FlexyGram.

## Matriz mínima a ejecutar después

| Escenario | Secuencia controlada | Observaciones requeridas |
|---|---|---|
| Inicio frío | Proceso nuevo, estado de datos conocido | proceso/primera escena, JNI/Python, fatal/ANR; separar warm startup |
| Abrir/cerrar chat | Lista→mismo chat→Atrás; gestos por separado | request/accepted/frame de destino y frame de lista |
| Pulsaciones rápidas | Secuencia fijada, p.ej. intervalos25/50/100ms en cohortes distintas | cada request, aceptación, cancelación/timeout y destino final esperado |
| Interrupción | Nuevo toque durante transición a fracción definida | ID anterior cancelled y nuevo ID independiente; sin falsos presented |
| Scroll | Misma distancia, velocidad y contenido precargado | ventana gfxinfo/traza completa y stream de ventana principal |
| Claro/oscuro | Tema inicial fijo, cambio y retorno repetidos | frame del tema solicitado, excepciones, retorno funcional |
| Nativo/Python | Carga y operaciones fixture permitidas | fallos de enlace/símbolos/JNI/importaciones; no sólo existencia de .so |

No confundir huecos de observación con pérdida de toques. Verificar destino final
con un observador de estado/vídeo revisado; un contador de clicks no lo demuestra.
No instrumentar mensajes de conversaciones para saber cuándo termina la acción.

## Repeticiones y análisis

Mínimo5 repeticiones emparejadas por build/cliente; alternar A/B o rotar
FlexyGram/Exteraless/Exteragram para reducir deriva térmica. Contrabalancear el
orden dentro de cada pareja. Guardar identificador repetition idéntico y run_id
distinto para cada toma. Registrar interrupciones del sistema y descartar una
pareja completa con razón previa, sin seleccionar sólo muestras favorables.

Para cada escenario de latencia: al menos10 acciones completas por repetición
(el protocolo recomienda30), con calentamiento separado que no entra en la
muestra. Caché cold y warm son cohortes diferentes. Si falla una acción, conservar
el fallo, no repetirla silenciosamente hasta sustituirla por un éxito.
La comparación de latencias se bloquea si hay timeouts/incompletos, o si los
supervivientes no representan todos los requests. Los contadores permanecen
visibles para investigar la regresión funcional.

Frames: al menos30 muestras válidas en ventana CLOCK_MONOTONIC y stream de
escena principal; verificar que el ring buffer no truncó la interacción.
`gfxinfo` no es un registro ilimitado. En escenarios largos, usar traza de
sistema cuando exista soporte y autorización, sin sustituir bytes perdidos por
estadísticas acumuladas. FrameTimeline/SurfaceFlinger o vídeo pueden comprobar
presentación; su captura/importación no se implementa automáticamente aquí.
No se distribuyen binarios de trace_processor ni se descargan al ejecutar tests.

El comparador informa deltas de p95 por pareja y su mediana. Requiere diferencias
>10% y >5ms de latencia en todos los pares para señalar empeoramiento observado
consistente. Para p95 frame usa >10% y >2ms; over-budget >5 puntos porcentuales.
No son umbrales oficiales ni una prueba de significancia. Revisar variación,
incertidumbre del endpoint, datos de CPU/GC y validez del diseño experimental
antes de atribuir causas o afirmar que una optimización funciona.

## Capturas y custodia de resultados

Conservar logs/trazas originales únicamente en almacenamiento privado del
laboratorio y con aprobación. El collector de esta rama sólo guarda el resumen
redactado y hashes; no conserva originales para reproducir cada clasificación.
Para investigación profunda usar un procedimiento privado separado, con revisión
de sensibilidad y correlación de hash, antes de compartir cualquier captura.
No subir Logcat de cuentas personales, heap dumps o trazas con nombres de chats.

Registrar inputs, scripts por SHA, APK instalada (el collector verifica APK
única), manifiesto/firma verificados por el laboratorio, metadatos, ventanas,
resultados y herramientas. El analizador no certifica firma ni autenticidad de
archivos aportados manualmente. Un informe con `source=android_lab` fuera de una
captura auditada sigue siendo una declaración del operador.

Revisar crashes/ANR primero; después rutas de aceptación, frames y memoria.
Si se propone corregir algo, medir antes/después bajo este mismo protocolo y
probar restauración/rollback de datos sintéticos. No empezar diseño o navegación
nuevos para encubrir un fallo. Este documento no autoriza esas etapas.
