# FlexyGram beta66: prueba de interacción elástica

Base optimizada y corrección de toques: beta63 `933befdeca9df32fd9edbd018bded2a8aa600cec`.
Rama `codex/flexygram-elastic-test`, paquete conservado
`com.flexygram.messenger.nativebaseline`, versión beta66/código1355.
No se reactivan FlexyFiles, FlexyStudio, personalización de navegación antigua,
efectos de burbujas, reproductor personalizado ni reescritura FastMotion.

## Controles y preferencias

Navegación y gestos → Interacción elástica: activada inicialmente en esta prueba,
preferencia independiente `flexy_elastic_interaction/enabled`.
Respuesta visible: hasta51% para botones pequeños,24% para medianos y15% para
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

El objetivo visual se identifica al DOWN y queda limitado al control accionado.
Se eliminan las promociones a MainTabsLayout, ActionBarMenu y al contenedor del
editor/envío. Una etiqueta heredada en un padre no puede agrupar a sus hijos.
Un grupo con acciones hijas independientes no se anima al tocar sus huecos.
Solo se permite un wrapper decorativo pequeño de un único hijo sin acción propia.

Cada control conserva su material y contenido en la misma transformación de dibujo.
ElasticControlBackground conserva el ripple original, padding, estado y visibilidad;
el material nuevo procede de la misma fábrica nativa de Telegram y se crea una
sola vez al configurar el control. No añade capturas, blur por CPU ni capas animadas.
El menú de cabecera usa materiales por acción; el compositor separa editor, emoji,
adjuntar y controles auxiliares. Enviar/micrófono conservan su pintura nativa propia.
Con OFF se dibuja de nuevo el material compartido y los fondos originales.
El fondo compartido nunca se transforma siguiendo al editor o a una barra completa.
La amplitud de pulsación/arrastre duplica beta65 (editor10.8%); los límites del padre
pueden reducir la expansión. No se duplica la frecuencia de frames ni los resortes.

Cobertura del observador común: actividades, diálogos, menús, hojas y visores citados.
No se afirma cobertura óptica comprobada en cada pantalla de una sesión real.
Las celdas ChatMessageCell contienen acciones Canvas independientes que no son Views:
se excluye su deformación conjunta; sus interacciones nativas se conservan hasta tener
geometría explícita por subcontrol. No se simula independencia animando toda la celda.
Las animaciones nativas de envío, reacción y transición conservan prioridad.

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
Un retap conserva posición/velocidad; hasta3 superficies por ventana pueden terminar
su recuperación juntas. Se limita ese conjunto y se cancela completamente con OFF.
El pose estable retenido no solicita más frames; OFF y detach limpian la transformación.
Se respeta SharedConfig.animationsEnabled, la escala de animadores y ahorro de energía.

La fusión de contornos se conserva únicamente en la preview de controles reales;
no anima ni une como bloque la cabecera o el compositor. Cada resorte es independiente.
No hay blur adicional, capturas Bitmap/PixelCopy ni lecturas GPU→CPU para elasticidad.
Los snapshots conservan la propiedad de los materiales de cada control.

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
