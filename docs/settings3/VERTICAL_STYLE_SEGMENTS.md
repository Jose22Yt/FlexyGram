# Galerías verticales con fondo activo

La elección de interfaz inferior y superior usa segmentos agrupados a todo el ancho, con separación de 4dp y radios exteriores de 28dp/interiores de 6dp. Se elimina la galería horizontal de cabeceras y su desplazamiento inicial automático. Se conserva el orden de estilos, sus identificadores y setters existentes; tocar una opción aplica el estilo y actualiza la selección.

`StylePreviewCard` contiene únicamente la vista previa con margen interior de 2dp y recorte redondeado. Desaparece la franja de texto bajo la imagen. El borde seleccionado usa el acento del tema; el nombre sigue disponible en accesibilidad y como tooltip en Android 26+. Los cinco estilos superiores y los dos inferiores usan el mismo contenedor.

Cada renderer sigue dibujando el fondo actual mediante SignatureWallpaperPreview y sus observadores existentes de tema/wallpaper. Se conserva su congelación acotada de fondos animados y cancelación al separar vistas, sin un reloj de animación nuevo. Un fondo sólido se representa mediante su drawable de color. No se añade una captura de conversaciones reales ni se reemplaza el wallpaper por una imagen fija.

Los previews inferiores conservan altura de 64dp. En la galería superior, el espacio extra alrededor del diseño baja de 40 a 12dp; Floating conserva el espacio necesario para mostrar la píldora de estado separada, por lo que su altura puede ser mayor. No se cambia la geometría de las cabeceras de conversación reales. Los controles de distribución permanecen bajo las dos opciones inferiores.

Validación: 24 pruebas existentes aprobadas sobre galería, cabeceras, fondos, medición, rango vertical y selector de grupo; dos pruebas nuevas aprobadas de geometría del segmento y conexión vertical/selección/observadores (26 en total). La nueva prueba ejecuta los métodos reales de recorte con dobles Android sobre densidades y bordes de agrupación, incluyendo tamaño cero. La galería, tarjeta y renderizadores reales compilan contra Android API37 con servicios del proyecto sustituidos por dobles. `git diff --check` limpio.

Sin APK ni publicación. Pendiente revisar en dispositivo claros/oscuros, cambio de wallpaper/color, fuente grande, TalkBack, tooltip y pulsación para aplicar cada diseño. Las pruebas host y compilación aislada no equivalen a una captura o una ejecución integrada del cliente.
