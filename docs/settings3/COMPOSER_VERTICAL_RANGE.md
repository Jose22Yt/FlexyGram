# Mayor recorrido inferior de la entrada compacta

Rama local: `share/flexygram-settings-motion-menus`.

El rango de posición pasa de −4…16 dp a **−160…16 dp**, conservando la posición predeterminada 0 y el botón de restablecer. Ambos editores de posición usan las constantes comunes, por lo que sus sliders reciben el rango nuevo sin duplicar límites. No se añade una corrección para mantener la barra dentro de pantalla: en el extremo inferior puede desaparecer, como se solicitó.

`ComposerStyle.offset` mantiene `10 + posición`. Con −160, el desplazamiento del conjunto cambia a 150 dp hacia abajo respecto al anclaje nativo, o 160 dp por debajo de la posición predeterminada. El contenedor existente traslada la isla completa, incluyendo los círculos; no se cambia la altura del texto para desplazarla. El ajuste se sigue aplicando al modo Compacta.

`ComposerStyle.reserve` queda acotado por debajo a cero para no restar 150 dp a la altura reservada de la entrada o la lista. Se conserva la reserva previa en el rango antiguo. El esquema de FlexyStudio acepta −160…16 para no rechazar el nuevo ajuste al importar/exportar. No se cambian los valores guardados ni se migra la preferencia: se amplía su validación.

Verificación: **16 pruebas aprobadas y 9 subtests aprobados**, ejecutando políticas reales, rango completo, extremos, validación del esquema, sliders/restablecer, pruebas de galería/medición, selector de grupos y codecs/transacciones de FlexyStudio. `git diff --check` limpio.

Sin APK ni publicación. Pendiente comprobar en dispositivo con teclado abierto/cerrado, navegación por gestos y teclas, y regreso a ajustes para restablecer una barra fuera de pantalla. Las versiones anteriores pueden rechazar configuraciones con posiciones fuera de su rango antiguo.
