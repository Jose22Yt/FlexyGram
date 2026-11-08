# Prompt de continuación — reproductor Órbita de FlexyGram

Continúa exclusivamente el rediseño del reproductor de música de FlexyGram. El usuario ya autorizó desarrollarlo. El avance está incompleto: termina y valida la integración; no lo presentes como una versión acabada.

## Código que debes recuperar

- Repositorio: https://github.com/Jose22Yt/FlexyGram
- Rama de continuación: `codex/flexygram-orbit-player-20261108`.
- Directorio de trabajo en el entorno de origen: `/workspace/FlexyGram-beta17-chat-controls`.
- Base anterior al trabajo de Órbita: `9ac9f8828be4884e3a4553b5af49fc22b7887998`. Recupera la rama de continuación, no solamente esta base.
- Conserva las modificaciones anteriores del proyecto. No sobrescribas ni hagas force push en `codex/flexygram-beta-glass`. Compara con su versión remota antes de una futura integración; pudo avanzar independientemente.
- No compiles una APK, no dispares el workflow oficial, no cambies la firma Android ni manipules secretos sin una nueva solicitud del usuario. Las comprobaciones Java/recursos y pruebas aisladas sí forman parte del trabajo.

## Referencias visuales exactas

Están guardadas en esta misma rama, para que no dependas de imágenes del chat:

1. `docs/design/music/player-proposals.png`: el usuario escogió **el diseño 2, Órbita**, segundo teléfono de izquierda a derecha. Los diseños 1, 3 y 4 no son la elección.
2. `docs/design/music/mini-player-proposals.png`: para el reproductor minimizado escogió **el diseño 4, Doble segmento**, segunda fila, columna derecha.

Abre ambas imágenes antes de continuar. Son referencias conceptuales, no capturas que demuestren que el código está terminado. Debes acercar el resultado real a esas elecciones.

## Diseño definitivo acordado

### Reproductor completo: Órbita

- Carátula circular grande, centrada, con un anillo fino de progreso musical a su alrededor y un indicador de posición. El anillo es también una superficie para buscar una posición en la canción y debe ser accesible.
- Sin rotación decorativa de la carátula ni visualizadores nuevos.
- Debajo, tiempo transcurrido y duración; título de la canción y artista centrados; acción de favorito/perfil conservada.
- Controles elegantes: anterior, pausa/reproducción circular predominante y siguiente dentro de una cápsula horizontal delineada; aleatorio y repetir en los extremos.
- Velocidad, Letras, Temporizador y Cola siguen disponibles, con iconos finos, círculos o píldoras. **Ningún botón cuadrado ni con forma de cuadrado redondeado.** La carátula circular es parte esencial del diseño.
- Sección «A continuación» con las próximas canciones. Conserva acceso a la cola completa y las funciones existentes de reproducción.
- Acentos del tema activo y compatibilidad con modo claro/oscuro. La imagen elegida es oscura, pero no hay que imponer ese modo.
- **Sin animaciones de iconos**: los cambios reproducción/pausa deben ser inmediatos. Sí se autorizó animar la geometría de la carátula/cabecera y el desplazamiento de letras.

### Cabecera superior personalizada

- Una bolita independiente para retroceder, una cápsula central con el nombre del chat/origen de reproducción, y otra bolita independiente para los tres puntos.
- La cápsula se ajusta al texto como la cabecera de contacto de las conversaciones de FlexyGram, con límites seguros para nombres largos, fuentes grandes y pantallas estrechas.
- Los tres puntos abren el menú real del reproductor y volver mantiene su función. No animar esos iconos.
- Cápsula y bolitas soportan blur y glass cuando los ajustes existentes los permiten. Usa el motor nativo y respeta ahorro de energía, API y preferencia; ofrece una superficie sólida legible si los efectos están desactivados/no disponibles. No simules glass únicamente con transparencia ni cambies la configuración global.

### Transición al navegar por «A continuación»

