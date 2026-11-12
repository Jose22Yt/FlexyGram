# Mini píldoras: clasificación e iconos

Se corrige la clasificación de la lista principal conservando los modos Adaptativo, Multicolor, Matte y Desactivadas.

## Cambios

- Solo un `TL_messageMediaDocument` real puede clasificarse como archivo, PDF, audio, vídeo o sticker. Las fotos utilizan su tipo de medio directo. Los métodos auxiliares de Telegram también inspeccionan documentos/fotos de páginas web: esos resultados ya no convierten una vista previa web en un adjunto.
- Las notas de vídeo se reconocen antes de documentos genéricos. Todos los tipos de sticker se evalúan antes de vídeo, y GIF antes de vídeo. Las notas de voz se identifican por sus metadatos nativos, sin suponer que cualquier OGG es voz.
- Se normalizan MIME con mayúsculas, espacios y parámetros. Se amplía la cobertura de imágenes, audio, vídeo, archivos comprimidos y documentos de oficina. Un MIME específico tiene prioridad sobre una extensión contradictoria; las extensiones Office/APK distinguen esos formatos dentro de contenedores ZIP. Un adjunto real desconocido mantiene el tipo Archivo.
- Los enlaces usan entidades URL de Telegram y los datos de la página web, incluidos enlaces ocultos y dominios sin esquema confirmados por Telegram. Un nombre de archivo mencionado en texto no basta para crear una píldora de archivo o enlace. Los offsets se validan como índices UTF-16. La etiqueta muestra el dominio y omite credenciales, rutas y parámetros.
- Los mensajes conservados como eliminados tienen prioridad de estado y conservan un resumen del texto. Administrador y propietario siguen requiriendo datos locales confirmados de participantes; no se deducen de palabras del mensaje, firmas o publicaciones anónimas.
- Los medios no soportados, mensajes restringidos, contenido efímero, spoilers y resultados resaltados conservan las rutas nativas existentes.
- Se añaden trazados propios para PDF con marca PDF, texto, GIF, sticker, encuesta, fijado, edición, canal, administrador, propietario, eliminado, entradas/salidas, APK, hoja de cálculo, presentación y documento. Las 27 geometrías se crean una sola vez y se reutilizan con los colores actuales. No se añaden bitmaps, fuentes ni bibliotecas.
- Los iconos de las píldoras pasan de 12 a 14 dp, manteniendo la altura de 20 dp. Si falta espacio para una píldora legible se conserva la presentación nativa. El modo Matte exige al menos 3:1 de contraste para iconos, y el texto mantiene 4.5:1.
- Los nombres largos mantienen su extensión sin partir pares Unicode de emojis; voz, vídeo y enlaces no utilizan el recorte intermedio de los nombres de archivo. La vista previa de ajustes incluye una muestra de PDF y ajusta sus filas.
- Se elimina un cálculo de estado secundario que no se dibujaba en la fila y repetía la consulta local del rol.

## Validación

`python3 -m pytest tests/ -q -p no:cacheprovider` (con JDK 21 en `PATH`): **234 aprobadas, 31 omitidas**.

Las pruebas nuevas ejecutan el clasificador, las etiquetas y la paleta reales con metadatos de Telegram simulados. Cubren documentos embebidos en páginas web, texto ordinario, MIME/extensiones contradictorios, voz/música, notas de vídeo, stickers animados, GIF, metadatos incompletos, roles, eventos, mensajes conservados como eliminados, protecciones de contenido, offsets URL, nombres Unicode, contraste y reutilización de todas las geometrías de iconos.

Los iconos, el span, la paleta y la vista previa de ajustes también compilaron contra Android API 37 con dependencias de aplicación mínimas. Sintaxis Java y `git diff --check` correctos. No se consultan bases de datos, decodifican archivos ni realizan peticiones de red para identificar las píldoras; la clasificación se realiza al preparar la fila, no en cada frame.

Se publica con `[skip actions]`, sin iniciar la compilación de APK. Estas comprobaciones no sustituyen la compilación Android completa ni la revisión visual en el dispositivo. La clasificación usa metadatos disponibles y no puede verificar el contenido binario de archivos con metadatos incorrectos.
