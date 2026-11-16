# beta67: retirada del rebote y barra óptica estable

Rama `codex/flexygram-performance-67`, versión `1.0.0-beta.67-performance`, código1356.
Paquete de prueba optimizada conservado: com.flexygram.messenger.nativebaseline.
La beta66 anterior queda en el historial ad0b99ba63492c248e1b32e33646f81738a01dc0.

## Retirada completa de la interacción añadida

Se eliminan observadores de MotionEvent, resortes globales, fusiones, matrices de
pulsación y fondos por control añadidos en beta64–66, junto con su pantalla,
icono, cadenas e IDs. Se restauran los materiales/gestos de la base nativa.
No se cambia la escala de animación de Android ni se reactiva FastMotion.
El interruptor opcional de Kyant se mueve a su paquete propio; el nombre del archivo
de preferencias anterior se conserva solo para leer la elección de la barra,
sin leer jamás la antigua clave de activación de elasticidad.

## Barra inferior

Material Kyant opcional, predeterminado OFF, únicamente en la barra principal.
Se retira InteractiveHighlight: pintaba rectángulos sin máscara de cápsula después
del backdrop. También se eliminan escala del panel, escala de iconos, velocidad
que deformaba el selector y clases auxiliares sin uso. El selector conserva solo
posición acotada y transición finita sin sobrepasar su destino; un nuevo gesto
cancela el trabajo anterior. No hay un reloj global de animación en reposo.
Los padres permiten dibujo exterior y el host carece de fondo/elevación/outline
rectangular. Se conserva la geometría nativa, la exclusión del área de sistema,
RTL, eventos y KyantDockContainer, evitando volver al bloqueo de pantalla completa.
La óptica de refracción/blur y el material nativo de Telegram siguen sus preferencias.
El manifiesto `third_party/kyant-backdrop/local-patches.json` distingue el código
local de las huellas originales; no se presenta el catálogo modificado como idéntico.

## Apertura y chats

Antes se construía y adjuntaba KyantDockView incluso con el efecto apagado, pudiendo
inicializar Compose durante el primer layout. Ahora no se crea hasta activar su
opción y se retira por completo al desactivarla. Una prueba ejecuta10000 aperturas
simuladas de la rama OFF sin construir un host y confirma creación única al activar.
No representa una medida de milisegundos de arranque en un teléfono.
Se conserva la prioridad existente de los primeros32 chats desde SQLite, publicación
local antes de la sincronización remota, cuentas secundarias diferidas y servicios
escalonados. No se añaden esperas de red, ni se oculta el estado de sincronización.

## Alcance y comprobación

Las pruebas cubren fuentes/restauración nativa, rutas retiradas, carga de chats,
residuo de clases/recursos, coste de la rama OFF, selector sin overshoot, límites
físicos LTR/RTL y dispatch de botones/scroll. El efecto óptico y la fluidez después
de horas de sesión siguen necesitando validación en el teléfono. No se afirman FPS
ni porcentajes de velocidad sin medición de dispositivo.
Los módulos antiguos de otras variantes del repositorio conservan sus referencias
compartidas; la prueba nativa mantiene sus bloqueos de rutas y optimización R8.
No se reintroducen FlexyFiles, FlexyStudio, reproductor propio, editor antiguo de
barra, efectos de borde de burbujas ni páginas obsoletas de ajustes.
