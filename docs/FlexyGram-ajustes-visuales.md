# Ajustes visuales de FlexyGram

Estado de compilación más reciente: [Compilación de la beta](FlexyGram-beta-compilacion.md). Las notas de validación de este documento describen las etapas anteriores.


Cambios preparados sobre el checkout de `main`. No se compiló APK ni se ejecutó Gradle.

## Cambios

- Ajustes de chat: las filas personalizadas de tamaño y forma de stickers, doble toque y selección de reacción ahora participan del mismo tratamiento de fondo que las demás filas. Con tarjetas redondeadas se elimina el fondo rectangular de esas filas; sin redondeo se mantiene el fondo del tema.
- Contador junto a retroceso: pinturas propias, colores del proveedor del tema activo y redibujado al actualizar colores. Ya no depende de las pinturas compartidas de la lista de chats. Se conserva el límite visual `99+`.
- Tarjeta de contacto de la cabecera: el ancho del título y subtítulo considera los márgenes y nunca genera especificaciones de medida negativas en espacios estrechos.
- Navegación inferior: opción de barra compacta con tres niveles seleccionables: Extracompacta (48 dp), Compacta (52 dp) y Cómoda (56 dp). Sin títulos se mantiene una altura de 48 dp. Los márgenes son 4/6/8 dp y el ancho preferido por pestaña es 56/64/76 dp. El espacio se distribuye entre las pestañas visibles y se limita al disponible en pantalla, descontando la búsqueda flotante. El modo compacto tiene prioridad sobre el estilo Material 3. Los controles existentes para ocultar títulos y pestañas se mantienen.
- Búsqueda circular opcional junto a la barra: espacio reservado, posición compatible con RTL e insets, fondo con el mismo proveedor glass y actualización de tema. Abre la búsqueda de Chats. Su visibilidad y estado táctil siguen la animación de la barra.
- Corrección adicional: las pestañas se habilitan al completar la animación (`factor >= 1`); antes se exigía `factor > 1`, fuera de su intervalo normal.

Los dos nuevos controles están en Ajustes de navegación de la app: **Barra de navegación compacta** y **Botón flotante de búsqueda**. La barra compacta está activada por defecto; la búsqueda es opcional. Recursos en español e inglés.

## Validación

- Sintaxis de los archivos Java modificados: validada con Tree-sitter.
- Recursos XML nuevos: lectura correcta.
- `git diff --check`: correcto.
- Suite Python: 140 aprobadas, 31 omitidas y 2 fallos preexistentes en `test_reflection_gate.py`; las simulaciones no exponen `get_reflection_policy`, requerido por el cargador.

Estas comprobaciones no sustituyen una compilación Android ni pruebas visuales. Queda por probar en dispositivo: cambio claro/oscuro sin reiniciar, títulos largos, tamaño de fuente grande, RTL, orientación horizontal, tres/cuatro pestañas, búsqueda activada/desactivada y navegación por gestos/tres botones. No se afirma equivalencia exacta con Cherrygram. Las opciones «Signature Compact» y «Liquid Glass perlado» de la captura no aparecen con esos nombres en este checkout; los cambios se aplicaron a sus componentes disponibles, sin poder reproducir esa pantalla exacta.

## Ampliación: nivel de compactación

En Ajustes de navegación, activar **Barra de navegación compacta** y abrir **Nivel de compactación**. La selección queda guardada y reconstruye los fragmentos para aplicar las nuevas medidas. La opción de ocultar títulos sigue siendo independiente. En modo compacto se reparten los píxeles sobrantes entre pestañas mediante límites acumulados para evitar desbordes por redondeo. Sintaxis Java, XML y diff verificados; adaptación visual pendiente de prueba en dispositivo. No se compiló APK.

## Vista previa interactiva y orden de pestañas

- La sección de navegación incorpora una vista previa con los iconos reales de las pestañas y el avatar de perfil. Tocar selecciona una pestaña dentro de la vista previa, sin navegar fuera de los ajustes.
- Mantener pulsada una pestaña inicia el arrastre. Soltar sobre otra intercambia sus posiciones; cancelar o soltar fuera no guarda cambios. Se resaltan los destinos y hay respuesta háptica al comenzar.
- El orden se guarda localmente y se aplica tanto a la barra real como al orden de las pantallas al deslizar. Chats puede cambiar de posición y sigue siendo la pantalla inicial y el destino del botón de búsqueda.
- Las pestañas ocultas conservan su lugar guardado. Feed comparte el lugar de Contactos y Llamadas comparte el de Ajustes, según las opciones existentes.
- Se conserva el estado de Chats al reconstruir la distribución; las otras pantallas se recrean en sus posiciones nuevas.
- Se añadió «Restablecer orden de pestañas». Los interruptores de pestañas quedan dentro de «Pestañas visibles», desplegable, para reducir el contenido inicial. La sección se agrupa en una tarjeta y la vista previa refleja el nivel de compactación y la reserva de búsqueda.
- Accesibilidad: las pestañas anuncian nombre y posición; las acciones de avanzar/retroceder permiten intercambiar con la pestaña adyacente sin arrastrar.

Validación añadida: `tests/test_main_tabs_order.py`, con dos pruebas JVM aprobadas. Cubren las 24 permutaciones, intercambios reversibles, correspondencia entre pestaña y posición, ocultación y restauración, preferencias malformadas y restablecimiento. Se ejecuta el módulo compilador Java únicamente para estas pruebas de lógica aislada; no se compila Android ni APK. Sintaxis Java, XML y `git diff --check` correctos. Pendiente verificar en dispositivo el gesto nativo de arrastre, TalkBack, cambio de tema y las transiciones del ViewPager.
