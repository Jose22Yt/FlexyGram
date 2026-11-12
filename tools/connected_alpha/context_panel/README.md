# Panel contextual compacto

Pruebas y referencias de la integración histórica del menú contextual de mensajes.
La base de referencia es la revisión `e00b33e806921017ad74ff50eb5ec88607131d9c`.

El panel reutiliza la selección de acciones, permisos y reacciones nativos. La geometría
compacta debe respetar texto largo, RTL, tamaño de fuente, límites de pantalla y controles
táctiles. Los enlaces, medios, spoilers y otros elementos interactivos conservan su
prioridad frente al gesto que abre el menú.

Los fixtures de esta carpeta verifican políticas y presentación de esa revisión; su
resultado no sustituye una compilación integrada ni la aceptación en dispositivo.