El usuario confirmó expresamente este comportamiento: «al subir, la carátula y el reproductor quedan como tarjetas superiores; al bajar, una animación fluida continua regresa la carátula y todo a su lugar».

- El disparador es **el scroll vertical**, no tocar Cola ni un botón adicional.
- Mientras se sube por la lista, la carátula circular grande se reduce y se integra visualmente en la cápsula de origen; los controles principales pasan a esa cabecera compacta.
- Al terminar, la cabecera queda fija: carátula pequeña, nombre del chat, información musical que quepa y controles reales de pausa/siguiente. Volver y menú permanecen independientes y utilizables.
- Al bajar, la misma transformación se invierte continuamente hasta recuperar la composición grande, incluida la carátula con anillo. No debe saltar a su posición ni reiniciarse con cada cambio de dirección.
- Una sola carátula real y un solo propietario de reproducción; no duplicar decodificación ni reproducir el audio de nuevo.
- Evita controles duplicados visibles/tocables, superficies que intercepten la lista, iconos animados, zonas de toque solapadas y saltos de layout. Verifica scroll rápido, cambio de sentido y cambio de canción mientras está contraída.

### Tarjeta minimizada: Doble segmento

- Izquierda: carátula pequeña, título y artista, progreso discreto dentro de ese segmento.
- Derecha: cápsula separada con pausa/reproducir, siguiente y **X de cerrar**; espacio visible entre los dos segmentos.
- Compacta y con acentos del tema. Blur real cuando esté habilitado en ajustes, y alternativa sólida al deshabilitarlo.
- Actualiza tanto `PlayerBarView` (barra en conversación) como `PlayerMiniView` (mini inferior), preservando las rutas de abrir, minimizar, burbuja y cerrar.
- La X detiene/cierra la reproducción mediante el comportamiento nativo; tocar el contenido abre el reproductor. No sacrificar los controles esenciales para hacer sitio al texto; adaptar nombres largos y fuentes grandes.

### Pantalla de letras

El usuario informa que actualmente la letra no aparece bien y no se sincroniza. Investiga la integración real, no afirmes haber reproducido el fallo físico a partir de pruebas aisladas.

- Letras abre una vista dedicada, amplia, coherente con Órbita, no un bloque diminuto entre controles.
- Cabecera compacta con canción/carátula y reproducción accesible; volver regresa al reproductor.
- Versos grandes y legibles; verso activo con acento del tema, anteriores/siguientes atenuados pero **sin blur que impida leerlos**.
- Sigue el tiempo real del motor, también tras seek, pausa, reanudación, cambio de velocidad y canción.
- Desplazamiento suave para seguir el verso actual. Si el usuario desplaza manualmente, deja leer y muestra «Volver al verso actual»; no secuestres inmediatamente el scroll.
- Tocar un verso con timestamp permite buscar ese instante.
- Si solo existen letras sin tiempos, muestra que no están sincronizadas; no inventes marcas de tiempo ni animaciones de sincronización.
- Mantén estados de búsqueda, permiso existente, error/reintento, sin resultados e instrumental; no inventes letras ni extraigas textos de canciones equivocadas.
- Respeta la identidad de canción/cuenta, cancelación de solicitudes viejas y caché. No reescribas innecesariamente los proveedores ya existentes.

## Cambios iniciados en esta rama

Ruta Java común: `TMessagesProj/src/main/java/app/exteraless/player/`.

Nuevos:

- `OrbitMotion.java`: interpolación pura en función del scroll, sin animador independiente.
- `OrbitArtwork.java`: contiene el `CoverImage` real, recorte circular, anillo dibujado, búsqueda táctil, cancelación y acciones de accesibilidad.
- `OrbitPlayerLayout.java`: nueva escena con contenido desplazable, cabecera fija, tres superficies, carátula única que se contrae hacia la cápsula, controles compactos y distribución separada de letras. Incluye adaptación inicial de cabecera a ventanas estrechas/fuentes grandes.
- `MusicGlassRenderer.java`: puente API 33+ al motor `blur3` usado por las cabeceras del cliente, con source RenderNode y factory. **Todavía no se ha validado el puente real en GPU ni compilado contra todos sus tipos de producción.**

