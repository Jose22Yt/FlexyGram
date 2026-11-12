# Beta 51 — animaciones de desplazamiento

Rama oficial `codex/flexygram-beta-glass`, versión preparada `1.0.0-beta.51` / `1340`.
El propietario pidió implementar los tres estilos elegidos y **no compilar APK**.
El commit usa `[skip ci]` para impedir que el push active la compilación automática.

## Controles

Ajustes de FlexyGram → Pantalla principal → Animaciones al desplazarse:

- Lista de chats: Sin efecto / Rueda 3D / Perspectiva inclinada / Deslizamiento lateral.
- Dentro de las conversaciones: las mismas cuatro opciones, independientes de la lista principal.
- Intensidad compartida: Suave (0,7), Marcada (1,0), Intensa (1,3). Marcada es el valor inicial;
  ambas listas empiezan en Sin efecto, sin cambiar elecciones anteriores.

Las preferencias se conservan al reiniciar y pertenecen a la sección Pantalla principal
al exportar/importar la configuración con FlexyStudio. Los valores desconocidos vuelven
a Sin efecto/intensidad Marcada. Los textos tienen recursos español e inglés.

## Movimiento y coste

Los dos consumidores usan exactamente `ScrollEffectMotion`, `ScrollEffectGeometry` y
`ScrollEffectsController`. La posición y la velocidad se normalizan por el espacio
visible; la intensidad no se reduce dentro de una conversación. La integración analítica
usa tiempo monotónico real, no una cantidad fija por frame: 60/120/144 Hz y frames
irregulares recorren la misma respuesta para el mismo historial de entradas.

Rueda 3D proyecta cada fila alrededor de un cilindro, con hasta 58° por la intensidad
Marcada, ligera reducción horizontal y corrección de centros para comprimir los bordes.
Perspectiva inclina la superficie común según la dirección, hasta 13°/7°/1,8° en los
respectivos ejes. Deslizamiento lateral conserva el texto recto y desplaza los elementos
hasta un 18 % del ancho en los extremos. Las magnitudes se modulan con la velocidad;
se conservan continuas al invertir. No son mediciones de fluidez de un teléfono.

Se usan Camera/Matrix reutilizados sobre el Canvas existente. No se crean bitmaps,
capas hardware, efectos blur, animadores por fila ni layouts nuevos en cada frame.
Los cuadros adicionales terminan al asentarse la respuesta; no queda un reloj en reposo.
Los cambios de posición programáticos en estado IDLE no disparan el efecto.
La separación de la ventana elimina el estado. Las animaciones globales desactivadas,
la escala Android en cero y la exploración táctil de accesibilidad inhiben el efecto;
la consulta de escala del sistema contempla Android 24/25 sin llamar una API26.

## Integración nativa

Solo participan las filas reales de conversaciones en la pantalla principal y los
mensajes/acciones de la conversación. Cabeceras, fondo y composer permanecen en sus
coordenadas. Se proyectan todos los pases de mensajes, incluidos fondos dibujados por
el padre, horas, nombres, captions y reacciones. Las piezas visibles del mismo álbum
comparten un ancla y una proyección, para no separar sus imágenes del fondo común.

No se escriben propiedades de traslación, escala o pivote de las celdas. Se conservan
los animadores, swipe-to-reply y selecciones de Telegram. En las transiciones de ítems,
menús y vídeo externo activo se suspende el efecto para no desalinear sus overlays.

Al tocar una lista todavía transformada se busca la fila bajo el punto mediante la
matriz inversa. Ese desplazamiento inicial se conserva en el resto del gesto: los
deltas, touch slop, velocidad y distancias entre punteros siguen siendo los nativos.
El evento original no se modifica y la copia se recicla en `finally`. El efecto se
asienta suavemente en vez de saltar a cero al interrumpir un fling. También se aplica
el desplazamiento a la observación de gestos propios de las burbujas.

## Validación sin APK

`tests/test_scroll_effects.py` ejecuta el código de producción de movimiento/geometría,
preferencias y controlador con dobles explícitos. Cubre continuidad en inversión,
60/120/144 Hz, frames irregulares y perdidos, intensidad normalizada, reposo, separación,
animaciones/accesibilidad desactivadas, persistencia y reciclado de eventos ante errores.
El wrapper de touch real se ejecuta para comprobar que no cambia el delta del gesto.

La comprobación opcional de tipos compila las cinco clases nuevas contra un `android.jar`
real, con los servicios/widgets propios de Telegram declarados como dobles. No usa
Gradle, no empaqueta recursos y no genera APK:

```sh
FLEXY_SCROLL_ANDROID_JAR=/ruta/android.jar python -m pytest tests/test_scroll_effects.py -q
python -m pytest tests/ -q -p no:cacheprovider
```

La revisión de sintaxis comprende también ChatActivity, DialogsActivity y RecyclerListView.
La compilación de tipos aislada no sustituye la compilación integrada de Android.

## Revisión posterior de fluidez

La [auditoría de coste y continuidad](BETA51_SCROLL_EFFECTS_AUDIT.md) documenta las
optimizaciones posteriores de proyección, álbumes y movimiento con velocidad continua.
Se mantienen los tres estilos, las intensidades y la preparación sin APK.

## Aceptación pendiente en dispositivo

Con una APK solicitada posteriormente, comparar ambos espacios con cada efecto e
intensidad, scroll lento/rápido y reversas a 60/120/144 Hz cuando el equipo lo permita.
Medir FrameTimeline/input-to-present, CPU/GPU y temperatura; no afirmar FPS a partir
de los tests JVM. Comprobar fotos y álbumes, audios, mensajes altos, reacciones,
pulsación prolongada durante fling, swipe-to-reply, selección, carpetas, historias,
teclado, RTL, rotación, acceso con lector de pantalla y retorno desde segundo plano.

Resultado de esta revisión: **410 passed, 39 skipped** en la suite general (189,51 s).
Las **22 comprobaciones enfocadas** de scroll/blur también pasan y las **8 pruebas del
módulo** pasan de nuevo tras el ajuste final de anclas para mensajes altos. Se comprobó
el tipado de las cinco clases nuevas con el jar real de Android API35 y la sintaxis de
los 11 archivos Java nuevos/modificados. Cinco pruebas adicionales de FlexyStudio
pasan. No se ejecutó una compilación de APK ni una medición física.

Las matrices por ancla se reutilizan en una caché acotada de 64 entradas. Su estado se
incluye en el hash de captura del desenfoque para evitar conservar una captura obsoleta
cuando la lista termina de asentarse. Los mensajes más altos que el viewport usan el
centro de su parte visible; no giran alrededor de un pivote lejano fuera de pantalla.
