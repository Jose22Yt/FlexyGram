# Optimización de trabajo durante scroll y navegación

Se revisaron las rutas de mensajes, lista principal y carpetas, cabecera, efectos compartidos, ajustes y arranque de la beta. Se conservan las mejoras anteriores de carga anticipada de diálogos locales y servicios auxiliares pospuestos. Esta revisión no añade tareas antes de presentar la interfaz ni modifica los datos de sesión/historial.

## Cambios aplicados

- `BlurredBackgroundDrawable`: los setters de radios, grosor e intensidad omiten reconstrucciones cuando los valores que controla cada API son idénticos. La geometría de esquinas visible y la geometría del shader conservan sus reglas nativas, incluida la variante con esquinas inferiores a cero. Los cambios reales de tamaño, estilo y radio siguen actualizándose.
- `BlurredBackgroundSourceRenderNode`: se reutiliza el efecto de blur cuando radio y efecto de entrada no cambian. El radio cero utiliza el efecto de entrada directamente o limpia el efecto. Esto evita recrear cadenas equivalentes y evita construir un blur de radio cero.
- `BlurredBackgroundDrawableRenderNode`: se conserva el filtro de sombra mientras color, radio y desplazamiento sean iguales. Los cambios de opacidad, tema o parámetros lo actualizan; la geometría continúa dibujándose con los bounds actuales.
- `RenderNodeWithHash`: las invalidaciones explícitas usan versiones. Un hash cero ya no puede hacer que se ignore una invalidación. Se respetan cambios de tamaño, pérdida de display list e invalidaciones durante la grabación. Se finaliza la grabación incluso si el renderer falla y se deja pendiente el siguiente intento. Los renderers sin hash continúan actualizando su contenido.
- Cabecera Signature: los cambios de 100 a 101, etc., conservan el contador real pero reutilizan la misma etiqueta «99+», sin crear otro StaticLayout ni solicitar otro layout. El contraste blanco/negro se recalcula al cambiar el acento; una actualización del contador restaura el color correcto después de copiar la pintura compartida.
- Ajustes: caché de resolución de iconos limitada a 128 entradas, separada por identidad de Resources. Los recursos desconocidos conservan su identidad y los IDs todavía ausentes pueden resolverse cuando estén disponibles. Los filtros de color siguen actualizándose con el tema.
- Conversaciones: la comprobación de traducción deduplica álbumes mediante un HashSet, evitando búsquedas lineales repetidas. Se conservan todos los miembros del álbum, los mensajes ordinarios y las mismas reglas de visibilidad/prefetch. Al destruir la conversación se cancela la comprobación diferida pendiente.

Los cambios del motor compartido se aplican a las superficies que lo utilizan al desplazar mensajes/listas o durante transiciones, sin cambiar la física del fling, los tiempos de animación ni forzar modos de pantalla.

## Verificación en este entorno

Con JDK 21 en PATH, `python -m pytest tests/ -q -p no:cacheprovider`: **240 aprobadas, 31 omitidas**.

Seis pruebas nuevas ejecutan código de producción para geometría, display lists, blur/sombras, caché de recursos, contador y álbumes. Como comprobación de trabajo, 20.000 llamadas con radios, efectos o sombras idénticos producen una sola actualización inicial; 20.000 resoluciones del mismo icono en la misma tabla consultan su nombre una vez. También se verifican cambios reales, hashes cero, reentrada, fallo de grabación, cambio de Resources y actualización posterior de un ID ausente. Estos son contadores de trabajo con dobles, no mediciones de latencia del dispositivo.

Se verificaron la sintaxis Java y `git diff --check`. La caché de RenderNode, la fuente nativa de blur, los hashes y la caché de iconos compilaron contra Android API 37 con dependencias mínimas de aplicación. Las pruebas previas mantienen el contraste, la clasificación de mini píldoras, tamaños del compositor, navegación, ajustes y conservación de mensajes.

## Entrega

Publicación con `[skip actions]`; no se inicia la compilación de APK. No se generan resultados de FPS ni se afirma ausencia de jank sin una medición Android real.

La siguiente comprobación con la APK debe cubrir conversaciones largas con medios/álbumes, desplazamiento rápido de chats y carpetas, entrada/salida con gestos, contador superior a 99, teclado y cambios de claro/oscuro y estilo de borde/blur. La compilación Android completa y la verificación visual siguen pendientes.
