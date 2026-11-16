# FlexyGram beta64: prueba de interacción elástica

Base optimizada y corrección de toques: beta63 `933befdeca9df32fd9edbd018bded2a8aa600cec`.
Rama `codex/flexygram-elastic-test`, paquete conservado
`com.flexygram.messenger.nativebaseline`, versión beta64/código1353.
No se reactivan FlexyFiles, FlexyStudio, personalización de navegación antigua,
efectos de burbujas, reproductor personalizado ni reescritura FastMotion.

## Controles y preferencias

Navegación y gestos → Interacción elástica: activada inicialmente en esta prueba,
preferencia independiente `flexy_elastic_interaction/enabled`.
Respuesta visible: hasta8.5% para botones pequeños,4% para medianos y2.5% para
superficies anchas, adaptada al espacio disponible para evitar invadir sus padres.
La preview utiliza dos controles pulsables reales con unión de contornos.
Una elección OFF se conserva; no se sobrescriben las preferencias de Android.

Navegación y gestos → Barra inferior → Liquid Glass Kyant: apagada inicialmente.
Solo sustituye el material de la barra principal. Se restaura LiquidGlassEffect y
su shader original de Telegram en las demás superficies y en el fallback nativo.
Su interruptor global de ahorro de energía conserva su significado original.
La preferencia Kyant es independiente y no cambia ese interruptor.

## Entrada nativa y cobertura

Observador sin consumo en BasePermissionsActivity, AlertDialog, BottomSheet,
ActionBarPopupWindow, PhotoViewer, ArticleViewer, StoryViewer y StoryRecorder.
Se conserva el MotionEvent original: no se reenvía, retrasa ni sintetiza un clic.
La raíz se canoniza por ventana y se deduplican observaciones del mismo evento.

El objetivo visual se identifica al DOWN: botones, pestañas, filas nativas,
interruptores, campos, controles y superficies dibujadas en celdas de mensajes.
Las superficies Canvas de mensajes responden como celda, no como una malla
independiente para cada subelemento. Las animaciones nativas de entrada/envío,
progreso, reacción y transición se conservan, sin sustituir sus temporizaciones.
El compositor promociona el editor a su contenedor visual; el fondo de entrada
acompaña su pulso. Cabecera: fondo nativo y control comparten deformación.

El scroll cancela la pulsación elástica al superar el slop. Los botones fuera de
listas pueden seguir el arrastre con desplazamiento limitado. UP/CANCEL/multitouch
liberan el resorte. En campos el pulso se libera pronto para preservar la selección.
No se deforman WebView, SurfaceView o TextureView ni se alteran el teclado del
sistema, otras aplicaciones o contenido externo. Una Animation nativa existente
conserva prioridad. Kyant tiene su interacción propia, evitando una segunda capa.

## Implementación

Transformación de dibujo Animation, no View.scaleX/translationX ni layout.
La matriz nativa de hit testing permanece estable; los cambios de tamaño son visuales.
Resorte integrado en pasos pequeños, finito, interrumpible y sin ticker global.
El pose estable retenido no solicita más frames; OFF y detach limpian la transformación.
Se respeta SharedConfig.animationsEnabled, la escala de animadores y ahorro de energía.

La fusión utiliza conectores Bézier locales entre un máximo de4 superficies registradas:
compositor, cabecera y preview. Una barra ya unificada no añade un conector duplicado.
No se comparan todos los controles de la aplicación. Los límites del fondo nativo
se obtienen de los drawables; referencias a vistas/drawables/ventanas son débiles.
Se pintan únicamente los huecos de superficies cercanas mientras hay deformación.
Es una unión visual2D; no una simulación de agua ni reproducción verificada de la
óptica de Apple sobre la unión. La apariencia debe validarse en la APK real.
No hay blur adicional, capturas Bitmap/PixelCopy ni lecturas GPU→CPU para elasticidad.
Los snapshots de menús conservan el dibujo normal, sin la pose temporal de la entrada.

La barra mantiene KyantDockContainer: el overlay no puede expandir WRAP_CONTENT a
pantalla completa. Se mantienen coordenadas físicas/insets/RTL y clipChildren=false
para permitir el dibujo exterior de las animaciones y sombras dentro de la pantalla.

## Comprobación

`pytest tests/`: estabilidad de resortes, presupuesto de invalidaciones en reposo,
rutas de ajustes y contratos del cliente. `tools/kyant_lab/android/run.py` compila
el núcleo real con Compose/Android y prueba matriz de toque intacta, clics, foco,
selección, cancelación, reciclaje, scroll RecyclerView, fusión local y límites de barra.
Solo los servicios anfitriones ajenos al escenario son dobles explícitos.
Estas pruebas no certifican FPS/temperatura/batería de un teléfono ni cobertura de
cada pantalla de sesión real. Comparar ON/OFF sobre la misma cuenta y mismos chats
tras terminar sincronización. La fluidez medida decide la intensidad final.
