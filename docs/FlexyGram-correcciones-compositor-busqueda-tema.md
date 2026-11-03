# Correcciones de compositor, búsqueda inferior y modo claro

Cambios sobre la versión probada `544622070` de la rama
`codex/flexygram-beta-glass`, a partir de las capturas del propietario.

- El compositor compacto conserva su distribución y áreas táctiles. Adjuntos
  usa un círculo visual basado en 44 dp menos el inset de compactación, en lugar
  del tamaño completo de su View. Los límites del micrófono se alinean con el
  círculo de 44 dp que ya dibujaba su vista nativa.
- La entrada, adjuntos, micrófono y envío tienen drawables persistentes propios
  con límites y contornos independientes. Comparten la captura y el desenfoque
  existentes: no se crean motores, shaders ni bitmaps adicionales. Cada radio
  se actualiza sólo al cambiar de tamaño y las piezas no visibles se desactivan.
- Cuando el padre dibuja el envío, su vista evita la segunda pintura de fondo
  y utiliza un color de icono adecuado al tema. Las transiciones y controles
  especiales conservan la ruta nativa cuando no hay una pieza estable.
- Barra y búsqueda se centran juntas, con 8 dp entre ellas, a partir del ancho
  medido de la barra y los insets de la ventana. La colocación contempla RTL.
  Al ocultar la búsqueda se eliminan los desplazamientos adicionales.
- Modo claro: se reduce la capa blanca del compositor y la cabecera, y el borde
  inferior utiliza un color de contraste. El material Universal adapta también
  su contorno completo. Se mantiene la paleta oscura de la cabecera y se
  respetan el ahorro de energía y los controles de desactivación del blur.

Validación: prueba JVM de centrado, separación y contención de barra/búsqueda
para varios anchos, densidades, números de pestañas y ambas direcciones de texto;
comprobación de los diámetros de compactación; suite existente y sintaxis Java.
La compilación Android se inicia al publicar los cambios mediante el workflow
ARM64 existente. Las capturas no constituyen una medición posterior al cambio:
la comprobación visual en dispositivo sigue pendiente.

## Igualdad visual de adjuntos, micrófono y envío

El clip compacto conservaba sus 28 dp intrínsecos con `CENTER`, mientras el
micrófono animado se reducía al espacio interior de 24 dp con su padding nativo.
El clip pasa a `CENTER_INSIDE` con el mismo espacio interior; se conservan la
vista de 44 dp, sus gestos y el área táctil. El modo clásico recupera su centrado
y padding originales. La variante estática del micrófono mantiene sus 24 dp
nativos y deja de ampliar su contenedor de icono a 28 dp; los iconos de emoji
conservan su tamaño compacto anterior.

Los tres círculos y el radio del material comparten ahora el cálculo de diámetro
visual del compositor. El botón de envío y el micrófono de reserva usan la misma
función de geometría. Una prueba JVM ejecuta los getters reales de los tres
controles con nueve densidades, tres niveles de inset y tres tamaños de vista
nativa: todos producen círculos del mismo diámetro sin ampliar los controles.

Validación local de esta ampliación: 211 pruebas aprobadas y 31 omitidas,
sintaxis Java y diff correctos. Queda pendiente comparar el aspecto de los
iconos en dispositivo con el APK nuevo.
