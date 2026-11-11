# Beta 47 — FlexyBubble Camera Pop

> Histórico: esta función se retiró completamente en beta 50. No describe la versión actual.

Implementación interna opcional, apagada inicialmente. Parte de beta 46, conservando
el inicio optimizado, las animaciones anteriores y la pantalla principal por defecto.

## Integración

- `NotificationsController.processNewMessages`: puente después de la deduplicación,
  exclusión del chat abierto y decisión nativa de preferencias. Solo se envían al
  hilo UI los mensajes entrantes de chats seleccionados. No se retienen mensajes,
  cuerpos, nombres ni avatares en los registros de recordatorios.
- Ajustes de FlexyGram → Conversaciones → FlexyBubble Camera Pop. Selector nativo
  de varios chats con búsqueda, contactos, grupos/supergrupos, canales y bots.
  Preferencias independientes por cuenta. Sin selección no aparecen avisos.
- Avisos inmediatos y recordatorios se controlan por separado. Intervalos 5/15/30
  minutos; permanencia 2/4/6/10 segundos. Horario de silencio configurable.
  Ocultar nombres también oculta los avatares. La excepción a los silenciamientos
  requiere desactivar expresamente el respeto por las preferencias de Telegram.
- El estado mantiene el último ID por diálogo, tema del último mensaje y próximo
  vencimiento. Se conserva la marca de deduplicación después de leer. Nunca se
  cuentan mensajes sumando eventos: se consulta el contador nativo antes de mostrar.
- Nueva cuenta en una ranura antes utilizada: se invalidan selección/activación y
  vencimientos del propietario anterior. Al cerrar sesión se limpian los pendientes
  de la cuenta observada; al restaurar se verifica también el propietario.
- Cola máxima de tres diálogos, agrupación por diálogo y una ventana breve de
  agrupación que no se aplaza indefinidamente si llegan muchos mensajes seguidos.
- Las escrituras de pendientes durante una ráfaga en primer plano se agrupan durante
  600 ms. Al pausar se vacía esa escritura antes de cancelar callbacks. Después de
  una terminación abrupta se recuperan pendientes desde los diálogos seleccionados
  de la caché nativa, sin generar avisos inmediatos para mensajes antiguos.
- Pulsación: cancela movimiento y retira la cápsula antes de solicitar la navegación
  nativa. Se respetan bloqueo, cuenta y comprobación de acceso. No se espera a la salida.

## Recorte y movimiento

`WindowInsets` / `DisplayCutout.getBoundingRects()` aportan la geometría de ventana.
En API 31+ `getCutoutPath()` permite afinar el origen con el contorno real,
intersectándolo con el recorte seleccionado cuando hay varios. Se transforman las coordenadas para la vista decor. Como alternativa
best-effort en vertical se conserva el detector `NotchInfoUtils` existente de Telegram;
no se presupone que su recurso interno exista. Si no hay datos válidos se usa la
zona superior segura. Se admiten posiciones descentradas y se respetan insets laterales.

La cápsula empieza pequeña en el borde inferior del recorte y se expande hacia su
posición segura. La salida invierte el movimiento y se contrae hacia el mismo origen.
Es una ilusión alrededor del recorte: no hay píxeles utilizables sobre el sensor.
No se copia el desenfoque CPU/GPU del perfil. La superficie sigue los colores del tema.

Reloj nativo finito con Choreographer (entrada 240 ms, salida 200 ms), propiedades
translation/scale/alpha, sin dependencia de los multiplicadores x5/x10 del sistema.
Con animaciones desactivadas, lector de pantalla o ajustes internos sin animación,
se muestra/oculta inmediatamente. Durante la permanencia no hay callbacks de cuadros.
Rotar/recrear/interrumpir cancela el movimiento; no quedan listeners del decor ni vistas
ocultas retenidas. No existe una capa de pantalla completa que capture gestos externos.

## Programación y límites explícitos

Solo hay un vencimiento próximo programado mientras LaunchActivity está activa.
Al pausar se retiran observadores, temporizadores, vista y referencia a Activity.
Mientras está en segundo plano pueden registrarse eventos que el sistema nativo ya
recibe, pero Camera Pop no despierta el proceso, no programa alarmas y no crea servicios.
Al volver se revalidan los pendientes. Android/HyperOS no garantizan intervalos puntuales
en segundo plano. El repetidor de notificaciones normal de Telegram permanece intacto.

