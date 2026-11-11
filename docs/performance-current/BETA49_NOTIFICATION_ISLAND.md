# Beta 49 — isla de notificaciones interna

> Histórico: esta función se retiró completamente en beta 50. No describe la versión actual.

## Comportamiento

Ajustes de FlexyGram → Conversaciones → Isla de notificaciones. El interruptor
existente activa/desactiva la función. Al actualizar se conservan activación,
privacidad, horario de silencio y demás preferencias existentes. El nuevo alcance
Todos los chats está activado inicialmente y puede sustituirse por la selección
nativa de conversaciones. Los ajustes siguen siendo por cuenta.

La isla recogida muestra número de chats y número de mensajes. Al tocarla se abre
una lista de conversaciones pendientes; solo una pulsación sobre una fila solicita
abrir su chat. No se marca leído al expandir ni al recoger. Los contadores se toman
de los diálogos nativos, no se acumulan sumando eventos. Las lecturas y nuevas
llegadas actualizan el mismo panel, sin apilar nuevas cápsulas.

Duración: permanencia mientras existan pendientes (valor 0), 1–9 segundos, 10/15/30/60
y valor personalizado de 1–300 segundos. El panel expandido pausa el vencimiento;
recogerlo vuelve a iniciar la duración elegida. Cuando no hay pendientes, la isla
se retira incluso con permanencia seleccionada. Un chat abierto no se vuelve a
avisar encima de su conversación. Quedan activos horarios y silenciamientos
explícitos del usuario; Todos los chats no desactiva esas preferencias.

La demostración utiliza filas ficticias y nunca navega a IDs reales.

## Notificaciones Android

Con FlexyGram visible y apto para presentar la isla, los mensajes de su alcance se
filtran solamente de la presentación de NotificationsController. Se filtran tanto
el resumen como las notificaciones individuales. No se borra `pushMessages`, su
diccionario de deduplicación, contadores ni estado de lectura. Al pasar a segundo
plano, perder foco o desactivar la función se vuelve a solicitar la presentación
nativa sin reproducir una alerta sonora duplicada.

La opción Solo isla también filtra esos avisos en segundo plano. El ajuste informa
expresamente de que no habrá avisos visibles de mensajes fuera de FlexyGram. La isla
no se dibuja sobre otras apps y no solicita SYSTEM_ALERT_WINDOW ni permisos nuevos.

Se conservan avisos que la isla no representa: interfaces y servicios de llamadas,
reproductor, notificaciones de historias/reacciones, chats secretos y otros avisos
especiales. La isla agrega chats privados normales, grupos, supergrupos, canales y
bots de la cuenta activa. No se ha declarado una sustitución de todos los servicios
de notificaciones de Android ni una integración con la HyperIsland del fabricante.

## Geometría e interacción

`CameraPopCutout` reutiliza el detector previo: APIs oficiales, contorno cuando está
disponible y detector de Telegram como alternativa. La geometría pura calcula el
pivote en el centro real del agujero y reserva el espacio del sensor entre los
contadores. Las cámaras laterales admiten composición asimétrica. Un notch amplio
o una ventana sin geometría aprovechable usa una cápsula superior segura, sin
inventar un agujero.

La posición compacta y el panel pertenecen a una sola vista. El panel se recorta
siguiendo su forma durante la expansión. Las pulsaciones fuera de la forma visible
se rechazan en ACTION_DOWN para permitir que lleguen a la interfaz inferior.
También se excluyen de la zona táctil las esquinas transparentes del contorno.
La fila de conversación usa navegación y comprobaciones de acceso nativas. Cambiar
cuenta, bloquear, pausar o destruir retira la vista y sus referencias.

## Rendimiento y animación

- CameraPopSpring calcula la solución exacta de un resorte críticamente amortiguado.
  Un cambio de destino conserva valor y velocidad; no reinicia la animación desde
  un extremo. Se pueden invertir entrada/salida y abrir mientras se recoge.
- Choreographer solo solicita cuadros hasta estabilizarse, con límite de seguridad
  de 1,2 segundos desde la última interacción. No hay reloj de animación permanente.
- Propiedades de escala, pivote y alfa, y un Path/Paint reutilizado. Sin blur, capturas
  de pantalla, fondos animados ni bibliotecas nuevas. El movimiento reducido muestra
  el estado final inmediatamente.
- El listado es ListView/BaseAdapter con IDs estables y filas recicladas. Solo las
  filas visibles cargan miniaturas; el modo recogido no fuerza notificaciones al
  adaptador. Un cambio de contador no recalcula toda la geometría de la vista.
- La recuperación inicial recorre una instantánea nativa en bloques de 96 diálogos
  por callback. Después se revisan candidatos pendientes ante eventos; no existe
  un sondeo periódico de todos los chats. El índice se reconstruye cuando cambia
  el tamaño de la caché, ante una recarga nativa explícita o al volver, y se cancela al salir/cambiar preferencias.
- Las actualizaciones de contadores se agrupan sin posponer indefinidamente el
  primer refresco durante una llegada continua de mensajes.
- El modelo almacena únicamente IDs y contadores. Los registros antiguos de chats
  leídos se limitan a 512; los pendientes no se descartan por ese límite.
- Con la función apagada o en segundo plano normal, el filtro Android devuelve la
  lista nativa directamente. Las escrituras de pendientes siguen agrupándose.

## Verificación y límites

Pruebas JVM ejecutan modelos, geometría, resortes, reloj finito, coordinador con hosts
nativos explícitos y filtro real de presentación de NotificationsController. Se
comprueban agrupación, lista antes de navegación, selección/todos, permanencia,
pausa del ocultado al expandir, restauración Android y conservación de la cola.
Las clases nuevas se comprueban contra android.jar real con servicios grandes
simulados; no es una compilación integrada de APK.

Resultados locales: suite general **411 passed, 39 skipped** (128,87 s). Tras
los ajustes finales, **20 pruebas enfocadas** pasan, incluida comprobación de tipos
contra Android API 35. No se han sustituido pruebas físicas por estas cifras.

Prueba manual pendiente:
1. Activar y recibir mensajes de varios chats, canal y bot: una isla con total correcto.
2. Tocar para abrir lista sin navegar; tocar una fila para abrir ese chat.
3. Mantener el panel abierto más que el vencimiento, recogerlo y comprobar el nuevo plazo.
4. Probar permanencia, 1/3/9 segundos y duración personalizada.
5. Leer desde otro cliente, sincronizar y comprobar que la fila desaparece. Vaciar
   todos los pendientes y comprobar retirada completa de la isla permanente.
6. Recibir durante entrada/salida, tocar repetidamente y comprobar continuidad.
7. Probar cámaras centrada/lateral, notch ancho, multiwindow, rotación, fuente grande,
   lector de pantalla y animaciones desactivadas.
8. Enviar la app al fondo: restauración de notificaciones normales. Probar Solo isla
   por separado, desactivación, cuenta distinta y bloqueo.
9. Comparar FrameTimeline, CPU, memoria y respuesta táctil con función apagada y
   encendida, incluida una cuenta con muchos chats. No se han medido FPS ni probado
   físicamente el Poco en esta sesión.

Esta entrega es de código. No se solicita ni se supervisa una compilación de APK.
