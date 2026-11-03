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
