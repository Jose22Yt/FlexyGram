# Fluidez: cancelación y sustitución de animaciones

Revisión de controladores de interacción de burbujas, selección/menú, efectos de
reacciones, snapshots de borrado, máscaras del avatar y mini reproductor. Se
priorizan correcciones con un caso reproducible, conservando física y diseño.
No se cambian protocolos, envío de mensajes, almacenamiento ni preferencias.

## Burbujas al tocar

`BubbleTapMotion` conserva sus resortes, objetivos y velocidades. Añade una
identidad de generación para que un redibujado que cancela o reemplaza un gesto
no pueda volver a programar el fotograma antiguo. La protección cubre tanto la
pulsación inicial como la ejecución de cada fotograma.

Después de redibujar se comprueba el estado actual de los resortes: si el gesto
cambia de objetivo durante el callback, el controlador continúa hacia el objetivo
nuevo. Ya no decide si continuar con resultados calculados antes del callback.

Las pulsaciones repetidas mientras ya está pulsado y los arrastres con el mismo
objetivo no avanzan artificialmente la física ni solicitan callbacks adicionales.
Se conservan el retorno, la inercia y la ausencia de trabajo tras estabilizarse.

## Selección de mensajes

`SelectedBubbleMotion.enter` reconoce cuando la limpieza del propietario anterior
inició otra selección. Esa selección más reciente conserva el callback y sus
resortes; una entrada anterior no puede sobrescribirla al volver de la limpieza.

Se distingue de una limpieza que solo hace `reset`: esta libera el propietario
anterior y permite que la entrada solicitada continúe. No cambia las curvas,
el desenfoque, las dimensiones del menú, sus tiempos límite ni la liberación
del scroll al cerrar.

## Mini reproductor

`PlayerMiniView` cancela el animador retirando primero su propiedad. Los callbacks
obsoletos comprueban su identidad antes de cambiar progreso o notificar offsets.
Al terminar una transición se libera la referencia al animador.

Una actualización explícita sin animación ya no se descarta por existir un
animador activo hacia el mismo destino: aplica inmediatamente el estado pedido.
La inversión animada conserva el progreso visible. No cambian los 180 ms,
los interpoladores, el diseño ni la lógica de reproducción.

## Comprobaciones

Los probes JVM ejecutan los controladores/métodos de producción con un reloj y
colas contadas: cancelación en el primer redraw y durante el frame, sustitución
reentrante, cambio de objetivo cuando el resorte se estabiliza, ausencia de
callbacks duplicados, limpieza anidada y callbacks tardíos del reproductor.

La suite también incluye las comprobaciones anteriores de física a distintas
frecuencias y de apertura/cierre, blur, reacciones y otras funciones del cliente.
Estos son tests de estado, comportamiento y cantidad de trabajo; no mediciones
de FPS o tiempo de fotograma en dispositivo.

No se compila una APK ni se inicia GitHub Actions. La revisión visual de gestos,
scroll con reproductor visible, cambios rápidos de presentación y reentrada
tras salir de la pantalla queda pendiente de una prueba física.

Resultado final: **437 pruebas pasadas, 39 omitidas**. Las 12 pruebas dirigidas
de interacción y propiedad de animaciones también pasan. La sintaxis Java de los
tres archivos modificados y `git diff --check` se verificaron sin errores.
