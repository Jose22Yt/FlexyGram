# beta.58: primera lista local durante el arranque

Rama: `codex/flexygram-beta-glass`. Versión beta.58 / 1347.
Se conservan los parches de beta.55–57.

## Evidencia y alcance

El registro del usuario corresponde a beta.55 (1344), no a este parche.
En sus dos arranques fríos, `Flexy.startup.request_local_dialogs` comienza en
529553280229825 y 529561119764826 ns. Las primeras lecturas SQLite comienzan en
529553632044825 y 529561475144211 ns y duran 22,91 y 22,53 ms.
Eso supone unos 352 y 355 ms desde el comienzo de la solicitud hasta comenzar
la lectura; descontando el tramo síncrono de la solicitud, quedan unos 314 y
332 ms. El registro no identifica qué función Java consume toda esa espera:
no contiene muestras de pila de CPU. No se atribuye toda ella a filtros ni se
promete eliminarla por completo.

Sí se comprueba en el código que `MessagesStorage.openDatabase()` encola la
carga de filtros, recuperación de notificaciones no leídas y tareas pendientes
antes de que el llamador pueda solicitar la página inicial. Los filtros
pueden recalcular contadores y recuperar pares fijados; las notificaciones
leen mensajes y sus pares. Compiten en la misma cola serial de almacenamiento.
Además, la consulta de la primera página filtraba por carpeta y ordenaba por
fijado/fecha sin un índice que cubriese las tres columnas.

## Corrección

- La inicialización de la cuenta seleccionada reserva `MessagesStorage` antes
  de crear `MessagesController`. Solo el arranque de interfaz solicita esta
  reserva. La base de datos se abre y migra normalmente.
- Durante esa reserva, se posponen los tres trabajos auxiliares. La lectura
  local nativa se encola antes de liberarlos. Un `finally` libera la reserva
  también si la sesión ya no existe o no se puede solicitar la página.
  Todos los cambios de estado posteriores al constructor se realizan en la
  cola de almacenamiento. No se altera su orden FIFO ni se bloquea el hilo UI
  esperando a un resultado.
- Las entradas de push/servicio conservan la recuperación inmediata habitual,
  incluso sin Activity ni fotograma. Una instancia ya creada no se reinicia
  ni vuelve a aplazar sus tareas. No hay temporizador ni espera de red nuevos.
- Migración SQLite 179 → 180: índice
  `dialogs(folder_id, pinned DESC, date DESC)`. También existe en bases nuevas.
  No se cambian la consulta, contenido, cuenta, archivos de sesión o límites de
  paginación. Construir el índice tiene un coste único durante la migración;
  mantenerlo añade trabajo a las escrituras que modifican sus columnas.
- Nuevos marcadores Perfetto: espera en `Flexy.dialogs.storage_queue`,
  `Flexy.dialogs.stage_queue`, `Flexy.dialogs.ui_queue`; trabajo de
  `Flexy.dialogs.sort` y publicación `Flexy.dialogs.publish_cache/remote`.
  No recopilan contenido de conversaciones.

## Verificación reproducible

`tests/test_startup_update58.py` ejecuta la lógica Java de producción con una
cola controlada. Cubre ambas carreras de apertura de la base, liberación sin
página, liberación repetida, inicio en segundo plano y reutilización de una
instancia existente. Verifica lectura local antes de los tres trabajos
auxiliares sin perderlos ni duplicarlos.

También ejecuta el SQL real con los esquemas de producción y 12.000 diálogos
sintéticos. Antes aparece `USE TEMP B-TREE FOR ORDER BY`; después se utiliza
`folder_pinned_date_idx_dialogs` sin ordenación temporal. Se comparan filas,
carpetas, páginas y actualizaciones de fijación/carpeta/fecha.
Una medición local adicional con SQLite 3.53.1 cuenta 148.345 instrucciones de
VM antes y 1.619 después para la primera página de 32 filas, idénticas.
Es trabajo de una consulta sintética, no tiempo Android ni mejora porcentual
del arranque de la aplicación.

Suite local: `python -m pytest -q tests` con las dependencias JVM reales de
AI disponibles: **512 passed, 43 skipped** (172,91 s). Los casos omitidos
requieren capacidades opcionales del entorno. Esta suite no sustituye la
compilación Android ni una medición en dispositivo.

## Validación pendiente en dispositivo

Todavía no hay una traza posterior al parche. Para confirmar el resultado,
medir primera pantalla **con filas**, no solo primer fotograma: arranque frío,
reapertura, modo avión con caché, reconexión, cuenta seleccionada distinta de
cero y cuenta sin caché. Los chats guardados deben ser utilizables durante la
sincronización; mensajes recientes, borradores, archivo, contadores y filtros
se deben actualizar normalmente. Una cuenta nueva sin datos locales necesita
red para descargar sus chats por primera vez.

Este parche no oculta «Actualizando» ni cambia MTProto/getDifference. Si la
sincronización sigue tardando tras mostrar la lista local, debe distinguirse
su latencia de red de la espera de disco/procesamiento/publicación con los
marcadores nuevos. No se declara resuelto todo el arranque sin esa medición.
