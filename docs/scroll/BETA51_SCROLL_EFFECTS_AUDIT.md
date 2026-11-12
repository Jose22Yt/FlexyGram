# Beta 51 — revisión de fluidez y coste de los efectos

Base comparada: `0accf3a2f9703fb2506485eec293b2a61f109990`, rama oficial
`codex/flexygram-beta-glass`. Se conserva la versión preparada 1340; esta revisión
optimiza los mismos tres estilos y **no compila APK**. El commit usa `[skip ci]`.

## Evaluación

La primera implementación ya reutilizaba matrices, mantenía las propiedades nativas
de las celdas y detenía los cuadros adicionales al asentarse. Aun así, había trabajo
repetido y una discontinuidad de velocidad al cambiar el objetivo de la animación.
Esta revisión corrige esos puntos sin reducir las amplitudes ni separar el motor
entre la lista principal y las conversaciones.

### Movimiento continuo

La respuesta exponencial anterior conservaba posición, pero cambiaba instantáneamente
su velocidad al invertir el objetivo o empezar la salida. Ahora amplitud y dirección
usan un resorte críticamente amortiguado con solución analítica y velocidad conservada.
No se añaden rebotes, keyframes ni animadores por fila. Al invertir o soltar, el nuevo
objetivo modifica la aceleración; posición y velocidad siguen continuas.

El avance divide exactamente el intervalo que cruza los 80 ms de expiración de entrada.
Las frecuencias son 56 s⁻¹ para entrada de amplitud, 42 s⁻¹ para salida y 48 s⁻¹ para
dirección. La salida termina solo con amplitud y velocidad residuales pequeñas; no
permanece un reloj en reposo. El primer evento deja de inventar un intervalo de 1/60 s:
la velocidad se calcula cuando ya existe una duración observada.

Se conservan los ángulos/desplazamientos originales de cada estilo y las intensidades
0,7 / 1 / 1,3. La respuesta es común a ambos espacios. La prueba numérica comprueba
posición y velocidad en los puntos de inversión/salida; otra compara el mismo historial
de entradas a 60/120/144 Hz y sin cuadros intermedios, incluyendo pausas y reversas.
Estas pruebas describen el modelo temporal, no los FPS del renderizador Android.

### Menos cálculos en el dibujo

Perspectiva inclinada tiene un solo pivote para el viewport completo: su matriz era
idéntica en todas las filas. Ahora usa una única entrada en la caché por fotograma,
también para fondos, captions y reacciones. Deslizamiento lateral utiliza directamente
`Matrix.setTranslate`: no pasa por Camera ni genera una proyección 3D identidad.
Rueda 3D conserva las proyecciones por ancla que necesita su curvatura, pero omite
las rotaciones nulas de los otros ejes. La profundidad de Camera se configura solo
al cambiar el ancho y se conserva al restaurar su estado.

Comparación ejecutada sobre el controlador de producción antes/después, con Camera,
Canvas, Matrix y servicios Android como dobles explícitos. La escena tiene 30 filas
y seis pases por fila en un fotograma; se cuentan operaciones, no tiempo de GPU:

| Operación | Antes | Después |
| --- | ---: | ---: |
| Proyecciones Camera, Rueda 3D | 30 | 30 |
| Proyecciones Camera, Perspectiva inclinada | 30 | 1 |
| Proyecciones Camera, Deslizamiento lateral | 30 | 0 |
| Rotaciones Camera de Rueda 3D | 90 | 30 |
| Configuraciones de profundidad de Rueda 3D en el primer fotograma | 30 | 1 |
| Lecturas de hermanos para 10 álbumes de 3 celdas y seis pases | 5.400 | 300 |

Los límites de cada álbum se resuelven una vez y se reutilizan en todos sus pases.
La caché tiene como máximo 32 grupos, se crea solo al necesitarla y se invalida al
comenzar el dibujo, al desplazar, al relayout y al separar la lista. Se liberan las
referencias a los grupos. El desbordamiento conserva el recorrido correcto sin hacer
crecer la caché. La caché de matrices sigue limitada a 64 entradas.

Los eventos con `dy == 0` ya no solicitan un redibujado del efecto. No se introduce
ninguna escritura de preferencias, bitmap, capa hardware o temporizador por cuadro.
La prueba de asignaciones HotSpot ejercita 20.000 avances y los tres modos después del
calentamiento: exige un presupuesto total menor de 4 KiB, no un objeto por frame.
Esto no mide las asignaciones de todo Telegram ni el recolector de Android.

### Coherencia de captura y pulsación

Antes, una nueva entrada podía actualizar el movimiento mientras algunas matrices
seguían en la caché del dibujo anterior: el hash de blur y una matriz pendiente podían
representar fases diferentes. Ahora amplitud, dirección, intensidad y ancho se fijan
para cada dibujo; tanto las matrices como el hash leen esa misma instantánea. Las
entradas y las pulsaciones no cambian la pose ya mostrada antes del siguiente dibujo.

La matriz inversa se reutiliza cuando varias filas comparten proyección. La matriz
mutable usada al desbordar la caché nunca conserva una inversa obsoleta. Se mantienen
el mapeo inicial y el desplazamiento constante del gesto, con sus deltas y velocidad
nativos. La revisión no cambia fricción, fling, adaptadores, tiempos de red, selección,
notificaciones, reproducción, estilos ni preferencias del usuario.

## Verificación y límites

`tests/test_scroll_effects.py` y `tests/test_scroll_effects_audit.py`: **14 passed**,
incluido el tipado de las cinco clases del módulo contra Android API35 real.
Las nuevas regresiones ejecutan código de producción para continuidad de velocidad,
historiales de entrada a diferentes frecuencias, presupuesto de proyecciones, hash
estable ante entradas, inversa lateral, caché de álbumes y liberación de sus referencias.
Se conserva la comprobación de que los controles desactivados y las listas en reposo
no programen cuadros.

Reproducción sin empaquetar la aplicación:

```sh
FLEXY_SCROLL_ANDROID_JAR=/ruta/android.jar python -m pytest tests/test_scroll_effects.py tests/test_scroll_effects_audit.py -q
python -m pytest tests/ -q -p no:cacheprovider
```

Los recuentos anteriores prueban menos trabajo redundante. No prueban FPS, consumo,
latencia input-to-present ni satisfacción subjetiva en un teléfono. Cada efecto
continúa añadiendo transformaciones al dibujo normal; no se promete coste cero.
Con una APK solicitada posteriormente, medir FrameTimeline, CPU/RenderThread/GPU y
memoria con la misma escena, frecuencia, tipo de compilación y temperatura. Comprobar
mensajes altos, álbumes, reacciones, pausas, inversiones rápidas, pulsación durante
fling, swipe-to-reply, selección, RTL, teclado y retorno desde segundo plano.

Resultado final: **416 passed, 39 skipped** en la suite general (182,02 s). Las
**14 comprobaciones enfocadas** se ejecutaron de nuevo tras el ajuste final de
rotaciones/profundidad y también pasan. La sintaxis de los Java modificados y
`git diff --check` son correctos. No se ejecutó ningún build de APK.
