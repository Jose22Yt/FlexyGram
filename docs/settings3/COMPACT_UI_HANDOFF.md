# Entrega de segmentos, entrada de grupos y muestra de brillo

Actualización posterior a beta 6: la muestra de brillo y los modos Doble/Adaptativo fueron retirados; véase [restauración de brillo](GLARE_RESTORED.md). El resto de esta entrega se conserva.

Rama de entrega: `codex/flexygram-compact-segments-glare-20261105`.
Base: `b55bf39c7617253f2e4987010743c0069f17cb71`, publicada previamente en `share/flexygram-settings-motion-menus`.

El commit de esta entrega reúne los cambios posteriores a esa base:

- Selector nativo de identidad dentro de la píldora compacta en grupos, con espacio reservado para el texto y aparición por alpha.
- Posición inferior ampliada a −160…16 dp, reserva no negativa y rango compatible en FlexyStudio.
- Galerías inferior y superior verticales, previews a todo el ancho sobre el fondo activo, sin franja de nombre y con borde seleccionado de acento.
- Muestra de brillo de 64dp con círculo, píldora y tarjeta; utiliza el contorno nativo y el fondo activo, sin controles extra ni animación permanente.

Verificaciones realizadas durante el desarrollo: 8 pruebas del selector/composer; 16 pruebas y 9 subtests de posición/Studio/composer; 26 de segmentos y vistas previas; 11 de muestra de brillo/contornos/fondos. Los grupos se solapan y no se deben sumar como pruebas únicas. Se comprobó compilación aislada contra Android API37 con servicios sustituidos por dobles y sintaxis Java. Estas comprobaciones no son una compilación integrada ni validación visual en teléfono.

No se compila en la publicación, no se genera APK ni se modifica otra rama. El commit usa `[skip actions]`. La integración en `codex/flexygram-beta-glass` queda pendiente del integrador: comprobar que el destino contiene la base y dependencias antes de aplicar el commit. No se ha hecho merge ni cherry-pick sobre esa rama.

Informes: `GROUP_COMPOSER_SENDER.md`, `COMPOSER_VERTICAL_RANGE.md`, `VERTICAL_STYLE_SEGMENTS.md`, `GLARE_RESTORED.md` en esta misma carpeta. Pendiente aceptación en dispositivo (tema/fondo, teclado, texto largo, selector/popup, scroll, accesibilidad y modos de brillo).
