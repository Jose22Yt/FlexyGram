# Selectores compactos de interfaz y burbujas

Una vista previa principal y una cuadrícula de miniaturas con nombre sustituyen las galerías verticales de diseños completos. Interfaz inferior conserva sus dos estilos e Interfaz superior sus cinco estilos. La cuadrícula adapta columnas al ancho y al tamaño de fuente, respeta RTL y expone cada tarjeta como opción de radio accesible. Solo la vista previa principal observa y prepara el fondo: las miniaturas no cargan wallpapers ni ejecutan animaciones.

Burbujas ofrece Telegram, FlexyGram y Telegram para iPhone. La forma es independiente del material. Personalizar burbujas despliega debajo los controles existentes de superficie, transparencia, blur, bordes y fusión. Todos los estilos admiten estos controles. La búsqueda expande el grupo necesario, se conserva su estado y las vistas recicladas vuelven a conectarse a su controlador.

## Geometría de Telegram para iPhone

Fuente oficial: [ChatMessageBubbleImages.swift](https://github.com/TelegramMessenger/Telegram-iOS/blob/24638bc69bd083981b178dd1e7f921eebbf7fc46/submodules/TelegramPresentationData/Sources/ChatMessageBubbleImages.swift), commit `24638bc69bd083981b178dd1e7f921eebbf7fc46`. Se conserva una copia y su SHA-256 en `tools/ios_bubbles`.

El port usa el cuerpo de 33 puntos, la columna del pico de 6 puntos, las curvas cuadráticas originales, el recorte elíptico y los puntos de estiramiento originales (18,19) sobre la plantilla de 43×37. Los radios predeterminados 16/8 proceden de PresentationChatBubbleSettings. Los mensajes recibidos reflejan el contorno completo; los agrupados reducen las esquinas correspondientes y omiten el pico. Los medios conservan sus clips y layouts nativos.

La forma se almacena por caché de geometría de celda. Traslaciones conservan la geometría: no repiten las operaciones booleanas del contorno. Cambiar de perfil invalida también la caché de dibujo y el borde parcial, incluso si coincide el radio. No se añaden tareas de animación ni lectura de preferencias durante el dibujo.

Se copia la definición oficial de la geometría; no se afirma una comparación píxel a píxel con una app instalada en iOS 27. CoreGraphics y Skia pueden diferir en antialiasing, y los temas, texto y medios siguen perteneciendo al cliente Android. Las personalizaciones elegidas modifican expresamente el acabado.

## Compatibilidad y validación

La migración conserva la apariencia anterior: sin forma explícita, superficie nativa mantiene Telegram y los modos anteriores mantienen FlexyGram. Las preferencias antiguas desactivadas siguen inactivas. La forma se congela al cambiar el material, se exporta en FlexyStudio y no altera el radio guardado de Telegram.

Se ejecutaron la suite general, regresiones puntuales de los fixtures actualizados y las pruebas de integración de los ajustes compactos. Cinco pruebas Robolectric/API35 con gráficos nativos verifican cambio de perfil y vuelta limpia, simetría, personalización independiente, geometría y accesibilidad de las tarjetas y comparación de máscaras con los comandos originales a escala 3×. Las diferencias permitidas en el contorno corresponden a antialiasing; esta comprobación no sustituye probar la app completa en teléfono.

No se compila una APK, no se incrementa la versión de distribución y los commits usan `[skip ci]`.

Resultados: 419 casos de la suite base verificados entre la ejecución general y la regresión puntual corregida, 39 omitidos; 31 pruebas de integración tras incorporar la última consolidación de ajustes; 5 pruebas de gráficos nativos. Sintaxis verificada en 14 archivos Java y XML válidos en los tres idiomas.
