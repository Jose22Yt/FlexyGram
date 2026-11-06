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