Modificados:

- `PlayerSheet.java`: conecta Órbita bajo `BuildConfig.CONNECTED_ALPHA`, mueve las vistas existentes a la nueva escena, reutiliza listeners, usa `MediaController.getProgressMs(message)` para letras/tiempos y fallback cuando no está disponible. Añade `visualContent()` para adaptar la transición mini/completo. Al estar en letras, volver sale de esa vista.
- `ControlsRow.java`: botón principal circular y comienzo de un contorno de cápsula entre anterior/siguiente. El tamaño principal se ha cambiado a 72 dp en el camino conectado.
- `CompactPlayerQueue.java`: constructor configurable, acotado a 12 próximas filas; se conserva la cola completa por su entrada existente. Revisa si este adelanto basta para la navegación acordada; no convertir una cola enorme en miles de Views.
- `MusicBlurSurface.java`: soporte inicial de dos regiones separadas, superficies elevadas de cabecera y puente glass opcional. Conserva capturas reducidas, notificaciones de layout/scroll, límites y liberación al desmontar.
- `PlayerBarView.java`, `PlayerMiniView.java`: inicio de aspecto doble segmento y progreso dentro del segmento de contenido; ajustes de altura y espacio de texto. **El resultado aún necesita comparación visual con la referencia 4.**
- `LyricsView.java`: proveedor del reloj real, ticker de 150 ms solo para letras sincronizadas visibles y en reproducción, acción localizada de volver al verso, desactivación del blur de versos, color activo adaptado al tema y limpieza del reloj al desmontar. Estos cambios deben terminar de probarse.
- `values/flexy_beta.xml`, `values-es/flexy_beta.xml`: nueva cadena `FlexyMusicFollowLyrics`.

Pruebas:

- Se ampliaron `tools/connected_alpha/music_visual/stubs.py` y `MusicVisualTest.java.in` para incluir la escena Órbita real y probar contracción/retorno, anillo, controles, letras como panel, tamaños y fuentes, y capturas claro/oscuro.
- Se inició `tools/connected_alpha/lyrics_ui/` para probar el **LyricsView real con RecyclerView real**, parser y reloj con dependencias explícitas.

## Estado real de validación y qué falta

