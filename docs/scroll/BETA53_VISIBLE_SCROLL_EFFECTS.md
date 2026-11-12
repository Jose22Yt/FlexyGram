# Beta 53 — recuperar la presencia de los efectos

Fuente: `1.0.0-beta.53` / build `1342`, rama oficial `codex/flexygram-beta-glass`.
Base: `a90b8441ca2cea10432b1ae18537bef28050900a` (beta 52).

El propietario informa de que los efectos dejaron de apreciarse tras reducirlos.
La corrección recupera su presencia y elimina reinicios generales innecesarios,
conservando el filtrado, la geometría coherente y la interrupción por toque.

## Calibración visible

En beta 52 se redujeron simultáneamente la geometría nominal y el objetivo de amplitud
inicial. Las reducciones se multiplicaban: un arrastre corto podía mostrar solo una
inclinación o traslación muy pequeña. Las pruebas anteriores comprobaban límites
máximos, continuidad y corrección, pero no exigían presencia mínima en ese recorrido.

| Parámetro | Beta 52 | Beta 53 |
| --- | ---: | ---: |
| Objetivo de amplitud según velocidad | 0,30–0,85 | 0,65–0,90 |
| Rueda 3D, ángulo nominal | 26° | 40° |
| Rueda 3D, reducción horizontal nominal | 1,8 % | 3 % |
| Perspectiva, ejes X/Y/Z nominales | 5° / 2,5° / 0,4° | 9° / 4,5° / 0,7° |
| Lateral, proporción nominal del ancho | 6 % | 12 % |

Son magnitudes previas a modulación por amplitud, posición e intensidad. Se usa una
calibración intermedia respecto a la beta 51 original (58°, 13°/7°/1,8° y 18 %).
El efecto mantiene presencia a velocidad baja y gana énfasis al desplazar más rápido,
sin abandonar el filtro temporal ni la continuidad del movimiento.

Las tres opciones y el ajuste de intensidad continúan en Pantalla principal. Se
conservan sus valores guardados y la independencia de selección entre lista de chats
y conversaciones. No se modifica una elección explícita Sin efecto ni se fuerzan las
animaciones del sistema. Los dos espacios usan el mismo motor y la misma intensidad.

## Reinicios que ocultaban el efecto

- En ChatActivity se reiniciaba el estado completo siempre que el animador de ítems
  estuviera activo. Se permite ahora la composición Canvas con las animaciones nativas
  de los elementos. La animación de una fila no apaga el efecto de todo el chat.
- En la pantalla principal se hacía el mismo reinicio general. Las filas móviles que
  DialogsItemAnimator dibuja separadamente conservan su representación nativa y se
  excluyen tanto de la transformación como de la proyección inversa del toque; las
  demás filas mantienen el efecto. Se conservan los guardas de transición de página.
- `destroyTextureView()` puede retirar el contenedor de vídeo de contentView sin poner
  a null su referencia ni cambiar su visibilidad. Comprobar solo referencia/VISIBLE
  podía seguir reiniciando el efecto después de retirar el reproductor. El guarda
  comprueba ahora que el contenedor siga siendo hijo de contentView y esté visible.
  Se conserva la suspensión durante vídeo externo realmente adjunto y menús externos.

## Se conserva el pulido anterior

La proyección de Rueda 3D sigue usando el ángulo mostrado para calcular separación y
curvatura; no se restaura la mezcla de ángulos que comprimía excesivamente los centros.
Se mantienen los pivotes de filas normales y la transición gradual en elementos altos.

También se conservan la salida visual monótona de 96 ms al tocar, la detención de
inercia antes de entregar ese mismo DOWN a la lista y el mapeo desde la pose mostrada.
El toque puede abrir el chat/pulsar la burbuja mientras la salida visual aún termina.
Un nuevo arrastre puede retomarla; no hay espera de animación ni desactivación de la
interfaz. Las cachés y los atajos de proyección mantienen sus límites anteriores.

## Regresiones y límites

La nueva prueba de presencia ejecuta movimiento y geometría de producción con un
arrastre de 3 píxeles por muestra, viewport de 800 y ancho de 400, hasta 80 ms.
En los tres niveles exige rueda mayor de 10°, perspectiva mayor de 2° y lateral
mayor de 12 píxeles en los puntos comprobados. Son umbrales numéricos de esa escena,
no una medición subjetiva ni de FPS de un teléfono.

Otras pruebas ejecutan los preámbulos reales de dibujo: una animación de ítems o un
vídeo retirado no reinician todo el efecto; un vídeo realmente adjunto, un menú y las
transiciones especiales conservan su tratamiento. Se ejecuta también el filtro real
de filas móviles para asegurar que sus coordenadas nativas no reciban una inversa
que no corresponde al dibujo. Se mantiene la suite de continuidad, toque, cachés,
recursos y comprobación de tipos con el jar real de Android API35.

El propietario pidió compilar. Tras las comprobaciones locales se publica un commit
con `[skip ci]` y se solicita una sola compilación manual del workflow oficial sobre
la rama actual. Se deja sin supervisión: no se consultan progreso, logs o artefactos,
ni se declara el resultado del APK como verificado. La apariencia final se debe
comprobar con la nueva APK en el dispositivo.

Resultado final: **425 passed, 39 skipped** en la suite general (207,98 s).
Las **23 comprobaciones enfocadas** de efectos pasan, incluida la comprobación de
tipos contra Android API35 real. Se verificaron sintaxis Java y `git diff --check`
antes de publicar y solicitar la compilación.
