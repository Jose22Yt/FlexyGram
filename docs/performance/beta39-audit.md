# Revisión y correcciones de rendimiento — beta 39 / build 1328

Base: `ffd734d4cdbc3112317091cc1caae1ef2b0086d6`, rama `codex/flexygram-beta-glass`. Esa base ya compiló correctamente en GitHub Actions (ejecución 42890078686). Esta entrega no inicia otra compilación: el propietario indicó que la haría por su cuenta.

## Correcciones

### Captura compartida del reproductor

`MusicBlurCapture` coordina las tres superficies de Orbit mediante un único juego de observadores. En cada actualización toma la unión de las superficies visibles en coordenadas de pantalla y solicita una captura regional del fondo. Conserva la reducción mínima de 8 veces y limita el lado mayor a unos 384 píxeles. La unión puede ocupar más píxeles que tres recortes independientes, pero evita repetir el recorrido de ventanas por cada superficie; hay que medir esa compensación en GPU/dispositivo.

La captura de vistas se realiza en UI, como requiere Android; el desenfoque permanece en `themeQueue`. No se trasladan vistas ni Canvas de ventanas a un trabajador. Cada superficie comparte el bitmap y recorta su región mediante una matriz con coordenadas fraccionarias. El renderer glass conserva sus shaders/nodos propios y actualiza la grabación al cambiar imagen, tamaño o recorte. Las siluetas no se reconstruyen cuando sus límites y segmentos no cambiaron.

Una generación descarta trabajos de hosts cerrados; una revisión descarta capturas anteriores a cambios de disposición/scroll. Las imágenes publicadas se liberan por referencia y no se reciclan mientras RenderThread pudiera conservarlas. La espera de 160 ms tiene una única invalidación final si existe un cambio pendiente: no hay temporizador periódico en reposo. Se retiran observadores y callback final cuando sale la última superficie. Blur apagado elimina la captura conservada.

Se añade una sobrecarga regional de `AndroidUtilities.makeGlobalBlurBitmap`; los llamadores anteriores conservan su ruta. La nueva ruta aplica traslaciones de pantalla antes/después de la escala en las unidades correspondientes.

### Aperturas de chats

`ChatNavigationGate` extiende la precarga existente a `ActionBarLayout.presentFragment`, `addFragmentToStack`, el panel lateral y `ChatActivityContainer`. Cubre la navegación normal desde enlaces, notificaciones, otras pantallas y chats incrustados, además de la lista que ya tenía precarga.

Se conservan parámetros de navegación, previsualización, posición de pila y decisiones del delegado. La carga termina antes de `onFragmentCreate`. Una generación invalida solicitudes anteriores; también se comprueban el fragmento, la cuenta seleccionada, la cuenta del destinatario y el propietario. Pausar, cerrar, vaciar la pila o separar el host invalida la solicitud correspondiente. La navegación con peer en caché continúa sin esperar tareas. Los fallos de almacenamiento no reintentan indefinidamente.

No se ha eliminado la ruta síncrona heredada dentro de `ChatActivity.onFragmentCreate`: sigue como compatibilidad para llamadores externos/plugins que invocasen directamente el ciclo de vida, evitando la navegación del cliente. Los puntos de entrada nativos de chats revisados pasan ahora por precarga. La creación de layouts y la carga inicial de mensajes todavía requieren trazas para atribuir cualquier demora residual.

### Cola y búsqueda

`MusicQueueSearch` copia los identificadores/objetos de la lista en UI y realiza normalización, índice de título/artista/archivo, filtrado y DiffUtil en `Utilities.searchQueue`. Reutiliza el índice entre consultas de la misma versión de cola. La interfaz publica el resultado mediante notificaciones de filas; el refresco completo se conserva únicamente al cambiar el tema.

Cada cambio de texto cancela inmediatamente la solicitud previa, antes de la espera de 120 ms. Resultados publicados tarde o pendientes de un layout se rechazan mediante generaciones. Cerrar la hoja o iniciar un arrastre invalida el trabajo; el arrastre no puede empezar con un filtro pendiente. Las listas originales y los callbacks de UI no se modifican desde el trabajador. Se mantienen los límites y comprobaciones de edición de la cola nativa.

### Diagnóstico y efectos

El filtro de `JankProfiler` incluye `app.flexygram.`. La medición de frames ya tenía en cuenta el deadline del dispositivo: se mantiene. No se activa el muestreo automáticamente ni se cambia la preferencia de ahorro de energía. El menú depende de `DEBUG_TOOLS` (compilaciones de diagnóstico con `-PdebugTools=true`).

Las burbujas mantienen sus cachés y el dibujo de bordes/fusión. No se altera su apariencia para ocultar coste de GPU. El sistema propio de animaciones, sus curvas y los ajustes de animaciones de Android no se modifican.

## Comprobaciones

- JVM sobre clases/métodos de producción: tres superficies comparten una captura; 10 000 predraws estáticos no generan otras capturas; una invalidación final por cambio, límites de resolución, blur apagado, cierre, resultados tardíos, recorte de origen negativo y precisión fraccionaria.
- JVM: consultas con acentos y listas de 5 000 entradas, caché de índice, cálculo fuera de UI, cambios rápidos de consulta, cancelación al cerrar, snapshots independientes y diferenciación de mensajes con igual ID en otros chats.
- JVM: aperturas obsoletas, cuenta seleccionada/destino cambiada, propietario inválido, fragmento destruido, fallo y ruta con caché. Se compila y ejecuta el método completo de producción `addFragmentToStack`, conservando inserción al principio, al final, sin adjuntar vista y descarte de respuestas tardías.
- Clasificación de módulos FlexyGram en el perfilador; fixtures visuales adaptados al coordinador y al recorte compartido.

**Suite completa: 374 aprobadas, 39 omitidas, 0 fallos.** Las omisiones corresponden a SDK/AndroidX, corpus externos y herramientas ausentes. La sintaxis de los 12 archivos Java de producción modificados/nuevos y los 57 archivos del fixture musical generado pasa. Las pruebas con dobles de Android verifican ejecución y conteos, no FPS ni tiempos de GPU. El SDK API 37/Build Tools 36 no está instalado en este entorno, por lo que no se presenta el render nativo ni el enlace Android completo como ejecutados.

## Validación pendiente en dispositivo

Comparar base y candidata en el mismo equipo con scroll de lista/chats, apertura fría/caliente por lista/enlace/notificación, cambio de cuenta durante carga, blur/glass, teclado, rotación y sesiones largas. Medir p95/p99, frames fuera del presupuesto, UI/RenderThread, memoria y toque-a-primer-contenido, con los mismos datos, frecuencia y tema. Probar colas grandes y cambios rápidos de consulta/arrastre. No hay un porcentaje de mejora ni una promesa de ausencia total de lag sin estas mediciones.
