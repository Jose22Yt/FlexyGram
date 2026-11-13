# Preparación local del historial antes de abrir chats

## Alcance y motivación

La referencia de arquitectura es Telegram-iOS `24638bc69bd083981b178dd1e7f921eebbf7fc46`,
en particular `ChatHistoryPreloadManager`, la preparación del controlador y las
transiciones de historial. Se adapta el principio de preparar trabajo útil antes
del toque; no se copia Swift ni se introduce su infraestructura en Android.

La integración usa `MessagesStorage.getMessagesInternal` y la ruta nativa
`processLoadedMessages`, con sus estados de lectura, ancla, paginación y datos
adicionales. No crea una segunda lista de mensajes ni reutiliza Views de otro chat.
No cambia el diseño, las curvas de apertura, MTProto o las notificaciones.

## Política de trabajo

- La lista principal solicita una comprobación al quedar visible, recibir una
  actualización o terminar un desplazamiento. No hay polling ni callback por frame.
- Se espera 350 ms de reposo y al menos tres segundos entre lotes solicitados.
  Eventos repetidos comparten una sola comprobación pendiente.
- Se eligen hasta dos chats realmente visibles: primero no silenciados; dentro de
  cada grupo, primero los que tienen mensajes sin leer. El orden visual desempata.
- Cada lectura se encola con 80 ms de margen y solo empieza la siguiente cuando
  termina la anterior. Usa el tamaño inicial nativo: 25 o 15 según el dispositivo.
- Scroll activo, búsqueda, selección, previsualización, otra pantalla, pausa,
  destrucción o ahorro de energía impiden o cancelan la preparación. Antes de cada
  lectura se vuelven a comprobar cuenta, propietario, visibilidad y candidatos.
- Las tareas eliminadas y las terminaciones antiguas no pueden iniciar otro lote.

## Resultado reutilizable

El cargador nativo prepara los mismos mensajes y metadatos que una lectura normal,
pero no los envía al controlador todavía. Tampoco realiza solicitudes de red. Si
el lector necesitara crear un registro de huecos, la preparación termina sin
escribir ni guardar un resultado parcial; la apertura normal realizará ese trabajo.

Un resultado se conserva cinco segundos, una sola vez, con un máximo de dos
entradas por cuenta. Cada entrada admite hasta 64 mensajes y 256 KiB de payload
serializado; el total es 512 KiB de payload, **no una medición del heap Java**.
Usuarios, chats y objetos deserializados tienen sobrecarga adicional. No se guardan
bitmaps, vistas ni Activities dentro del resultado.

Se validan identidad de la conexión de base de datos, propietario, `total_changes()`
y `PRAGMA data_version` antes/después de preparar y al consumir. Cualquier cambio
local de filas, escritura desde otra conexión, cambio de propietario, reapertura
o caducidad provoca un fallo de caché y conserva la lectura nativa. La política es
conservadora: una escritura de otro chat también puede invalidar la preparación.

Solo se reutiliza el resultado para una apertura normal desde no leídos, con el
mismo tamaño inicial, sin ancla explícita, fecha, historial fusionado, topic o modo
especial. Secretos, foros y filas de carpeta no se preparan. Las rutas especiales
mantienen su implementación nativa.

Al consumir, se retira el resultado **antes** de procesarlo y se entrega con el
`classGuid`, índice de carga y logger de la apertura actual. La cola de etapas y
el procesamiento posterior son los originales. Un fallo de caché no añade otra
espera ni una consulta SQL de revisión cuando la caché está vacía. La ruta de lectura
normal conserva un solo callback de entrega, como antes.

## Recursos y ciclo de vida

Hay una sola tarea finita de caducidad en la cola de almacenamiento. La limpieza de
cuenta elimina resultados y tarea. La presión de memoria los libera sin crear
instancias de otras cuentas y suspende diez segundos las nuevas preparaciones,
incluidas las que estaban esperando en la cola. Una lectura ya ejecutándose termina
en la cola nativa; no se bloquea la UI esperando su cancelación.

## Verificación

Los probes JVM ejecutan las clases nuevas y los métodos reales del adaptador de
almacenamiento con colas contadas. La consulta grande de SQL se sustituye por un
lector controlado; se conserva la entrega real de metadatos al controlador. Se
comprueban:

- 10.000 eventos con una sola comprobación pendiente, dos lecturas secuenciales,
  cancelaciones, finalizaciones antiguas, ahorro de trabajo y cambios de cuenta.
- Prioridad semántica y exclusión de filas no válidas.
- Uso único, TTL, límites, cambios locales/externos y conexión de base de datos.
- Una lectura preparada y **cero repeticiones del lector** al abrir con un hit;
  una segunda apertura vuelve a leer. No se procesa nada en el controlador antes
  de la apertura. GUID, índice y metadatos pertenecen a la solicitud consumidora.
- Rechazo de cola, limpieza, caducidad y suspensión por presión de memoria.
- Los contadores de revisión se verifican además con dos conexiones SQLite reales.

No se ejecuta Gradle ni se genera una APK. Los probes no ejecutan el SQL completo
de Telegram sobre una cuenta real y no demuestran FPS o tiempos en un teléfono.
El beneficio depende de que el chat candidato se abra antes de caducar y no haya
escrituras que invaliden el resultado.

## Prueba manual pendiente

1. Dejar quieta la lista y abrir un chat visible; comparar con abrir otro tras un
   fling. Verificar primera respuesta visual y primer historial, no solo duración
   total de la animación.
2. Recibir, editar o borrar un mensaje inmediatamente antes de abrir. Comprobar
   contenido, contador de no leídos y posición inicial.
3. Probar retorno rápido, cambios de carpeta/cuenta, ahorro de energía, pausa y
   presión de memoria, junto con chats secretos, foros, búsquedas y enlaces a mensajes.
4. Comparar tiempo de fotograma, CPU, memoria y latencia con la base anterior en el
   mismo dispositivo. No se ha obtenido una medición física en esta tarea.

Resultado de regresión: **471 pruebas pasadas y 39 omitidas**. Tras ampliar la
exclusión a foros de bots y monoforos, las siete pruebas dirigidas de preparación
y almacenamiento también pasan. Sintaxis Java verificada y `git diff --check` limpio.
