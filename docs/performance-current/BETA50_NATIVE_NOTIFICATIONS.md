# Beta 50 — notificaciones normales y precarga de chats

## Retirada solicitada

Se elimina el módulo Camera Pop/isla completo, incluida su pantalla de ajustes,
entrada en Conversaciones, textos en español/inglés, vistas, contadores, índices,
resortes, persistencia, observadores y callbacks de LaunchActivity. Se retiran sus
pruebas específicas; quedan comprobaciones de regresión de su ausencia y del flujo
normal. No se mantienen servicios, vista oculta, filtros ni temporizadores de isla.

NotificationsController vuelve al código previo a Camera Pop, que ya contenía las
optimizaciones anteriores de FlexyGram. Resúmenes y avisos por conversación vuelven
a utilizar directamente las listas nativas. Los antiguos valores locales de
configuración de la isla son inertes: ningún código los lee ni puede suprimir los
avisos. No se cambian las preferencias de notificaciones que el usuario eligió en
Telegram o Android, ni se fuerzan permisos del sistema.

Se conserva la animación nativa del avatar de perfil hacia la cámara: es una función
independiente de Telegram, no una notificación de isla. También se conservan iconos,
reproductor, pantalla principal normal, ajustes de blur/glass y mejoras de arranque.

## Correcciones nuevas de apertura

ChatPeerPreloader ya hacía las lecturas en la cola de almacenamiento. Sin embargo,
varios intentos de abrir el mismo interlocutor antes de terminar podían ejecutar
lecturas idénticas. Ahora se agrupan por cuenta, propietario, controlador y tipo/ID
del interlocutor. Cada consumidor recibe su resultado en UI y la entrada se elimina
antes de callbacks para permitir reintentos inmediatos.

Se valida el propietario antes del trabajo y antes de insertar en caché. La entrega
también verifica que siga siendo el mismo controlador. Si una actualización en vivo
ya puso datos más recientes en caché, se conserva ese objeto. Las cuentas y los tipos
de interlocutor no comparten lecturas por coincidencia de IDs.

Solo durante lecturas pendientes se observa el cierre de sesión. Al cerrar sesión
se descartan callbacks obsoletos y se libera el observador; una cola antigua detenida
no conserva los fragments de esos consumidores. Al completar una lectura normal o
fallida se libera también el observador. Un callback con error no impide que los
demás reciban su resultado.

## Comprobación

Las pruebas JVM ejecutan el código real de precarga con hosts nativos explícitos:
20 solicitudes simultáneas del mismo contacto comparten una sola lectura, sin IO
en UI y con 20 resultados; se ejercitan propietarios cambiados, logout, recreación
del controlador, datos en vivo más nuevos, callbacks fallidos y reintentos. Se
mantienen las pruebas de separación de cuentas/tipos y generación de navegación.
Estas cifras son contadores de trabajo en pruebas, no tiempos ni FPS de un móvil.

Las comprobaciones de retirada verifican que no quede módulo, ruta, recursos ni
filtro de notificaciones de isla y que no se haya eliminado el efecto del perfil.
La suite general y revisión de sintaxis se ejecutan antes de publicar el commit.
Resultado local: **401 passed, 39 skipped** (113,68 s). Tras los ajustes finales,
las **24 comprobaciones enfocadas** también pasan. No se ha afirmado una prueba
física ni una APK integrada verificada en esta sesión.

Pruebas manuales pendientes en APK:
1. Actualizar desde beta 49 con Solo isla previamente activo: el ajuste desaparece
   y los avisos siguen el comportamiento normal de Telegram/Android.
2. Recibir mensajes privados, grupos y canales con app visible y en segundo plano,
   respetando los silenciamientos y permisos actuales.
3. Abrir repetidamente un chat frío; comprobar que se abre una vez y responde bien.
4. Cambiar de conversación/cuenta durante una carga y cerrar sesión: no deben
   aparecer chats antiguos ni reemplazarse datos actuales por resultados tardíos.
5. Comprobar iconos, reproductor, scroll y avatar del perfil. Comparar trazas en el
   mismo dispositivo si se necesita cuantificar latencia, memoria o fluidez.

La APK se construye únicamente con el workflow oficial ui-beta-debug.yml. Por
indicación del propietario se publica el commit final para iniciar la compilación
sin consultar su progreso, descargar artefactos ni declarar un resultado verificado.