Se comprueban los diálogos seleccionados con pendientes, nunca una consulta periódica
indiscriminada de todos los chats. Si la caché del diálogo no está disponible, se pospone
el aviso en lugar de inventar contadores. No se solicitan red, cámara ni permisos de
superposición adicionales. Esta primera versión no incorpora chats secretos al selector.

## Verificación automatizada

`python -m pytest tests/test_camera_pop.py tests/test_camera_pop_types.py -q`

- JVM ejecuta las clases de estado y geometría: centrado/lateral/horizontal, densidades
  representadas en píxeles, ventanas pequeñas, fallback y áreas seguras.
- JVM ejecuta coordinador y preferencias reales con hosts Android/Telegram simulados:
  selección, silenciamientos/excepción, lectura, privacidad, cambio de cuenta,
  recordatorios vencidos, horario de silencio, recreación, desactivación y cierre.
- Se ejecutan los métodos de movimiento de producción con un reloj determinista:
  aparición, absorción, interrupción, alternativa sin movimiento y fin de callbacks.
- Las seis clases nuevas se comprueban contra un android.jar real cuando está disponible,
  con servicios/vistas de Telegram simulados. Esto no sustituye la compilación integrada.
- Comprobaciones del puente nativo y de recursos inglés/español.

Resultados locales: suite general **400 passed, 39 skipped** (122,75 s). Tras los
ajustes finales de agrupación/persistencia, la suite enfocada vuelve a pasar sus
**9 pruebas**, incluida compilación de tipos contra Android API 35. Las omisiones
de la suite general corresponden a sus condiciones de herramientas/fixtures;
no deben interpretarse como pruebas físicas completadas.

## Prueba manual pendiente en APK/dispositivo

1. Abrir la nueva entrada y probar la demostración aún con la función apagada.
2. Seleccionar un chat privado, grupo, canal y bot. Activar avisos y recordatorios.
3. Recibir mensajes reales desde otra cuenta estando en la lista de chats: una cápsula,
   contador nativo y foto correcta. Un chat no seleccionado no debe mostrar Camera Pop.
4. Pulsar durante entrada y durante salida: abrir al primer toque, sin esperar.
5. Leer desde otro cliente antes del recordatorio; comprobar que no aparece tras sincronizar.
6. Silenciar el chat; comprobar respeto por defecto y la excepción explícita. Probar también
   categorías globales y temas silenciados de un foro.
7. Activar privacidad y horario de silencio (incluido el que cruza medianoche).
8. Rotar durante entrada/salida, bloquear/desbloquear, cambiar de cuenta y recrear Activity.
9. Salir de la aplicación más de cinco minutos y volver: revalidar pendientes sin avisos
   sobre otras apps. Desactivar: ninguna cápsula, callback ni recordatorio pendiente.
10. Probar cámara centrada, lateral, notch ancho, pantalla sin recorte, multiwindow,
    tamaños de fuente grandes, claro/oscuro y animaciones desactivadas.

## Rendimiento: mediciones todavía pendientes

No se han medido FPS, memoria, CPU ni latencia en el Poco indicado. Las pruebas JVM
verifican políticas, geometría y limpieza; no son una certificación de fluidez física.

Comparar la misma APK con Camera Pop apagado/encendido: misma cuenta, conjunto de chats,
frecuencia de pantalla y temperatura. Tras calentar cachés, repetir scroll/apertura de chat
con y sin ráfagas entrantes. Capturar Perfetto FrameTimeline, CPU y asignaciones; registrar
p50/p95/p99 de duración de cuadro, cuadros fuera de presupuesto, memoria antes/durante/
después de avisos y tiempo del toque hasta navegación. Comprobar también arranque en frío.
Usar las herramientas de diagnóstico ya existentes solo en compilaciones opt-in.
No afirmar impacto cero ni pruebas físicas completadas sin estas capturas.

## Entrega

La compilación integrada corresponde al workflow oficial `ui-beta-debug.yml` en
`codex/flexygram-beta-glass`. Por indicación del propietario se inicia al publicar el
commit final y no se vigila ni se declara exitosa desde esta sesión.
