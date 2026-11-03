# Barra inferior adaptable y búsqueda

Correcciones sobre la beta de FlexyGram del 3 de noviembre de 2026:

- El dock flotante adapta su ancho proporcionalmente al número de pestañas activas, tomando cuatro como referencia y respetando el ancho disponible y el espacio mínimo de cada pestaña. La vista previa también adapta su ancho. La barra anclada conserva su ancho completo.
- Se permite retirar cualquier pestaña, incluida Chats y la última. Una selección vacía se conserva al reiniciar y oculta la barra. Las pantallas montadas recalculan sus espacios inferiores al recibir los insets; las pestañas independientes de Estadísticas conservan su altura.
- El indicador de selección mantiene extremos redondeados aunque el fondo de la barra anclada sea rectangular.
- Activar la búsqueda inferior conserva la preferencia explícita de mostrar los nombres de las pestañas. El espacio de la búsqueda se reserva antes de medir y el conjunto se centra; una búsqueda sin otras pestañas no deja una separación vacía.
- La búsqueda inferior selecciona primero la página Chats y utiliza la acción nativa de búsqueda, con su mismo estado de apertura y cierre. Se cancela cualquier cambio de página programático pendiente. La solicitud diferida de teclado comprueba que la búsqueda siga abierta, para evitar reabrirlo tras Atrás.

No se agregaron controles nuevos. El cálculo del ancho no crea objetos ni inicia animaciones recurrentes.

## Validación

`python -m pytest tests/ -q -p no:cacheprovider`: **217 aprobadas, 31 omitidas**. Las pruebas nuevas ejecutan las clases Java reales de configuración, destinos y cálculo de ancho con preferencias en memoria: selección vacía persistente, pestañas individuales, búsqueda separada, etiquetas y límites de ancho. También se revisaron la sintaxis Java de los archivos modificados y `git diff --check`.

Estas comprobaciones no sustituyen una prueba visual y de gestos en Android. Se debe comprobar en la APK el cambio entre 0–6 pestañas, los tres niveles de compacidad, dock flotante y anclado, orientación/RTL, búsqueda desde cada pantalla y cierre con Atrás antes y después de aparecer el teclado.
