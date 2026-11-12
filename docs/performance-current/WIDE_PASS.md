# Revisión ampliada de fluidez

Base: `41ec915549ddeea4bbe53eb6ade6d20114b1dc4b`; rama local `share/flexygram-settings-motion-menus`. Conserva la intervención anterior de listas y ajustes. Sin APK ni publicación.

## Cobertura y evidencia

Se inspeccionaron listas y transiciones de conversación, ajustes y búsqueda, galerías/cabeceras, entrada de texto, etiquetas de lista, efectos de borrado, fondos/blur, editor de archivos y tareas de Studio. Se ejecutan pruebas host del código real con dobles explícitos cuando depende de Android. No es una ejecución funcional de todas las pantallas ni una medición de rendimiento físico del cliente completo.

ADB vuelve a mostrar cero dispositivos conectados. No se dispone de FPS, GPU, PSS, FrameTimeline ni latencia input→presentación. Los siguientes números cuentan operaciones en escenarios controlados, no milisegundos ni velocidad global.

## Cambios aplicados

| Zona / archivo y método | Coste encontrado | Cambio | Prueba y riesgo que vigilar |
| --- | --- | --- | --- |
| Lista principal, DialogsActivity.checkUi_filterTabsVisible/createView | Alpha de búsqueda provocaba requestLayout sin cambio de reserva de espacio | Separar factor visual del factor geométrico; reiniciar al recrear vistas | Búsqueda/reversa de 120 pasos sin solicitudes adicionales después de inicializar. Mantiene layout si cambia filtro o panel lateral. Revisar offsets al interrumpir búsqueda. |
| Ajustes, Settings2Cell.bindIcon/updateCard/updateForeground | Nuevos drawables por bind y textos desactualizados con tema | Reutilización por fila, invalidación por Resources/Configuration y actualización de colores | 10.000 actualizaciones estables sin reconstruir recursos. Revisar ripple y agrupación. Ver SETTINGS_ROW_REUSE.md. |
| Lista principal, SignatureSmartPillSpan.getSize | Misma etiqueta medida/recortada repetidamente | Cachear resultado por tamaño efectivo de texto, densidad e identidad de la fuente; contenido/presupuesto/documento son inmutables por instancia | 1.000 consultas posteriores sin measureText/ellipsize extra; resultado coincide con instancia fresca tras cambiar tamaño/densidad/fuente; mantiene métricas nativas. Vigilar fuentes grandes, nombres de archivo y truncado. |
| Cabecera, HeaderPreviewView.onMeasure/prepareClassicText/drawClassic | ellipsize y conversión a String dentro del dibujo clásico | Preparar los dos textos al medir; dibujar los resultados retenidos | 1.000 dibujos producen 2.000 textos con solo dos llamadas iniciales de recorte; soporta ancho cero y RTL. Revisar recorte tras cambiar tamaño/configuración. |
| Burbujas, BubblePreviewView.onMeasure/refreshTheme/onConfigurationChanged | Cuatro StaticLayout por medición aunque no cambie nada | Reutilizar geometría y layouts por ancho/densidad; invalidar al refrescar tema/configuración | Primera medición crea cuatro layouts; 1.000 repeticiones no crean otros. Cambio de ancho/densidad/tema recalcula; compara geometría con instancia fresca. Revisar cambio de fuente, tema y rotación. |
| Borrado, DeleteMotionOverlay.drawCrystal/drawVortex/drawTnt | Repetía fade y setAlpha idénticos por cada pieza | Preparar alpha una vez antes de recorrer piezas, restaurar 255 después | Tres estilos × 101 progresos y 32 piezas: todas las piezas conservan alpha esperado, dos setters por frame frente a 33; fade una vez frente a 32 fuera de la fase inicial. No cambia captura ni partículas. Revisar composición real con varios overlays. |
| Archivos, FlexyFileEditorActivity.load/LoadedContent | Lectura en worker pero decodificación, detección de texto/binario y escaneo de líneas en UI | Construir resultado de bytes + texto en el mismo worker cancellable; callback UI solo aplica contenido | Ejecuta load real con dispatcher de prueba en un thread, SelectedDocument real y archivos temporales UTF-8, UTF-16 con BOM, binario, encoding inválido y límite de texto; conserva bytes y roundtrip de texto. Revisar cancelar/cerrar/reabrir durante carga. |

## Decisiones sobre el hilo principal

La decodificación de documentos sale de UI sin añadir colas ni dependencias. Las vistas y Editable se siguen modificando en UI. No se mueve View.draw a un worker ni se hacen operaciones sobre vistas desde otro hilo. El resultado de carga no retiene la Activity; el mecanismo existente de publicación comprueba generación y vigencia del propietario antes de aplicarlo.

La medición de etiquetas y vistas previas sigue siendo de UI, pero se evita repetirla con entradas idénticas. No se introducen animadores, callbacks permanentes, cachés globales de views/bitmaps ni nuevas capas hardware.

El blur y la congelación de fondos ya tienen trabajo asíncrono/cancelación; no se cambia esa planificación sin trazas. Las operaciones de guardado/importación de Studio inspeccionadas ya usan workers. No se modifica la entrada de texto real ni las duraciones de animación en este grupo.

## Validación y límites

Suite final sobre el árbol completo: **280 aprobadas, 33 omitidas y 9 subtests aprobados** (219,53 s). Comando: `python -m pytest tests/ tools/connected_alpha/test_flexystudio.py tools/connected_alpha/test_composer_reference.py -q`, con JDK 21. Las omisiones corresponden a condiciones opcionales del entorno; no se cuentan como cobertura ejecutada.

`git diff --check` limpio. Las modificaciones forman parte del historial del repositorio; no requieren aplicar parches locales adicionales.

Pruebas nuevas: `tests/test_preview_frame_work.py` y `tests/test_file_editor_decode_worker.py`. Se añaden a las regresiones previas de lista/ajustes. Las pruebas verifican lógica y recuentos; los dobles de Canvas no equivalen a píxeles Android.

La cabecera completa se compiló contra android.jar API 37 con dobles de servicios del proyecto. Se analizó la sintaxis Java de los otros archivos modificados. No se ha compilado todo el módulo ni comprobado HWUI/ART en teléfono.

Antes de atribuir una mejora global, ejecutar la matriz de `JANK_PASS.md`: mismos datos/configuración y temperatura, repeticiones antes/después a refresco real 60/120 Hz, búsqueda, scroll, chat/teclado, borrado, cambio de tema/configuración y carga/cancelación de archivos. Comparar frames fuera de deadline, p95/p99, recorrido de medida/layout, CPU main/RenderThread, GPU, GC y memoria. También probar Reducir animaciones encendido y apagado: duración corta no demuestra menos coste de renderizado.

No se considera el cliente entero libre de jank ni terminado sin esta aceptación en dispositivo. La revisión local deja varios cambios pequeños verificables y un punto de partida para medir el siguiente cuello de botella.
