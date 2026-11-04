# Burbujas: tarjetas compactas del editor

Se adapta únicamente `BubbleSettingsActivity` al estilo agrupado existente: tarjetas a todo el ancho, radios exteriores de 28 dp, interiores de 6 dp y separación de 4 dp, definidos por la infraestructura compartida de ajustes. No se añade una barra de pestañas nueva.

## Organización por función

La vista previa se mantiene independiente, seguida de tres grupos nativos:

- **Apariencia**: transparencia y desenfoque de fondo.
- **Borde**: activación, estilo, grosor, posición e intensidad glass (cuando el estilo la permite).
- **Fusión**: modo de fusión e intensidad/adaptación cuando se selecciona Fusion 2.0. Este grupo se oculta si el borde está desactivado.

Los títulos se dibujan sobre el fondo de la pantalla, fuera de las tarjetas tanto por tipo del adaptador como por tag de la vista, incluso si cambia la preferencia global de encabezados. Así cada bloque recibe sus propias esquinas exteriores y las filas interiores conservan la separación compacta común.

Las filas personalizadas de sliders declaran `MATCH_PARENT`/`WRAP_CONTENT`, como el resto de filas de ajustes. La vista previa conserva su fondo propio y queda fuera del grupo tanto por el tag de la vista como por el clasificador del adaptador. Sus márgenes compensan el inset de 8 dp del preview para alinearlo con los 12 dp de las tarjetas. Se desactiva el animador de filas en esta pantalla, como en los otros editores compactos.

No cambian los controles, getters/setters, opciones de fusión, rangos de sliders, preferencias ni callbacks. Se conserva la vista previa con el fondo contextual.

## Validación sin APK

`tests/test_bubble_settings_cards.py` ejecuta las fábricas, construcción de filas y clasificadores reales con APIs Android representadas por dobles explícitos. Cubre las 24 combinaciones de borde activado/desactivado, cuatro estilos y tres modos de fusión, con ambas preferencias globales de encabezados (48 casos); comprueba anchura completa, clasificación, alineación, límites y orden de secciones, filas condicionales y animador desactivado. No es una captura visual de Android ni una prueba de la APK en un teléfono.

No se compila APK ni se publica la rama para evitar activar la compilación automática.
