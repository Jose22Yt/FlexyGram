# Burbujas adaptativas al fondo

El selector **Ajustes → Chat → Burbujas de chat → Efecto de burbuja** ofrece:

- **Adaptativo del fondo**, predeterminado: reutiliza el material nativo de los avisos de servicio. No tiene controles adicionales.
- **Efecto anterior**: conserva transparencia, desenfoque, contorno y fusión con los valores guardados anteriormente.

`ServiceBubbleSurface` dibuja el shader y los filtros existentes del proveedor de tema de cada chat, sobre la geometría original de `MessageDrawable`. También usa la capa de oscurecimiento y el estado seleccionado nativos. No extrae colores ni crea otro bitmap de desenfoque. El proveedor conserva la propiedad de sus pinturas; un `Paint` reutilizable compone el alfa sin modificarlas.

`ChatMessageCell.applyServiceShaderMatrix()` aporta las coordenadas nativas, incluidos los desplazamientos de teclado y separadores. Los fondos con shader usan el pase del padre para evitar fijar el muestreo al RenderNode de una fila durante el scroll. El modo adaptativo omite el tinte, el gradiente saliente y los bordes anteriores. Cuando el material nativo no dispone de shader, conserva su alternativa sólida.

El texto usa la tinta de servicio. La hora conserva el color nativo de los mensajes recibidos del tema del chat, tanto en modo claro como oscuro y al seleccionar la burbuja; no adopta el blanco de servicio ni el acento saliente. La vista previa sigue la misma política. Los ticks conservan forma y posición; sus copias locales se reutilizan y cambian de color sin modificar los drawables compartidos. Las imágenes, los stickers sin fondo, los indicadores de error y los controles de selección mantienen sus rutas de dibujo.

La preferencia `flexygram_bubbles/surface_effect` se incluye en FlexyStudio. El modo adaptativo impide preparar la caché de blur anterior, pero conserva esa preferencia para volver al efecto anterior.

## Verificación

Pruebas ejecutables: `tests/test_adaptive_bubbles.py`, `tests/test_bubble_settings_cards.py`, `tests/test_bubble_time_ticks.py` y `tests/test_signature_settings3.py`. Cubren valores predeterminados, persistencia, cambio de modo, controles ocultos, capas nativas, selección, alfa, fallback y aislamiento/reutilización de los ticks. Estas pruebas usan dobles explícitos para las API de dibujo; no sustituyen la revisión de píxeles en Android.

Comprobar en dispositivo antes de publicar una beta:

1. Probar modo claro y oscuro con fondo fotográfico, degradado animado y color sólido; comparar las burbujas con el aviso nativo del mismo chat.
2. Probar temas y fondos específicos de conversación, cambiar de tema y volver a abrir el chat.
3. Desplazar mensajes entrantes y salientes, incluidos álbumes, respuestas, audio, archivos y pies de foto; vigilar alineación del fondo, contraste y recortes.
4. Abrir/cerrar teclado, desplegar paneles, girar la pantalla y comprobar chats con temas o mensajes con estrellas.
5. Seleccionar mensajes, mantener pulsado, enviar y leer mensajes; comprobar horas y transiciones de ticks sin halos ni cambios de posición.
6. Cambiar al efecto anterior y volver al adaptativo; exportar/importar con FlexyStudio y verificar la selección y los valores anteriores.
7. Medir scroll y apertura con FrameTimeline/Perfetto a 60 y 120 Hz. No se afirma una mejora de FPS sin esta medición.

Este cambio no requiere modificar el fondo ni recompilar recursos gráficos. No se generó APK durante el desarrollo.