1. La prueba Android musical aislada llegó a **25 pruebas aprobadas**, pero después hubo cambios adicionales en recorte circular, colores de cabecera, reloj de letras y tamaño/contorno de controles. **Hay que repetirla sobre el estado actual.** No equivale a probar todo `PlayerSheet` ni Telegram en dispositivo.
2. El nuevo conjunto `lyrics_ui` compila sus fuentes pero sus **4 pruebas fallan al inicializar RecyclerView** con `NoClassDefFoundError: androidx/recyclerview/R$attr`. El harness extrae `classes.jar` de los AAR, pero falta proporcionar correctamente los R/recursos de las bibliotecas. Corrige el entorno de prueba conservando RecyclerView real; no lo tapes marcando las pruebas como omitidas ni sustituyendo el componente por uno falso.
3. El harness musical usa un doble explícito de `MusicGlassRenderer` que falla si se intenta entrar en su ruta GPU. Sus capturas con Canvas software **no prueban glass**. Comprueba las firmas/tipos reales del puente y prueba blur/glass con los efectos activados y desactivados donde sea viable.
4. Las capturas aisladas anteriores no demostraban todavía el acabado exacto de la referencia. Debes revisar carátula completamente circular, anillo exterior, título/autor/favorito centrados, cápsula de controles, contraste de bolitas/cabecera y doble segmento sin una superficie continua detrás.
5. Revisa cuidadosamente el orden de dibujo tras entrar/salir de Letras: `header.bringToFront()` puede dejar la carátula detrás de la cápsula al regresar. La mini carátula debe seguir visible en su posición final.
6. Revisa la trayectoria de `updateCollapse()`: combina una posición desplazada con interpolación; en puntos intermedios puede subir demasiado antes de integrarse. Debe mantenerse visible y no atravesar indebidamente la zona de estado/cámara. Respeta insets reales. No basta comprobar solo inicio/final.
7. Evita targets invisibles aún tocables o accesibles durante el cambio entre controles grandes/compactos. Prueba posiciones intermedias, no solo el estado totalmente contraído. Comprueba que Letras permite regresar y que los tres puntos funcionan en todos los estados.
8. Valida el gesto del anillo frente al scroll del contenedor, el salto de 359° a 0°, cancelación/soltar, TalkBack y orientación RTL. No generar seeks accidentales al intentar recorrer la lista.
9. Verifica toda la integración de `PlayerSheet`: reaprovecha componentes y listeners, pero el antiguo `PlayerLayout` permanece como camino legado. Comprueba que sus métodos, morph de mini/completo, Back y gestión de letras no siguen usando dimensiones del contenedor desacoplado.
10. Comprueba liberación de listeners, solicitudes, RenderNodes/bitmaps y relojes al cerrar, cambiar de canción/cuenta o salir. Revisa que las tres superficies de cabecera no generen capturas de fondo continuas estando quietas ni retengan bitmaps con efectos desactivados.
11. Comprueba sincronización real con posición del motor, velocidades y seeks. Conserva fallback sin tiempos y estados de error honestos. En el traspaso no hay prueba física ni prueba de servicio en segundo plano que certifique el fallo resuelto.
12. Ejecuta recursos/sintaxis y pruebas generales al terminar; agrega el harness de letras UI al workflow de comprobaciones cuando funcione, sin ejecutar una compilación APK por iniciativa propia. No reutilices como resultados actuales los números de suites de tareas anteriores.

## Comandos y herramientas disponibles en el entorno de origen

- JDK 21: `/workspace/.flexygram/jdk/jbrsdk-21.0.11-linux-x64-b1163.125`
- Python: `/workspace/.flexygram/venv/bin/python`
- SDK: `/workspace/.flexygram/android-sdk` (API 37, build-tools 36)
- Maven: `/workspace/.flexygram/maven/apache-maven-3.9.9/bin/mvn`
- Los caminos pueden no existir en un entorno nuevo: usa equivalentes configurados; no solicites secretos en el chat.

Ejecutar con JAVA_HOME/PATH apropiados:

```sh
python tools/connected_alpha/music_visual/run.py --sdk-root "$ANDROID_HOME" --output-dir /tmp/flexy-orbit-widgets
python tools/connected_alpha/lyrics_ui/run.py --sdk-root "$ANDROID_HOME" --output-dir /tmp/flexy-orbit-lyrics-ui
python tools/connected_alpha/lyrics_runtime/run.py --sdk-root "$ANDROID_HOME" --output-dir /tmp/flexy-orbit-providers
python -m pytest tests -q
```

Se puede pasar `--maven /ruta/a/mvn` a los harness. Ninguno de esos comandos construye la APK de FlexyGram.

Logs/capturas temporales del entorno original, no necesariamente disponibles en otra sesión:

- `/tmp/flexy-orbit-widget-probe.log` y `/tmp/flexy-orbit-widget-probe/orbit-light.png`, `orbit-dark.png`.
- `/tmp/flexy-orbit-lyrics-ui.log` (fallo de R de RecyclerView).

## Entrega esperada

Termina Órbita y Doble segmento según las dos referencias elegidas, con transición reversible ligada al scroll y letras realmente legibles/sincronizadas cuando la fuente lo permita. Conserva todas las funciones existentes del reproductor y los colores del tema. Entrega cambios en rama propia y explica qué verificaste, qué sigue sin validación física y si hay limitaciones reales. No declares que el diseño es «exacto» o que no tiene errores basándote solo en una ilustración o en pruebas parciales.
