# Inicialización de imágenes y archivos bajo demanda

Continuación de `c448c7862`, rama `codex/flexygram-kyant-scoped-performance`.
Son cambios de fuente posteriores a beta64. No se modifica la versión, no se
ensambla una APK y no se solicita GitHub Actions en esta entrega.

## Gestores por cuenta

El constructor de ImageLoader solicitaba FileLoader para los 10 slots de cuenta
con el único fin de instalar sus callbacks. Cada instancia prepara dos arrays
con cinco FileLoaderPriorityQueue cada uno, sus listas/mapas y un wrapper
FilePathDatabase, aunque el slot no se utilice.

ImageLoader ahora publica los directorios de caché e instala una fábrica de
callbacks. FileLoader utiliza su bloqueo de creación existente para:

- Conectar los gestores que ya existían, sin crear otros.
- Conectar los gestores nuevos antes de publicarlos desde getInstance.
- Asociar cada callback al número de cuenta solicitado.

Los seis cuerpos de callbacks se movieron sin cambiar su contenido. Las rutas
de progreso, descargas completadas, errores, subida, guardado en galería y
notificaciones mantienen el comportamiento anterior. setDelegate sigue admitiendo
un reemplazo explícito y la referencia se publica como volatile. La fábrica no
solicita singletons ni ejecuta transferencia alguna bajo el bloqueo: solo crea
el objeto de callbacks.

Una solicitud a una sola cuenta crea un gestor y 10 objetos de cola, frente a
los 10 gestores y 100 objetos de cola que provocaba el bucle de ImageLoader.
Esto **no significa 90 hilos menos**: los objetos de prioridad comparten el
worker existente. FilePathDatabase ya abría su SQLite bajo demanda; tampoco se
atribuye a este cambio evitar diez aperturas SQL que antes no se realizaban.
Las cuentas activas y las nuevas sesiones conservan la creación bajo demanda.

## Comprobaciones de carpetas multimedia

La variante sin callback de checkMediaPaths utiliza CoalescedTask, ya existente.
Eventos de permisos, montajes y actualización de listas acumulados antes del
worker requieren una sola comprobación pendiente. Un cambio que llega durante
la comprobación puede solicitar un siguiente pase; no se pierde el nuevo estado.

La variante con callback conserva una ejecución independiente y su orden:
crear rutas en cacheOutQueue → publicarlas en UI → ejecutar el callback en UI.
Esto mantiene las barreras usadas al cambiar almacenamiento o limpiar caché.
No se agregan hilos, timers, servicios, consultas de chats ni cambios de esquema.

## Validación y límites

Tests ejecutan los métodos reales de registro/getInstance/constructor con
contadores: ningún slot creado por registrar la fábrica, un único gestor por
cuenta, registro posterior a una creación anticipada, solicitudes concurrentes y
reemplazo explícito de delegado. La prueba de directorios cubre 10.000 eventos,
un cambio durante el escaneo, orden de publicación/callback y recuperación tras
una excepción. Comparación directa de los cuerpos antiguos/nuevos confirmó que
los seis callbacks se preservan sin cambios aparte de espacios.

Son pruebas de corrección, concurrencia y trabajo evitado; no mediciones de un
Android físico. Falta medir tiempo hasta contenido utilizable, asignaciones,
CPU y primer toque con datos/cache/compilación ART equivalentes. La prueba manual
posterior debe incluir avatar/foto, descargas y subidas por cuenta, cambio de
cuenta, nueva sesión, galería, cambio de almacenamiento, permisos y montaje.
Las optimizaciones previas de arranque y la integración Kyant solo en la barra
principal permanecen; no se modifica su diseño ni sus preferencias.

Validación final de host: **557 passed, 41 skipped** en la suite completa,
con los fixtures R8 reales disponibles. Los tres casos nuevos pasaron también
por separado. Sintaxis de ambos Java modificados y `git diff --check` correctos.
No se ejecutó una compilación de APK ni una medición física de Android.
