# Beta 48 — avisos reales e independencia de notificaciones del sistema

## Problemas corregidos

En beta 47 Camera Pop dependía de un puente dentro de NotificationsController,
posterior a filtros y preferencias de notificaciones. Además, restaurar pendientes
usaba el mismo registro de deduplicación que recibir un mensaje: podía registrar
el ID antes de que llegara el aviso inmediato. Al entrar se esperaban vencimientos
en lugar de recordar siempre los pendientes; perder foco o recibir contadores con
retraso podía vaciar la cola. El código también sustituía el contador nativo con una
comparación de IDs que podía descartar pendientes válidos en diálogos/foros.

## Integración actual

- Observa `NotificationCenter.didReceiveNewMessages` con cuenta activa, modo normal,
  mensajes entrantes reales, no leídos, no importados ni de servicio. Se elimina el
  puente en NotificationsController. Los avisos no consultan el permiso Android ni
  la habilitación de categorías generales de Telegram; no cambian esos ajustes.
- Sigue avisando exclusivamente de chats escogidos. Se conserva el control de
  silenciamientos, pero ahora solo consulta excepciones explícitas de chat/tema en
  NotificationsSettingsFacade. Un bloqueo global no se interpreta como silencio
  explícito de todos los chats. Privacidad, bloqueo de aplicación y horario de silencio
  mantienen su efecto. Las notificaciones normales de Telegram permanecen intactas.
- `CameraPopState.seed` reconstruye el candidato pendiente sin consumir el ID de
  llegada. La persistencia admite los registros anteriores y guarda separadamente
  ambos valores. Marcar leído conserva la deduplicación.
- Con recordatorios activados, cada regreso a primer plano prepara recordatorios de
  los seleccionados que sigan pendientes, incluso si aún no vence el intervalo.
  Cada diálogo se recuerda una vez por entrada; no por cada recarga nativa. Se
  mantiene la cola máxima de tres y la agrupación para evitar una ráfaga larga.
- Si falta foco al abrir o aún no se cargó el diálogo, conserva el candidato hasta
  un cambio de foco o evento de caché. Un aviso inmediato con contador tardío permite
  tres reintentos acotados de 120 ms y también se recupera al actualizarse la caché.
  No inventa contadores ni consulta todos los chats periódicamente.
- La presentación utiliza el contador nativo. La lectura confirmada elimina los
  pendientes; pulsar cancela la animación antes de abrir la conversación.

## Movimiento de referencia

Se inspeccionó la grabación de 5,95 segundos proporcionada por el propietario: el
avatar se estrecha, forma un cuello corto y termina dentro del agujero, en lugar de
atenuarse a mitad del trayecto. Camera Pop usa esa dirección visual:

- El origen/fin pasa del borde inferior al centro del contorno disponible; la posición
  de reposo permanece debajo de la barra y fuera del recorte.
- Contracción horizontal adelantada, seguida de la vertical; destino dentro del
  agujero con tamaño terminal inscrito en un recorte circular.
- Silueta de cuello corta dibujada mediante Path/Paint reutilizados. El contenido se
  retira durante la contracción y la superficie queda opaca hasta el final físico.
  Cuando no hay geometría válida se utiliza una salida superior segura con atenuación.
- Entrada 300 ms, salida 280 ms, reloj finito Choreographer propio y sin rebote.
  No se usa el blur CPU/GPU del perfil, buffers de pantalla ni shaders de cristal.
  Canvas solo se invalida durante el movimiento; en reposo no hay callbacks de cuadros.
- Se conserva cancelación inmediata, movimiento reducido y retirada completa de la vista.

## Verificación

`python -m pytest tests/test_camera_pop.py tests/test_camera_pop_types.py -q`

Las pruebas ejecutan producción de estado/coordinador con hosts nativos explícitos,
inyectan el evento de mensajes real de NotificationCenter (no el antiguo puente),
comprueban personas y canales, categorías desactivadas, mensajes duplicados/propios/
programados, siembra previa del mismo ID, caché tardía, foco, silenciamientos y excepción.
También verifican cada regreso con pendientes antes del intervalo, ausencia tras
lectura, terminal geométrico inscrito, opacidad hasta el agujero y reloj finito.
La comprobación de tipos usa android.jar real cuando está disponible; los servicios
y vistas grandes de Telegram son dobles. No equivale a una APK integrada o un móvil.

Resultado local de la suite general: **405 passed, 39 skipped** (120,65 s).
Tras los últimos ajustes, las **14 pruebas enfocadas** pasan, incluida la comprobación
de tipos de las siete clases contra Android API 35. Las omisiones de la suite general
son condiciones de herramientas/fixtures, no pruebas físicas completadas.

## Prueba manual de aceptación

1. Activar Camera Pop y escoger un contacto y un canal. Desactivar las notificaciones
   de FlexyGram en Android, sin desactivar Camera Pop.
2. Con FlexyGram visible y fuera del chat escogido, recibir mensajes reales. Deben
   aparecer la cápsula y el contador correcto. Repetir con categorías globales de
   Telegram desactivadas y con ráfagas.
3. Silenciar expresamente el chat: verificar el control de silenciamientos encendido
   y apagado, sin confundirlo con el bloqueo global.
4. Mantener mensajes sin leer, salir y volver antes de cinco minutos. Con recordatorios
   activos debe recordar sin esperar al vencimiento. No debe repetirse por cada
   actualización de la lista. Leer desde otro cliente, sincronizar y repetir: ningún aviso.
5. Abrir en frío con caché cargando; comprobar el aviso al estar disponibles el foco
   y los contadores. Probar con el chat elegido abierto: no debe avisar sobre él.
6. Revisar entrada/salida en cámara centrada y lateral, claro/oscuro y rotación.
   Pulsar durante la absorción debe abrir al primer toque. Sin agujero: fallback seguro.
7. Salir o apagar Camera Pop: sin vistas, callbacks de cuadros ni recordatorios activos.

No se ejecutaron pruebas físicas ni mediciones de FPS en el Poco. Comparar activado/
desactivado con las capturas de FrameTimeline, CPU y asignaciones descritas en beta 47.
No se ha afirmado impacto cero. La función es interna; no aparece sobre otras apps ni
recibe permisos adicionales, y no sustituye el transporte push ni las notificaciones
normales. La compilación se inicia con el push final y no se inspecciona por indicación
expresa del propietario.
