# Estado actualEste sistema fue retirado. Véase [Restauración de Liquid Glass nativo](FlexyGram-restauracion-liquid-glass.md).
El resto de este documento conserva la descripción histórica.

# Cristal universal

Estado de compilación más reciente: [Compilación de la beta](FlexyGram-beta-compilacion.md). Las notas de validación de este documento describen las etapas anteriores.


Implementación opcional basada en las dos referencias visuales: superficies translúcidas, tinte suave y bordes de luz. No se afirma reproducción idéntica a las capturas; no se ha ejecutado ni comparado la app en un dispositivo.

## Ajustes

Ruta: **Apariencia → Universal · Cristal optimizado**.

- Personalización del acabado, desactivada por defecto. El motor de cristal optimizado se utiliza de base; desactivar la personalización no restaura Liquid Glass.
- Opacidad del tinte: 20–85 %, con valor inicial 42 %. En oscuro el tinte se ajusta proporcionalmente.
- Intensidad del borde de luz: 0–100 %, inicialmente 70 %.
- Activación independiente para entrada de mensajes, cabecera, navegación principal, búsqueda, menús y carpetas.
- «Aplicar apariencia» reconstruye las superficies abiertas. Los cambios guardados también se aplican al cerrar esta sección.

## Integración

`UniversalGlass` concentra los colores, bordes, sombra y comprobaciones de disponibilidad. Reutiliza el motor blur/glass existente; no captura la pantalla ni crea bitmaps por fotograma. Los controles numéricos se limitan incluso si las preferencias guardadas contienen valores fuera de rango.

- Campo de mensaje: adapta su proveedor de color existente, conservando geometría y comportamiento del teclado.
- Adjuntos y envío: fondos glass propios con el mismo material. Adjuntos conserva el selector táctil. Envío adapta el icono y el indicador de carga al tema y evita que el relleno opaco tape el cristal.
- Cabecera: adapta el proveedor de la píldora de título y del fondo glass existente del avatar/menú. Cuando se activa este estilo, la variante Material 3 permite dibujar la píldora central. No se superpone una capa translúcida al retrato del contacto.
- Navegación y búsqueda circular: proveedores separados para que sus interruptores sean independientes.
- Búsqueda principal y carpetas: material compartido aplicado a los fondos glass de las barras existentes. Se conservan los indicadores de selección; no se rediseña la geometría individual de cada carpeta.
- Menú de mensajes y reacciones: integración en el proveedor nativo y en el menú personalizado. La capa de relleno evita duplicar el borde exterior.

Se respetan los ajustes de desenfoque, contorno, ahorro de energía y disponibilidad del motor. Activar el nuevo material no fuerza el desenfoque ni elimina las restricciones existentes. Si este no está habilitado, continúa la apariencia de reserva del componente. Los iconos siguen los colores del tema para conservar legibilidad, en lugar de forzar blanco sobre cualquier fondo.

## Validación y límites

- Prueba JVM de `UniversalGlass`: aprobada. Comprueba activación por zona, desactivación de blur, identidad del proveedor de reserva, límites de opacidad y borde, y adaptación del tinte al tema. Usa dobles de prueba para las dependencias Android; no prueba el renderizado real.
- Sintaxis de Java modificado y lectura de XML: correctas.
- `git diff --check`: correcto.
- No se ejecutó Gradle ni se compiló APK.

Queda por validar en Android: resultado sobre fondos claros/oscuros y complejos, contraste, temas por conversación, estados de envío/grabación/carga, adaptación de adjuntos, animaciones, menús de mensajes, filtros/carpetas y rendimiento con blur disponible o desactivado. La intensidad y calidad del desenfoque siguen las capacidades del motor existente; los nuevos controles cambian tinte y borde, no inventan un nuevo algoritmo de refracción. La vista previa de reordenación de pestañas conserva su función de distribución; no constituye una comparación óptica del acabado con las referencias.


## Sustitución de Liquid Glass por cristal optimizado

La nueva ruta compartida utiliza desenfoque del fondo, tinte y contorno, sin refracción. Se reutiliza la ruta eficiente de blur existente en vez de introducir un nuevo shader. Esta sustitución es general para las superficies que usan `blur3`, independientemente de que la personalización universal esté activada.

- Las consultas al antiguo indicador Liquid Glass no lo activan, incluso si está guardado en preferencias o en una máscara combinada. Se conservan los demás bits y los valores guardados; no se borran las preferencias del usuario.
- La fábrica y el drawable conservan métodos de compatibilidad sin efecto; ya no crean `LiquidGlassEffect`. La clase y el recurso heredados quedan sin instanciar desde el código de la app.
- Se elimina el interruptor Liquid Glass de ahorro de energía y de la máscara de opciones del chat. El interruptor de desenfoque existente continúa funcionando.
- El capturador usa escala 8 por dimensión en la ruta normal; para una región de dimensiones divisibles por 8, el búfer capturado contiene 1/64 de los píxeles de resolución completa. Se conserva la captura completa para la ruta especial que solicita supresión de ruido de desplazamiento. Este cociente describe el búfer de entrada, no el consumo total de memoria/GPU ni una mejora de FPS medida.
- La rama normal deja de preparar la salida adicional de refracción; se mantienen la delimitación de regiones y las comprobaciones de contenido sin cambios del motor existente.
- Se elimina una grabación duplicada del primer RenderNode reducido.
- Los tamaños de captura y de reducción nunca bajan de un píxel para evitar búferes de tamaño cero.
- Las superficies opacas no graban el fondo que no se va a ver.
- Las animaciones que solo cambian opacidad actualizan el alpha del RenderNode sin volver a grabar su contenido. Posición, dimensiones, colores y cambios de fuente siguen invalidándolo.
- Se corrige el balance de `save`/`restore` al grabar el fondo.

Se preserva el blur esmerilado de la rama existente y sus colores adaptables. Al retirar el efecto de lente, el resultado puede ser más difuminado y menos deformado que el vídeo; hace falta comparación en dispositivo para afinar el parecido.

Validación de esta sustitución: tres pruebas nuevas aprobadas en `tests/test_optimized_glass.py`. Comprueban dimensiones pequeñas y habituales, reducción de captura, compatibilidad de preferencias antiguas/máscaras combinadas y ausencia de creación del shader refractivo en la fábrica/drawable. Las pruebas del material universal y del orden de pestañas también pasaron durante esta tarea. Sintaxis Java, recursos XML y diff revisados. No se ejecutó Gradle ni se compiló APK. No se ha medido FPS, batería, temperatura o memoria en Android; falta validar también la fidelidad visual y la ausencia de artefactos al desplazar contenido y abrir el teclado.
