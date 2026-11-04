# Burbujas: tarjetas compactas del editor

Se adapta únicamente `BubbleSettingsActivity` al estilo agrupado existente: tarjetas a todo el ancho, radios exteriores de 28 dp, interiores de 6 dp y separación de 4 dp, definidos por la infraestructura compartida de ajustes. No se añade una barra de pestañas nueva.

Las filas personalizadas de sliders ahora declaran `MATCH_PARENT`/`WRAP_CONTENT`, como el resto de filas de ajustes. La vista previa conserva su fondo propio y queda fuera del grupo tanto por el tag de la vista como por el clasificador del adaptador; así el primer control recibe el radio superior correcto incluso al hacer scroll. Sus márgenes compensan el inset de 8 dp del preview para alinearlo con los 12 dp de las tarjetas. Se desactiva el animador de filas en esta pantalla, como en los otros editores compactos.

No cambian los textos, controles, getters/setters, opciones de fusión, rangos de sliders, preferencias ni callbacks. Se conserva la vista previa con el fondo contextual.

Validación: `tests/test_bubble_settings_cards.py` ejecuta las fábricas, construcción de filas y clasificadores reales con APIs Android representadas por dobles explícitos. Cubre las 24 combinaciones de borde activado/desactivado, cuatro estilos y tres modos de fusión; comprueba anchura completa, clasificación, alineación, filas condicionales y animador desactivado. Se ejecutan también las regresiones existentes de agrupación y conservación de callbacks. No es una captura visual de Android ni una prueba de la APK en un teléfono.

No se compila APK ni se publica la rama para evitar activar la compilación automática.
