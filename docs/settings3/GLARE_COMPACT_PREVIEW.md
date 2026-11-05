# Muestra compacta de efectos de brillo

Se añade una sola fila de vista previa de **64dp** bajo el encabezado de efectos y antes de «Tipo». Solo contiene círculo, píldora y tarjeta neutros en una línea. No hay textos, iconos, botones ni una tarjeta de presentación grande. El segmento usa márgenes laterales de 12dp, radio exterior de 28dp y borde visible de 2dp; su interior muestra el wallpaper/color activo.

`GlarePreviewView` dibuja las tres superficies con `BlurredBackgroundColorProviderThemed` y llama a `BlurredBackgroundDrawable.drawStroke`, el renderer existente que interpreta GlassOutlineStyle. No se reimplementa un motor de brillo. La muestra representa el contorno sobre una superficie de color translúcido; no captura otra pantalla ni añade un motor de blur para el fondo de las formas.

La vista se registra como listener débil del modo de contorno y se invalida al cambiar el tipo; no inicia un reloj ni animación permanente. Utiliza SignatureWallpaperPreview para representar fondos activos, con sus copias acotadas de fondos animados; retira los observadores de tema/wallpaper y cancela el trabajo al separarse. Las geometrías se preparan al cambiar tamaño. El dibujo no crea objetos Java por frame ni mide texto.

La fila tiene tipo propio, queda fuera de las secciones de controles para no duplicar fondos y no es interactiva. «Tipo» conserva el mismo diálogo, valor guardado y notificación dirigida a su fila. Funciona también en la página combinada de ajustes de chat.

Validación: **11 pruebas aprobadas** (muestra nueva, efectos existentes, segmentos y propiedad de imágenes). La prueba ejecuta los métodos reales de medición/geometría con dobles Android en 16 combinaciones de densidad/ancho; comprueba altura, contención y separación. La muestra, sección y política se compilaron contra Android API37 con servicios del proyecto sustituidos por dobles. No es una compilación integrada ni una prueba de píxeles Android. `git diff --check` limpio.

Sin APK ni publicación. Pendiente verificación visual en dispositivo: claro/oscuro, los tres modos, cambio de wallpaper/color, volver a abrir y cerrar ajustes durante la preparación de fondo.
