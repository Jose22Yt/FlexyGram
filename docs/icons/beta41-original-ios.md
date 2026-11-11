# Beta 41 — originales de Telegram para iOS

Estado: cambios de código y recursos preparados en `codex/flexygram-beta-glass`, versión `1.0.0-beta.41`, build `1330`. No se ha compilado una APK ni solicitado un workflow de compilación.

## Procedencia y alcance

Se importa el material del [cliente oficial Telegram-iOS, revisión 24638bc69bd083981b178dd1e7f921eebbf7fc46](https://github.com/TelegramMessenger/Telegram-iOS/tree/24638bc69bd083981b178dd1e7f921eebbf7fc46): **235 recursos originales, 1.566 asociaciones con IDs Android, 30 roles de pestañas y 27 roles de vistas previas**. No son dibujos generados ni el conjunto Flutter Cupertino usado anteriormente.

La denominación «iOS 27» por sí sola no identifica todos los recursos de una versión concreta de Telegram. **Esta entrega no certifica un port completo de iOS 27.** Se aplica la revisión oficial indicada, con originales verificables. Quedan **483 asociaciones del catálogo anterior sin sustituir**, enumeradas en [coverage.json](../../tools/ios_originals/coverage.json). Conservan su recurso existente: no se les asigna arbitrariamente otro icono para anunciar una cobertura del 100 %. Incluyen acciones y estados especiales, formatos de texto, categorías de emoji y componentes propios de Android/FlexyGram que requieren una referencia exacta adicional por función.

[manifest.json](../../tools/ios_originals/manifest.json) registra archivo de origen, SHA-256, Git blob, dimensiones, conversión y archivos Android resultantes. Los originales se conservan sin modificar en `tools/ios_originals/upstream/`; el importador verifica sus blobs contra el árbol del commit oficial. Las correspondencias revisadas se mantienen explícitamente en [catalog.py](../../tools/ios_originals/catalog.py) y [aliases.py](../../tools/ios_originals/aliases.py).

## Cambios visibles

- Iconos por defecto para conversaciones, búsquedas, ajustes, llamadas, menús, edición multimedia y reproductor en los roles cubiertos por el catálogo.
- La opción antigua «Cupertino» se presenta como «Telegram iOS» y usa los mismos originales. Solar, Remix y los packs elegidos explícitamente conservan su selección.
- Sticker de esquina doblada al abrir el panel de la entrada de texto; teclado, micrófono y cámara mantienen sus estados propios.
- Flecha de navegación y cierre, acciones de burbujas, controles musicales y vistas previas usan el archivo oficial en lugar de dibujar trazos aproximados. Los roles de archivos de las vistas previas usan el documento genérico original cuando corresponde.
- Las pestañas cubiertas cargan los originales incluso si estaba disponible una animación Android anterior; no se modifica el indicador de selección ni el funcionamiento de sus acciones.
- La elipsis circular horizontal original se muestra sin la rotación de 90 grados que exigía el antiguo recurso Android.
- Se mantienen la portada circular, el progreso musical, el blur/glass, el tema y las áreas táctiles actuales. No se cambia el logotipo de la aplicación.

## Tamaño y representación

Las dimensiones originales son puntos lógicos, no un número fijo de píxeles para todos los teléfonos. Se trasladan a dp y a las densidades de Android. Por ejemplo: navegación/búsqueda/adjunto de 30 puntos, sticker y teclado animados de 32, micrófono/cámara de 30 y recursos grandes play/pause de 60. El propio archivo define su margen interior.

`OriginalIconDrawable` conserva tamaño y proporción dentro del control. No amplía ni deforma el símbolo para llenar un botón grande. Cuando un espacio existente es menor, lo ajusta proporcionalmente. Las áreas táctiles siguen siendo las de FlexyGram; por ello no se promete que cada símbolo ocupe idénticos píxeles físicos que en un iPhone.

Hay **105 conversiones de trazados PDF, 12 de SVG, 104 rasterizaciones directas de PDF, 9 recursos PNG y 5 estados finales originales Lottie**. La comprobación de alfa rechaza conservadoramente conversiones vectoriales inciertas; en ese caso se rasteriza directamente el original en cinco densidades. No se reconstruye su silueta a mano. Los PNG conservan el alfa y los vectores las curvas/reglas de relleno. Como plantillas, reciben el tinte del tema.

Los estados del composer se obtienen con rlottie de los JSON oficiales. Se conservan los JSON fuente, pero no se afirma haber portado todas las animaciones del cliente iOS: las transiciones de FlexyGram siguen usando su propio sistema de tiempos.

## Rendimiento

Los **674 archivos Android resultantes ocupan 952.054 bytes**, frente a **1.300.230 bytes** de las hojas anteriores, una reducción aproximada del 27 %. Las conversiones y dependencias Python son herramientas de preparación; no se ejecutan dentro de la APK.

Android comparte píxeles/geometría mediante su caché de recursos. Cada control tiene estado de tinte, alfa y límites independiente; los clones mantienen las dimensiones según densidad. El mapa se inicializa una vez y busca por ID mediante búsqueda binaria, compatible con recursos `R` no finales. Los IDs de los propios originales quedan fuera del mapa para terminar la carga sin recursión.

No se incorporan relojes de animación, conversión PDF/SVG, lectura de JSON ni decodificación de imágenes dentro de `draw()`. El cambio no constituye una medición de FPS ni una garantía de ausencia de lag en dispositivos.

## Validación antes de compilar

- Suite de regresión: **376 pruebas correctas y 39 omitidas** por corpus/dependencias no disponibles en el entorno.
- Pruebas específicas: integridad de fuentes y resultados, correspondencias semánticas, estados diferenciados, tintes/alfas independientes, caché, densidad, clonación, conservación de proporciones y ausencia de ampliación forzada.
- Verificación aislada de diez clases de producción contra **Android API 35 real y AndroidX Core 1.15.0**: correcta. Los servicios de Telegram son dobles explícitos; esta comprobación no sustituye el build completo con el SDK/API 37 y las dependencias fijadas por el proyecto.
- **AAPT2** acepta las variantes de recursos importados. Se validan recursos en un directorio temporal; no se enlaza ni empaqueta una APK.
- `python tools/ios_originals/generate.py --check` verifica hashes y generación reproducible del mapa y la cobertura.
- Pendiente: compilación completa posterior y comprobación visual en dispositivo, incluyendo claro/oscuro, RTL, cambio de tema/pack, controles de grabación y tamaños de pantalla. No se ha activado GitHub Actions para compilar esta entrega.
