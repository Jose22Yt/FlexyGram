# Cristal adaptable

En **FlexyGram → Pantalla principal → Cristal iOS 27**, el interruptor principal
activa un material con refracción y contorno luminoso. Está apagado de fábrica.
Se puede elegir independientemente la barra inferior principal, la entrada de
conversación, la cabecera y las carpetas de chats. Se conserva la geometría del
estilo de interfaz elegido y sus controles táctiles. Solo la cabecera de
conversación registra ese ámbito; las barras compartidas de ajustes, adjuntos
y administración mantienen su material nativo.

## Prioridad y compatibilidad

En las zonas seleccionadas, este ajuste toma prioridad sobre el glass y blur
anteriores. No modifica sus preferencias: al apagarlo o excluir una zona, se
recupera su configuración anterior. El ahorro de batería efectivo suspende el
material temporalmente; no activa un segundo shader para reemplazarlo.

Requiere Android 13 o posterior y un lienzo con aceleración gráfica. Las versiones
anteriores conservan su apariencia compatible. Los dibujos de software mantienen
su ruta original. Si falla la creación del shader, se registra el error y se evita
repetir el intento durante el proceso actual.

## Renderizado

Cada superficie utiliza un solo shader sobre la captura nativa existente. Las
fuentes compartidas de la pantalla principal y del chat se habilitan según las
zonas activas de esa pantalla. El programa se crea al dibujar una superficie
visible y reutiliza sus parámetros; no añade temporizadores, animación continua
ni interceptores de toque. La actualización de preferencias agrupa invalidaciones
y conserva referencias débiles a los drawables.

La refracción disminuye hacia el interior y el contorno responde a una dirección
de luz fija. La composición ajusta el contraste del fondo según el tema, incluido
el tema particular de la conversación. La geometría y las fórmulas de borde se
adaptan del código público de Telegram-iOS; no se ejecuta el renderizador de Apple
ni se certifica equivalencia visual píxel a píxel. Véase [procedencia](../../CREDITS.md).

FlexyStudio guarda únicamente `enabled` y `surfaces` en `flexy_ios_glass`, dentro
de Apariencia. La restauración usa el mismo observador de preferencias.

## Verificación

`tests/test_ios_glass.py` ejecuta la política real de preferencias y transiciones
de material con dobles de servicios Android. Comprueba restauración, independencia
por zona, ahorro, caché y ausencia de reintentos de shader fallido. Cuando está
disponible skia-python, también compila y renderiza el programa real: refracción
en bordes, centro estable, recorte, tamaños mínimos y contraste claro/oscuro.

Estas pruebas y la comprobación de tipos contra el SDK no sustituyen una
compilación integrada ni la revisión visual y de tiempos de frame en teléfonos.
