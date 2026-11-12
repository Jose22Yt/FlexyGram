# Beta 52 — scroll suave e interacción durante el efecto

Rama oficial `codex/flexygram-beta-glass`, versión `1.0.0-beta.52` / build `1341`.
Revisión a partir de `09bd57962a65b3b3d577ff5fe933b8421f0d9451` tras la prueba del
propietario: demasiada intensidad, cambios bruscos y necesidad de poder interactuar
sin esperar a que termine la animación.

## Fuerza más baja en ambas listas

Se conservan los tres estilos, los selectores independientes y la intensidad
compartida. Las preferencias existentes no se reescriben. Todos los niveles son
más suaves; la intensidad intermedia se muestra como **Equilibrada / Balanced**.

| Magnitud nominal, antes de velocidad/intensidad | Beta 51 | Beta 52 |
| --- | ---: | ---: |
| Rueda 3D, inclinación máxima | 58° | 26° |
| Rueda 3D, reducción horizontal | 6,5 % | 1,8 % |
| Perspectiva, ejes X/Y/Z | 13° / 7° / 1,8° | 5° / 2,5° / 0,4° |
| Lateral, proporción del ancho | 18 % | 6 % |

El objetivo de amplitud pasa de 0,72–1 a 0,30–0,85, con una curva saturada suave
sobre la velocidad normalizada por viewport. Una media exponencial de 60 ms filtra
la velocidad de entrada; no demora el scroll nativo ni agenda trabajo posterior.
Los callbacks del mismo instante se agrupan como una sola muestra, recalculada desde
su estado original. No se inventa un intervalo mínimo de 1 ms ni se multiplica el
filtro por el número de callbacks de un mismo instante. La respuesta analítica común
mantiene posición y velocidad al invertir el scroll; no usa rebotes predeterminados.

## Pulido de Rueda 3D

La versión anterior mezclaba la proyección de 58° con una inclinación que ya había
sido modulada por amplitud. Durante la entrada/salida, la separación de centros y el
ángulo visible podían discrepar y comprimir demasiado las filas. Ahora ambos se
calculan con el ángulo mostrado. Cerca de cero se usa una expansión estable para
no dividir entre cero ni perder precisión. La prueba numérica comprueba que la
variación de la separación concuerde con el coseno de la inclinación efectiva a
lo largo del asentamiento, en todos los niveles.

Las filas normales mantienen el centro de su geometría, incluso cuando quedan
parcialmente recortadas: el clipping no desplaza su pivote. Los mensajes/álbumes
próximos al tamaño del viewport pasan gradualmente al ancla acotada de las piezas
muy altas. Se elimina el salto que producía un cambio de rama abrupto al superar
la altura del viewport. Se conservan el ancla compartida del álbum y las cachés
acotadas de geometría/matrices, así como la pose común para captura y pulsaciones.

## Toque prioritario, sin esperar a la animación

RecyclerListView selecciona filas para pulsación cuando su estado nativo es IDLE.
Durante un fling, el primer DOWN podía dedicarse solo a frenarlo. Ahora, únicamente
cuando el efecto está activo, se resuelve primero la posición mostrada con la
proyección inversa y se detiene la inercia nativa antes de entregar **ese mismo DOWN**
a la lista. Así la fila/burbuja puede recibir la pulsación inicial y el UP posterior,
sin un toque extra ni una espera a que el efecto llegue a cero.

La retirada visual toma la amplitud y dirección de la última pose mostrada, no una
fase adelantada por una entrada que aún no se dibujó. Usa una envolvente quintica
monótona de **96 ms**, con velocidad/aceleración nulas en sus extremos. No aumenta
antes de retirarse ni añade un rebote. La acción nativa se entrega inmediatamente:
los 96 ms solo describen la salida visual y no son un retraso del clic, una espera
del menú o un bloqueo de navegación.

Se mantiene el desplazamiento inicial constante del evento para preservar deltas,
touch slop, velocidad nativa y separación de punteros. La copia del evento se recicla
en `finally`; el evento original no cambia. La lista no se desactiva, no retiene
DOWN/UP ni espera un callback para abrir el chat. Un nuevo arrastre puede reanudar
el efecto durante esa retirada. Pulsación prolongada, doble toque, reacciones,
selección y navegación conservan sus rutas nativas. Separar la vista elimina el
estado pendiente y no deja un reloj periódico.

## Verificación local

Las pruebas de `test_scroll_effects.py`, `test_scroll_effects_audit.py` y
`test_scroll_effects_polish.py` ejecutan el código de producción con hosts explícitos.
Cubren amplitudes reducidas, coherencia de proyección, pivote al cruzar bordes y
altura de viewport, continuidad, 60/120/144 Hz, callbacks agrupados, salida monótona
con plazo acotado, reanudación antes de terminar, cuadros en reposo, cachés, tipos
Android y reutilización de recursos. El host del toque simula la puerta nativa IDLE:
comprueba que el mismo DOWN interrumpe el estado SETTLING, selecciona la fila y produce
el clic con el primer UP, aunque el efecto siga activo. También comprueba deltas,
reciclado y limpieza de eventos ante errores.

La compilación de tipos aislada utiliza Android API35 real; no empaqueta APK ni
sustituye la compilación integrada. No se han medido FPS, jank, temperatura, GPU o
latencia input-to-present en un teléfono en esta sesión. Hace falta comprobar la
sensación con la nueva APK, especialmente contactos/chats, enlaces, reacciones,
pulsación prolongada durante fling, álbumes, selección, swipe-to-reply y volver atrás.

## Compilación y entrega

Las comprobaciones locales se completan antes de publicar. El commit utiliza
`[skip ci]` y se solicita una sola compilación manual del workflow oficial
`ui-beta-debug.yml` sobre la rama oficial. Por petición del propietario, se deja
sin supervisión: no se consulta el progreso, no se leen logs ni se descarga o valida
el APK resultante. La confirmación de solicitud no declara una compilación exitosa.

Resultado local final: **422 passed, 39 skipped** en la suite general (196,23 s).
Las **30 comprobaciones enfocadas** de scroll, touch y navegación también pasan,
incluido el tipado aislado contra Android API35. La sintaxis Java y `git diff --check`
son correctos. Estas verificaciones se completaron antes de solicitar la compilación.
