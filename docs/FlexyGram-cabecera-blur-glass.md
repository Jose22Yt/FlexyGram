# Blur y glass de la cabecera del chat

La cabecera y el panel de mensaje fijado usaban un proveedor de color distinto al de la entrada de mensajes. En modo claro, el tinte superior mantenía un alfa de 193 (blur) o 216 (glass), mientras que la entrada usaba 140. Esa capa más opaca hacía mucho menos visible el fondo superior, aunque ya estuviera conectado al motor de efectos.

`ChatGlassColorProvider` reúne la política que ya usaba la entrada y ahora se aplica también a la cabecera y al mensaje fijado. Cada superficie conserva su clave de color del tema. Todas siguen usando los drawables, contornos, fuentes compartidas y cambios de modo del motor nativo; no hay nuevas capturas, bitmaps ni animadores.

El proveedor respeta el interruptor de efectos y las excepciones de modo claro/oscuro de la cuenta a la que pertenece el chat. Cuando no se permite blur, devuelve un fondo opaco. En modo oscuro conserva los valores anteriores de la entrada. El callback de cambio de tema actualiza también el proveedor superior antes de repintar los drawables.

No se modifican geometría, iconos, foto, nombre, estado del contacto, contador ni zonas táctiles. Los cambios recientes de la beta 12 se conservan.

## Verificación

`tests/test_chat_header_material.py` ejecuta los proveedores de producción junto con la condición nativa de activación. Cubre temas claros y oscuros, tintes personalizados, cuenta distinta a la seleccionada, efectos activados/desactivados, cambios entre blur y glass y actualización de los proveedores retenidos.

En dispositivo, comprobar cada estilo de cabecera con un fondo fotográfico contrastado, desplazando mensajes y mostrando/ocultando el mensaje fijado. Repetir en ambos temas y cambiar los efectos sin cerrar el chat. Verificar especialmente el contraste de texto e iconos y que el fondo opaco se restaura al desactivar efectos. La revisión visual y la medición de frames requieren un dispositivo; las pruebas JVM no las sustituyen.

No se generó una APK para esta corrección.
