# beta73: escrituras en la carga de la lista

Base 5b43225430d9de8946a6e3a42ac155a07cbb95b9; versión
1.0.0-beta.73-dialog-checkpoints, código 1362. Misma base nativa optimizada.

## Auditoría y prioridad

P2 verificado: UserConfig.setPinnedDialogsLoaded, setTotalDialogsCount y
setDialogsLoadOffset usaban commit síncrono, con el resultado ignorado. Los usan
la carga/procesamiento de diálogos, la recuperación y los cambios de carpetas.
Cada invocación podía esperar la persistencia en disco, incluso con los mismos
valores. No se dispone de una duración medida de ese bloqueo en el teléfono.

La carga inicial seleccionada ya solicita SQLite antes que los servicios
auxiliares, con una primera página de 32 y continuación nativa. Las aperturas
normales de chats pasan por ChatNavigationGate/ChatPeerPreloader para los peers
fríos. No se sustituye esa arquitectura ni se oculta una lista vacía para aparentar
rapidez. Quedan rutas heredadas con lecturas síncronas fuera de ese gate; no se
ha demostrado que correspondan al gesto normal reportado por el usuario.

## Corrección

Estos tres setters publican las preferencias inmediatamente mediante apply y
la implementación nativa se encarga de persistirlas de forma asíncrona. Si el
valor ya es idéntico no crean otro editor ni otro trabajo de escritura. La
comprobación y la publicación usan el monitor sync existente de UserConfig,
para no introducir carreras entre escritores de sus marcadores.

Se mantienen nombres/tipos de claves, valores centinela, distinción por cuenta
y carpeta y los seis campos del offset + validez en un único editor. La eliminación
de una escritura redundante requiere que existan los seis campos de esa carpeta,
además de la validez global: una carpeta nueva o restaurada parcialmente aún debe
guardar sus campos aunque sus valores coincidan con los defaults.

Solo cambia la persistencia de metadatos de carga. No cambia la transacción de
mensajes en SQLite, las consultas, el envío, las claves de cuenta ni la lógica
nativa de sincronización. apply conserva visibilidad en memoria antes de retornar;
no garantiza que un cierre abrupto conserve un marcador aún pendiente de disco.
Un marcador anterior puede provocar repetir carga/paginación al reiniciar. No se
introduce una confirmación ficticia de escritura ni se modifica la idempotencia
de la integración de diálogos existente. No es una prueba física de terminación
del proceso con SQLite y preferencias en vuelo.

Se conservan la política de memoria beta72, el ciclo de vida del dock beta71 y
las superficies nativas actuales. No se añaden animaciones, preloads de vistas,
prioridad de lecturas sobre escrituras de SQLite ni temporizadores de limpieza.

## Verificación

La regresión ejecuta los seis cuerpos reales de getter/setter en JVM con una
implementación explícita de preferencias que publica memoria y encola disco.
Antes falla al detectar commit síncrono. Después verifica publicación inmediata,
campos agrupados, enteros largos extremos, cuentas/carpetas independientes,
restauración desde el snapshot persistido y reparación de una carpeta parcial.
10000 actualizaciones idénticas no añaden escrituras, y cuatro hilos repiten
1000 actualizaciones cada uno sin añadir editores para el mismo estado.

Suite general: 550 pruebas pasadas, 41 omitidas. La comprobación final específica
tras reforzar casos de presencia/concurrencia pasa también. Son operaciones
verificadas, no milisegundos de arranque ni FPS medidos. No se repite el harness
Compose porque sus fuentes y ciclo de vida no cambian.

Revisión final: aprobado para compilación. La comparación física pendiente debe
separar arranque con proceso nuevo, regreso al mismo proceso, lista con caché local
y primera sincronización. Usar las trazas existentes Flexy.startup.* y medir el
tiempo hasta lista/contenido visible; para conversaciones, separar peer frío,
lectura de historial y primer frame con mensajes. No se afirma que toda la
latencia restante de arranque, red, disco o composición esté resuelta.
