# Segunda revisión: filas de ajustes

Base local: `41ec915549ddeea4bbe53eb6ade6d20114b1dc4b`, rama `share/flexygram-settings-motion-menus`.

## Cambios

`Settings2Cell` reconstruía dos GradientDrawable, un RippleDrawable y un InsetDrawable por cada asignación de esquinas. Cada bind también cargaba de nuevo el icono y su fondo nativo. Ahora cada fila conserva sus propios objetos y modifica solo colores y geometría que han cambiado. El ripple conserva su identidad durante cambios de tema o agrupación. La máscara mantiene las mismas esquinas que la superficie.

El icono se reutiliza mientras coincidan ID, Resources y una copia de Configuration. Se vuelve a cargar ante cambios de configuración o tabla de recursos; no hay caché global de Drawables, Context o vistas. Cada fila tiene sus propias instancias. Se vuelve a aplicar el color al asignar un icono.

La transición de fila normal a tarjeta solicita medición: añade el espacio inferior que usa la propia medición. El cambio de densidad actualiza radios e inset.

Se corrigió también el cambio de tema en filas ya visibles: antes dispatchDraw actualizaba el filtro del icono pero no los colores de título y descripción. Ahora se sincronizan los tres, con setters únicamente cuando cambian los colores o se asigna el contenido.

## Verificación

Suite final: **274 aprobadas, 33 omitidas y 9 subtests aprobados** (`tests/`, `tools/connected_alpha/test_flexystudio.py`, `tools/connected_alpha/test_composer_reference.py` con JDK 21). `git diff --check` limpio.

- Pruebas JVM ejecutan los métodos reales con dobles explícitos de Android y contadores de creación/setters.
- 10.000 actualizaciones idénticas conservan fondo e icono; solo se crean dos gradientes, un ripple y un inset por fila estable.
- Casos: cambios de tema, esquinas superior/inferior, densidad, fondo sustituido, icono ausente, ID distinto, mutación de Configuration, cambio de Resources e independencia entre filas.
- La prueba de tema verifica colores de texto/icono y evita repetir setters durante 10.000 dibujos estables.
- Se compiló la clase real Settings2Cell contra android.jar API 37 con dobles de los servicios del proyecto (javac 21); no es una compilación integrada ni una APK.
- Estas pruebas cuentan trabajo y comprueban comportamiento lógico; no miden FPS, HWUI, batería ni temperatura.

## Alcance de la revisión

Se inspeccionaron las rutas personalizadas de ajustes, galerías, cabecera, entrada, burbujas, wallpaper y navegación. Se revisaron las invalidaciones, creación de recursos y notificaciones de adaptadores; una coincidencia de búsqueda no demuestra un cuello de botella. Este cambio se limita al problema comprobado de filas de ajustes. No representa una auditoría funcional de todas las pantallas de Telegram.

Las rutas de blur y wallpaper ya tienen cachés/cancelación y pruebas previas: no se añadió otro motor ni otra cola. Las notificaciones completas de adaptadores al cambiar visibilidad de opciones no se sustituyeron sin verificar sus filas dependientes. La escala de animación no se considera una mejora de coste de renderizado.

Para optimizar apertura de chats, scroll y comportamiento térmico hace falta localizar el coste real con FrameTimeline/Perfetto en dispositivo: main thread, RenderThread, GPU, GC, caché fría/caliente. Aplicar cambios de planificación o reducir efectos sin esas mediciones puede empeorar carga, accesibilidad o calidad visual. No se afirman mejoras porcentuales de fluidez ni se generó una APK en esta revisión.
