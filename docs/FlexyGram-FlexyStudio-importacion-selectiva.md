# FlexyStudio: comparación e importación por secciones

Al abrir un archivo `.flexygram` desde una conversación o desde el selector de FlexyStudio, el cliente valida el documento y compara su contenido con los ajustes actuales antes de mostrar «Aplicar».

La hoja agrupa los cambios en burbujas, cabecera, entrada de mensajes, pantalla principal, apariencia, navegación, ajustes generales, chat/menús, plugins, IA, tema/fondo e icono, según el contenido real del archivo. Solo aparecen grupos incluidos. Los grupos que ya coinciden no se pueden seleccionar. Cada grupo permite consultar los valores actuales y los del archivo; los cambios se muestran en páginas de 20 para no construir una vista enorme. El tema y el fondo se tratan como un conjunto. Por defecto quedan marcados los grupos que cambian algo; se pueden desmarcar todos y «Aplicar» queda desactivado.

La comparación no escribe preferencias. Seleccionar un grupo aplica únicamente sus cambios. El registro de recuperación y «Deshacer» conservan el mismo alcance: no restauran secciones excluidas ni rechazan el deshacer por cambios posteriores en ellas. Sí detectan modificaciones posteriores en los ajustes importados.

## Correcciones de transferencia

- Los nombres de acciones de los menús personalizados se exportan como conjuntos de texto. Antes se intentaban convertir a números y fallaba la preparación del archivo.
- El exportador valida el paquete preparado antes de ofrecer guardarlo o compartirlo y distingue los errores de preparación de los de escritura.
- Un fallo de validación o comparación ya no publica un resultado parcialmente preparado en la interfaz de importación.
- El almacenamiento SAF reintenta con modo `w` si el proveedor no admite `wt` o devuelve un stream nulo en ese modo.
- La intención de compartir usa el MIME propio de FlexyStudio y conserva los permisos temporales de lectura y ClipData.
- El filtro existente de apertura también reconoce la extensión en minúsculas `.flexygram`, además de `.flexyGram`, sin añadir permisos de almacenamiento ni capturar documentos genéricos.
- Comparación, aplicación, recuperación y deshacer utilizan el ejecutor acotado de Studio. No bloquean las colas globales de dibujo o mensajería.

Las copias completas mantienen su formato. Los subconjuntos usados al aplicar y recuperar se construyen internamente después de validar el archivo; las claves siguen saliendo del catálogo permitido. No se importan preferencias arbitrarias, sesiones, credenciales ni código.

## Verificación

`tests/test_studio_import.py` ejecuta el catálogo, codec, copia completa, conjuntos de texto, selección y transacciones de producción con dobles explícitos de persistencia y tema. Incluye una comprobación de tipos de las clases de Studio contra Android API 37 y pruebas del fallback de escritura SAF y del filtro de extensión. `tools/connected_alpha/test_flexystudio.py` cubre el codec, archivos alterados, recursos y permisos.

Pendiente en dispositivo: guardar mediante distintos proveedores de documentos, compartir con otra aplicación, abrir el archivo recibido, seleccionar secciones, comprobar el antes/después y deshacer tras modificar una sección excluida. Revisar ambos temas, fuentes grandes y la navegación entre páginas de cambios. No se generó ninguna APK durante este trabajo.

## Selección por ajuste desde un archivo en el chat

El toque sobre un `.flexygram` sigue la ruta nativa `handleMessageTap` → lectura/validación en StudioIO → comparación sin escrituras → hoja de importación. La hoja muestra las secciones presentes y permite desplegar «Ver cambios» para marcar cada ajuste, con su valor actual y el que viene en el archivo. Las casillas de sección seleccionan o deseleccionan su contenido completo; un contador muestra cuántos ajustes están incluidos incluso cuando la selección es parcial. Se crean como máximo veinte filas de detalle por página y por sección abierta.

Cada cambio tiene una identidad que distingue sección, archivo de preferencias y clave. Solo los cambios seleccionados se incluyen en el preset transaccional; desmarcar una clave conserva su valor actual aunque se importen otras claves de la misma sección. La selección se copia antes de enviarse al trabajador. Una selección vacía o desconocida se rechaza antes de aplicar.

«Tema y fondo» queda desmarcado inicialmente. No se llama a la aplicación del tema si no se incluye ese cambio. La hoja obtiene sus colores del proveedor del tema activo; los ajustes importados conservan sus rutas nativas de renderizado. Marcar el tema permite sustituirlo de forma explícita. No se promete convertir valores incompatibles: la validación existente de formato, claves, tipos y versión sigue siendo obligatoria.

Pruebas añadidas al harness de cliente: selección de una sola clave en una sección, conservación de otra clave de esa misma sección, conservación de ajustes de otras secciones, ausencia de llamadas de aplicación del tema al excluirlo, tema como selección independiente, entradas vacías/desconocidas rechazadas y selección individual en formato antiguo. Se comprueba también undo limitado a las claves aplicadas. Persistencia de Android y aplicación del tema están duplicadas explícitamente en ese harness.

Verificación ejecutada: las nueve pruebas de `tests/test_studio_import.py` y `tools/connected_alpha/test_flexystudio.py` pasan, incluida la comprobación de tipos de Studio contra Android API37. Se añadió una prueba de interacción de casillas en el harness nativo aislado, pendiente de ejecución. No se construyó una APK ni se ejecutó en dispositivo.
