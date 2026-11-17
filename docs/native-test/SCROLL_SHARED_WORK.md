# Scroll: presupuesto de precarga y trabajo compartido

Base: `d50640dec`, Native Test beta.60, rama
`codex/flexygram-native-clean-bubbles`. No se restauran los efectos retirados del
perfil Native Test. Se mantienen las velocidades, fricción, umbrales táctiles,
fling, reciclaje y diseño nativos.

## Presupuesto del trabajador de RecyclerView

El `GapWorker` compartido por las listas de un hilo calculaba su intervalo al
crearse por primera vez. Un cambio posterior de la frecuencia de pantalla no
actualizaba ese valor: al pasar de 60 a 120 Hz podía seguir calculando la fecha
límite de precarga con 16,67 ms en lugar de 8,33 ms.

El observador de pantalla existente ahora informa ese cambio al trabajador del
mismo hilo. No crea trabajadores, callbacks por fotograma ni nuevos observadores.
La inicialización original de RecyclerView sigue calculando su presupuesto si
el trabajador todavía no existe. Los valores no finitos o fuera de 30–1000 Hz
no sustituyen el intervalo válido. La política afecta a las listas que comparten
ese trabajador: chats, mensajes, ajustes, contactos y otras listas RecyclerView.

Esto corrige el presupuesto de las tareas limitadas por plazo. Las tareas que
RecyclerView considera inmediatas conservan su política nativa; no se promete que
todo el trabajo de una pantalla quede dentro del presupuesto por este cambio.
No se fuerza un modo de pantalla ni se garantiza una frecuencia determinada.

## Tarjetas de ajustes y otras secciones segmentadas

Antes, calcular las dos esquinas de una fila consultaba cuatro veces la posición
y los dos tipos vecinos. Ahora se obtiene una sola vez la posición y se consultan
como máximo dos tipos. El mismo resultado se comparte entre la esquina superior
e inferior, tanto al dibujar como al recortar o preparar un fondo de menú.

No hay una caché persistente que pueda quedar desactualizada tras una inserción,
borrado o cambio de adaptador. Se preservan filas aisladas, píldoras, comienzos y
finales de sección, y se rechazan posiciones fuera del adaptador.

## Multimedia compartida

Durante arrastre y fling, su listener forzaba `checkSection(true)` y después el
listener común de RecyclerListView volvía a ejecutar `checkSection(false)`.
Se conserva la actualización común y se reserva la actualización forzada para
los movimientos que no son del usuario. Se mantienen la paginación, los avisos,
el scroll rápido y los demás callbacks nativos.

## Compatibilidad de las indicaciones de frecuencia

`setFrameContentVelocity` pertenece a API35. En API30–34, la indicación de scroll
intentaba invocarlo y capturaba el error de enlace en cada cambio de estado.
Ahora solo lo usa a partir de API35, igual que la categoría de frecuencia.
Se conserva la liberación de la indicación al parar y al desmontar la lista.

## Verificación y límites

Los probes JVM ejecutan los métodos de producción y los controladores reales con
dobles explícitos de las APIs Android. Comprueban:

- Cambio de presupuesto entre 30, 60, 90, 120 y 144 Hz, valores inválidos, ausencia
  de trabajador y separación entre hilos.
- Registro y retirada del observador, selección de pantalla y cambios de frecuencia.
- Equivalencia de esquinas para combinaciones de secciones de hasta siete filas,
  con una consulta de posición y hasta dos consultas de tipos por pareja de radios.
- 10.000 eventos de multimedia con una actualización de progreso de sección por
  evento durante arrastre/fling; ruta programática conservada.
- API23–34 sin invocaciones incompatibles y API35 con una indicación por cambio,
  restauración de estado y respeto por otra petición explícita de frecuencia.

La revisión incluye los puntos compartidos y las rutas de inicio, conversaciones,
ajustes y multimedia. No implica que se hayan medido todas las pantallas ni las
listas de cada plugin. No se aceleran los ScrollView del framework artificialmente.

No se ha medido FPS, CPU, memoria ni latencia táctil en un teléfono. Queda pendiente
comparar esta revisión con beta.60 bajo los mismos chats, tema, ahorro de energía
y frecuencia, incluyendo desplazamientos largos, multimedia y listas de ajustes.
No se ejecuta Gradle ni se inicia una compilación de APK en esta tarea.

Resultado: **536 pruebas aprobadas y 42 omitidas** en la suite completa. Las 31
comprobaciones dirigidas iniciales pasaron; tras la revisión final del vecino
inválido, los cinco probes nuevos volvieron a pasar. Sintaxis Java y
`git diff --check` correctos. No se ha verificado una nueva APK.
