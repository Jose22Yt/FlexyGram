# Beta 40 / build 1329 — material nativo del composer

Estado: preparada sin compilar por indicación del propietario. El commit usa `[skip ci]` y no se solicita workflow manual.

Base: `45b4f2002403a36d2a44916ce3fcc52d818aceee` (beta 39). Esa base compiló y produjo la APK ARM64 en la ejecución 42916576756; la APK de dicha ejecución no incluye este arreglo posterior.

La cabecera y el composer compacto ya comparten la factoría blur3, el proveedor de color y la política de Liquid Glass. La diferencia comprobada era una segunda capa: `drawFlexyNativeGlassIslands` dibujaba cada superficie nativa y después un relleno adicional de alfa 40. El drawable/shader ya compone su color de primer plano. La segunda capa reducía de nuevo la contribución del fondo y de la refracción, con una apariencia más plana, especialmente en temas oscuros.

Se eliminan las cuatro llamadas y el método de tinte adicional. La cápsula de texto y las islas de adjuntar, micrófono y enviar utilizan una pasada de su drawable nativo, como la cabecera. Los colores de cada rol siguen siendo los del tema. No se cambian las curvas de refracción ni la intensidad global para simular transparencia.

Se conservan las geometrías, el motor blur3, la fuente compartida, los contornos nativos, las preferencias de efectos/ahorro, el tratamiento del teclado y los estados especiales de grabación, borradores y envío. Los fondos nativos de los hijos siguen evitando sobrepintar las islas cuando el padre ya dibujó el material. Las rutas clásicas/sin efectos y las capturas de software conservan sus alternativas existentes.

**Suite completa: 376 aprobadas, 39 omitidas, 0 fallos.** Las omisiones corresponden a dependencias/herramientas ausentes; los contratos de fuente de conversación y la sintaxis del fixture de composición pasan.

Validación: ejecución JVM de los métodos reales de composición y dibujo de islas con combinaciones de botones, materiales claro/oscuro/opaco, alfa 0/128/255, desplazamientos y 10 000 repeticiones sin reconstruir radios. El Canvas del probe carece de primitivas de relleno: una segunda capa añadida al compositor no compila en la prueba. Se verifican la política y la alternativa sólida, y se ejecutan regresiones de proveedor de color y estado de snapshots.

El fixture `composer_surface` se actualiza para que su doble de drawable represente el tinte nativo, incluso sin imagen de fondo. Sus comparaciones de píxeles distinguen ese doble del compositor real: no prueban una GPU física. Se actualizan también los contratos de fuente de `conversation_glass` a la arquitectura actual de islas retenidas y política centralizada.

El entorno local no tiene SDK API 37/Build Tools 36. La comparación visual de blur/refracción con la cabecera en el dispositivo de la captura sigue pendiente; retirar la segunda capa es una corrección verificable de composición, no una confirmación visual en ese teléfono ni una medición de FPS.
