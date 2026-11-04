# Interfaz inferior: galería compacta y controles recuperados

La galería de **Chat → Interfaz inferior** conserva sus dos diseños. Las vistas previas pasan de 96 a **64 dp** y sus tarjetas reducen el padding, la altura del rótulo y la separación. El dibujo de demostración se escala a 0,8 para que los controles sigan cabiendo en todos los niveles y posiciones; esto no escala el editor real.

Debajo aparecen las filas agrupadas de **Distribución**:

- **Nivel de compactación**: Normal, Compacto y Muy compacto, que utilizan los valores existentes `compactLevel=0/1/2`.
- **Posición vertical**: deslizador con indicación de cuántos dp se sube o baja respecto a la posición original.
- **Restablecer posición original**.

Los ajustes se aplican al diseño **Compacta**, donde existen los botones circulares separados. Al seleccionar **Predeterminada** los controles quedan deshabilitados y la explicación indica su alcance. No se cambia automáticamente el diseño seleccionado.

Se reutilizan `FlexyComposerConfig` y los límites existentes: posición de -4 a +16 dp y superficies de 44/40/36 dp, manteniendo los slots táctiles nativos de 44 dp. La posición positiva sube todo el conjunto; la negativa lo baja. El contenedor nativo ya aplica ese desplazamiento al campo y sus botones, con reserva de espacio y respeto de los insets del teclado. No se modifica `ChatActivityEnterView` ni `ChatInputViewsContainer` para esta tarea.

La vista previa responde a tamaño, posición y restablecimiento. El movimiento del deslizador actualiza únicamente su valor y el dibujo de las vistas previas; no reconstruye la galería durante el gesto. La vinculación de filas no escribe preferencias. Los valores ya forman parte del catálogo de exportación/importación de FlexyStudio.

El cambio de tamaño de tarjetas se limita a esta galería inferior. El constructor previo de las tarjetas sigue disponible y conserva las medidas de la galería superior. Se añaden textos en inglés, español y ruso.

## Validación

- `tests/`, `tools/connected_alpha/test_flexystudio.py` y `tools/connected_alpha/test_composer_reference.py`: **268 pruebas correctas, 33 omitidas y 9 subcasos correctos**.
- El dibujo real de las miniaturas se ejecuta en JVM con dobles explícitos: **2.016 combinaciones** de estilo, densidad, ancho, compactación y posición. Se comprueban límites de las superficies, visibilidad de iconos y dirección del desplazamiento. También se ejecuta la construcción/ruta de las filas reales para ambas galerías.
- Compilación de las clases reales del editor de entrada, galería, tarjetas, preferencias y slider contra Android API 37, con dobles para los servicios del proyecto. Análisis sintáctico Java y comprobación de diferencias sin errores de whitespace.

Las auditorías históricas `test_flexy_composer.py` y `test_integrated_approved_composer.py` comparan fuentes con revisiones antiguas y no están adaptadas a esta beta: presentan **10 fallos al leer los archivos de `f24e67248b`, la base anterior a esta modificación**. Con los cambios actuales reportan 11 puntos de fallo, incluido el nuevo contenido del recurso ruso que la comparación congelada exige mantener idéntico. No se modifican esas auditorías ni se revierten cambios de la beta para satisfacerlas.

No se genera APK, no se publica la rama y no se ejecuta una prueba visual/IME en un teléfono. Las pruebas de dibujo con dobles no miden FPS ni sustituyen esa validación física.
