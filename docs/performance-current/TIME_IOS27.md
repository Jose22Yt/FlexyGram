# Hora limpia y ticks predeterminados

Rama local: `share/flexygram-settings-motion-menus`. Sin APK ni publicación.

- `ChatMessageCell.drawReadableTimeLayout`: se retiró el ajuste añadido de color/halo y su Paint temporal. El degradado de burbujas salientes forzaba una superficie transparente para ese cálculo, activando una sombra que engrosaba la hora. Ahora el layout usa una sola pasada con el color y alpha nativos del tema, igual que el recorrido normal de la hora. No se cambia fuente, tamaño, coordenadas ni transición de hora/edición.
- `Theme.createChatResources`: los checks nativos de FlexyGram usan dos vectores de estilo iOS 27, de trazos redondeados. Conservan 12dp de tamaño intrínseco y el algoritmo de colocación de check/half-check. No se altera el cálculo de enviado/leído, animación, color seleccionado, transparencia ni reloj/error. El resto de variantes mantiene sus recursos existentes.
- `BubblePreviewView`: utiliza esos mismos recursos predeterminados.

Validación: nueve pruebas específicas aprobadas (hora/ticks, modos de vidrio/contraste y tarjetas de burbujas). Los métodos de producción de hora y la fábrica de checks se ejecutan con dobles explícitos. Se comprueban una sola pasada, ausencia de modificaciones de paint, diez asignaciones de checks, variantes seleccionadas/multimedia y fallback; también tamaño y atributos de ambos vectores. Los XML pasaron aapt2 compile sin generar APK. Sintaxis Java de ChatMessageCell, Theme y BubblePreviewView verificada con javac 21. `git diff --check` limpio.

No se ha ejecutado el cliente en dispositivo. Pendiente comprobar visualmente temas claros/oscuros, degradados, selección, enviado→leído, fotos/stickers y vista previa. Los vectores son una interpretación del estilo solicitado, no recursos extraídos del sistema iOS.
