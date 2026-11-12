# Apertura de chats y trabajo de traducción al pausar

Esta revisión parte de `41c1f09f3`. Examina las cargas de apertura, las tareas de
scroll y traducción, la reanudación y los controladores de animación existentes.
Los cambios se limitan a fallos reproducidos en la apertura y el ciclo de vida de
la traducción. No añade efectos ni cambia el diseño, las preferencias o MTProto.

## Solicitudes de apertura

`ChatPeerPreloader` identifica cada solicitud por un objeto propio, además de la
cuenta, el propietario y el peer. Cerrar sesión invalida ese objeto y libera sus
callbacks. La cola de almacenamiento ve la cancelación mediante un campo
`volatile`, sin consultar el mapa de UI desde el hilo de almacenamiento.

Esto corrige dos casos de una sesión que se cierra y vuelve a iniciarse con la
misma cuenta:

- Un resultado antiguo ya leído no puede insertar su snapshot ni completar o
  retirar una solicitud nueva que tenga la misma clave.
- Una lectura todavía en cola no accede al disco si su solicitud fue cancelada,
  aunque el mismo propietario ya haya vuelto a iniciar sesión.

También se comprueba el resultado booleano real de `DispatchQueue.postRunnable`.
Si la cola rechaza el trabajo, se completa con fallo y se libera el observador,
en lugar de retener indefinidamente la solicitud y coalescer nuevos intentos con
una carga que nunca se ejecutará. El siguiente intento puede crear otra carga.
Se conservan la deduplicación de lecturas y la prioridad de los datos recibidos
en vivo sobre los snapshots del almacenamiento.

## Traducción

La programación y el inicio del callback comprueban si el chat está pausado o
finalizado. Una pantalla oculta no debe recorrer sus mensajes por un evento
nuevo o por un callback antiguo. `onPause` cancela la tarea y deja la revisión
pendiente; `onResume` solicita esa revisión tras retirar el estado de pausa.

La revisión al volver usa la ruta normal: se aplaza mientras hay scroll y conserva
el debounce existente. Los cambios explícitos de idioma en una pantalla activa
siguen usando la ruta inmediata. No se introduce polling ni otro bucle de frames.

## Validación

Los nuevos probes JVM ejecutan los métodos de producción con colas contadas.
Los cuatro casos nuevos fallaron antes de las correcciones y pasan después:
resultado antiguo tras reiniciar sesión, lectura cancelada antes de ejecutarse,
cola que rechaza trabajo y traducción al pausar/reanudar. El caso de traducción
incluye 10.000 solicitudes con la pantalla pausada y otras 10.000 con el chat
finalizado, sin tareas programadas ni scans.

Las pruebas anteriores siguen cubriendo coalescencia, cuentas y peers distintos,
cambio de controlador, snapshots frente a datos en vivo, errores de callbacks,
scroll, paginación y solicitudes explícitas de traducción.

No se compila una APK ni se ejecuta GitHub Actions. Estas verificaciones prueban
estado y cantidad de trabajo, no FPS ni latencia en un teléfono. La prueba física
pendiente debe incluir abrir chats no cacheados, salir y regresar a conversaciones
traducidas, cambiar idioma durante scroll y reiniciar sesión con cargas pendientes.

Resultado final de la suite completa: **462 pruebas pasadas y 39 omitidas**.
La sintaxis de los dos archivos Java modificados se verificó con tree-sitter;
`git diff --check` no detectó errores.
