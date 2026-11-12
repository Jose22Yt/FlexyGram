# Reacciones: movimiento continuo y entrega del icono

Se conserva el sistema nativo de reacciones de Telegram Android. No se modifica
el envío, el contador, la elección de reacción, MTProto ni la autenticación.
No se añaden preferencias, bibliotecas, servicios o consultas de red.

## Referencia y límites

Se revisaron `ReactionContextNode.swift` y `ReactionFlyInIconHandoff.swift` de
Telegram-iOS, revisión `24638bc69bd083981b178dd1e7f921eebbf7fc46`. La referencia
coordina el vuelo del emoji con el primer fotograma de la copia y la llegada
al botón. Su vuelo utiliza keyframes parabólicos; UIKit no se traslada a Android.

La adaptación Java utiliza una curva monotónica con velocidad y aceleración
nulas en sus extremos, una elevación pequeña en vuelos directos y una llegada
sin rebote exagerado. No se declara una reproducción idéntica de iOS 27.

El vídeo `Screenrecorder-2026-11-12-11-03-41-372.mp4` no pudo descargarse: la
herramienta rechazó el archivo por superar el límite de transferencia de 32 MiB.
No se declara una inspección de sus fotogramas ni una comparación visual realizada.

## Correcciones

- El overlay y los avances de partículas usan tiempo monotónico entre fotogramas
  en conversaciones. Se sustituye el avance fijo de 16 ms por dibujo, que cambiaba
  la duración con la frecuencia de la pantalla. Los intervalos se limitan a 32 ms
  para evitar teletransportes tras una pausa larga; un atasco prolonga la animación.
- Vuelo directo de 240 ms y llegada de 200 ms. Posición y escala comparten la
  curva. El origen del aterrizaje se captura una vez, evitando recalcularlo desde
  una expansión todavía activa. Las historias conservan sus tiempos anteriores.
- Origen y destino de mensajes se calculan en pantalla y se convierten al espacio
  local del overlay. Se toma el tamaño real del icono de destino. No se usa la
  esquina superior de la celda cuando el botón aún no está medido.
- El último estado se dibuja antes de completar. La finalización se ejecuta una
  vez, con el propietario correcto; una animación antigua no borra una más reciente.
- El icono nativo permanece visible hasta que hay píxeles reales del overlay cerca
  del destino. La mera existencia del drawable o una miniatura no basta. Se
  comprueban cuenta y vista propietaria para evitar ocultar otros mensajes.
- El icono de origen se oculta después del primer dibujo y recupera su alfa
  original al cancelar/terminar. Un holder reutilizado para otra reacción no se toca.
- El fade del efecto dentro de la burbuja usa tiempo real y solo comienza cuando
  hay un fotograma decodificado y la animación llegó al final, no antes de cargar.
- En el selector, el crecimiento de la pulsación y su cancelación dejan de
  competir. El avance usa tiempo monotónico y se protege la propiedad del animator.
- Se sustituyen los overlays anteriores de cada canal al recibir otra reacción.
  Los compañeros pendientes se retiran con su propietario; los que ya están
  reproduciéndose terminan por su propia ruta.
- La espera previa al inicio no mantiene un bucle de dibujo propio. Después
  del inicio solo se solicitan fotogramas propios si hay un emoji dibujado o
  empezó el efecto. Los recursos invalidan al estar disponibles. La geometría
  pendiente espera como máximo 350 ms antes de retirar el efecto. Un callback de
  seguridad de cinco segundos, cancelado al liberar la vista, limita el tiempo
  de vida si el recurso no llega o el inicio se pierde. Se limpia al salir del chat,
  al desaparecer el mensaje y al desmontar la vista.
- Máximo cuatro avatares decorativos por efecto de grupo. Sus ImageReceiver se
  desregistran al desaparecer. Se corrige el cambio de AnimatedEmojiDrawable para
  retirar la instancia anterior, sin dejarla enlazada a la vista.

## Validación y comprobación física pendiente

Los probes JVM ejecutan el reloj/curva a distintas frecuencias, los estados de
entrega del icono, carga tardía, sustitución del drawable, limpieza idempotente,
pulsaciones/overlays sucesivos, identidad de cuenta/vista y destrucción de varios
overlays relacionados. Se comprueba el orden del último dibujo y la finalización.
La suite general final pasa **434 pruebas, con 39 omitidas**. La última comprobación
dirigida pasa **7 pruebas**, incluida la exclusión de miniaturas no decodificadas.
Las pruebas dirigidas se solapan con la suite; no se suman como pruebas distintas.

No se ha compilado una APK, ejecutado la app en Android ni medido FPS, CPU o
memoria en dispositivo. Los checks de referencias de plugins se omiten sin su
corpus opcional y no equivalen a una compilación del cliente.

En la próxima prueba física revisar:

1. Tap, doble toque, selector y pulsación larga; soltar y cancelar a medias.
2. Emoji estándar, personalizado y assets aún no descargados; probar modo ligero.
3. Pulsaciones rápidas en reacciones distintas y en mensajes diferentes.
4. Mensajes de texto, fotos, álbumes, mensajes de servicio y distintos contadores.
5. Scroll durante el efecto, mensaje fuera de pantalla, cambio de chat y volver atrás.
6. Cambio de cuenta, rotación, cierre de Activity y reapertura.
7. Pantallas de 60/90/120/144 Hz, animaciones de FlexyGram desactivadas y retorno
   desde segundo plano. Revisar también historias por compartir la clase del overlay.

Los commits de esta tarea usan `[skip ci]`: no se inicia una compilación de APK.

## Limpieza al terminar las partículas

`ReactionMotion.advance` limita el progreso a `1`. La salida de los avatares ya
no espera un valor imposible `> 1`: `advanceAvatarExit` retira el avatar en el
fotograma terminal y deja de transformarlo/dibujarlo. El recorrido conserva el
índice correcto cuando terminan varios avatares consecutivos.

El overlay registra si los receptores se adjuntaron. Al retirarlo, una limpieza
compartida vacía las referencias y desadjunta cada receptor una sola vez, antes
de retirar la ventana. Así funciona también ante interrupciones, desmontaje
reentrante y una ventana que ya no pueda retirarse. Un overlay que todavía no se
adjuntó solo libera sus referencias. La limpieza posterior de `onDetachedFromWindow`
es idempotente.

El tiempo restante de la animación se calcula una vez por fotograma para todos
los avatares, y el radio constante se configura al crear cada receptor. Se
elimina otra comprobación redundante de progreso superior a uno. No se cambian
las curvas, duraciones ni preferencias de movimiento, ni se añaden asignaciones
al recorrido de partículas por fotograma.

Validación dirigida posterior: **17 pruebas aprobadas y 1 omitida** en las suites
de reacciones, propiedad de animaciones y minirreproductor. Incluye ejecución de
los métodos reales de salida/liberación, llegada exacta a uno, cuatro partículas
consecutivas, limpieza anidada, interrupciones y fallo de retirada de ventana.
No se compiló APK ni se midieron FPS en dispositivo.
