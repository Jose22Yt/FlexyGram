> Registro de beta68. El usuario reportó persistencia al volver: la recuperación reforzada y los cambios actuales están en [beta69](beta69.md).

# beta68: lente de la barra y recuperación de ventana

Base a9ca3b9117df4384b7bcd95492c82a1dcc63260b (beta67), versión
1.0.0-beta.68-dock-optics/código1357; paquete nativo optimizado conservado.

## Apariencia y coste

Se recupera la magnificación original78/56 de la lente seleccionada durante
pulsación/transición. La pestaña pulsada activa la refracción también al seleccionar
otra sección; beta67 solo activaba el progreso óptico al arrastrar sobre el selector.
El pulso es finito y cancelable; una generación de transición evita que la
finalización de un movimiento cancelado apague el pulso nuevo. No se restauran rebote global, observadores de
eventos, fusión, movimiento del panel, escala de iconos ni deformación por velocidad.
La capa InteractiveHighlight que pintaba rectángulos sigue eliminada.
No se añade una simulación de agua, Bitmap, PixelCopy ni un segundo sistema de glass.

El overlay dispone de24dp transparentes por encima y debajo. Solamente se amplía
su zona de dibujo; el contenedor conserva la altura medida desde la barra nativa,
coordenadas, insets y objetivos de toque. Composición y cálculo del gesto incluyen
el mismo desplazamiento óptico para que el indicador no quede desalineado.
Se mantienen clipChildren/clipToPadding desactivados, sin elevación ni fondo
rectangular. La fuente de escena conserva su caché y margen óptico de32dp.

## Al salir y volver

Se observa explícitamente visibilidad de ventana, recuperación de foco y layout
completado. AbstractComposeView conserva su onLayout final; se utiliza un listener.
El estado ready es observable y Content lo lee antes de publicar propiedad nativa:
una composición que vuelve a mostrarse puede recuperar el modo de dibujo correcto.
La barra nativa y su accesibilidad se conservan hasta que la composición está lista;
la pérdida de disponibilidad o la separación de la vista libera la escena, callbacks
y la propiedad óptica. Reentrar no modifica la preferencia del usuario.

Kyant continúa siendo opcional y predeterminado OFF, creado únicamente al activarlo.
Se mantienen las rutas de arranque/SQLite primero, sin cambios de sincronización,
cuentas, reproductor, burbujas limpias ni servicios globales.

## Verificación y límites

Pruebas reales Android/Compose de límites LTR/RTL/resize, margen transparente sin
cambiar la barra medida, dispatch nativo de botones/scroll y selector acotado.
La prueba del bridge ejecuta callbacks reales de ventana/foco tres veces y verifica
que se recupera el material, se conserva el opt-in y vuelve el fallback/accesibilidad.
La capacidad de hardware y la publicación de una composición completada son entradas
explícitas del test, no una afirmación de render óptico en una GPU física.
Las pruebas no certifican la apariencia píxel a píxel ni FPS en el teléfono;
la aceptación visual de la APK requiere compararla con el vídeo del usuario.
