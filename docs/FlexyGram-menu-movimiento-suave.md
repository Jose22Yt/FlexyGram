# Pulsación y cierre del menú de mensajes

Cambios sobre la beta 13 y la restauración pendiente de iconos/materiales. No se cambia el diseño ni la física de la animación.

| Archivo y método | Trabajo evitado | Cambio | Verificación |
| --- | --- | --- | --- |
| `ChatActivity`, cierre del popup compacto (`dismiss`) | Dos actualizaciones de WindowManager antes de empezar el retorno | Agrupa touchable, focusable y touch-modal en una sola actualización; una segunda petición de cierre no vuelve a actualizar la ventana | Prueba del punto de integración exige una llamada a `update`; cierre normal e interrupción conservan su limpieza |
| `ChatActivity`, `showMenu` y callback de `selectedBubbleMotion.enter` | Reasignación de pivotes en cada fotograma | Fija el pivote después de medir y antes de mostrar. Los fotogramas solo actualizan alpha, escala, desplazamiento y progreso | Prueba verifica pivotes fuera del callback y ausencia de medidas/requestLayout en él |
| `SelectedBubbleMotion.doFrame`, `reset` y `finish` | Un callback anterior podía volver a programarse si su redraw cancelaba o reemplazaba la animación de forma síncrona | Token de generación evita que ese fotograma reprograme al propietario cancelado o duplique al nuevo | Choreographer simulado rechaza cualquier callback duplicado; cubre reset y reemplazo dentro de redraw |

Se mantienen el traspaso de velocidad desde la pulsación, el único reloj compartido por menú/reacciones/burbuja, la captura de fondo con propietario validado y la finalización inmediata para una nueva interacción.

`pytest -q tests/test_message_menu_smooth_motion.py tests/test_bubble_scroll_feedback.py tests/test_message_menu_designs.py tests/test_context_preview_fit.py`: 12 aprobadas. El test recorre apertura y cierre completo con relojes simulados de 30/60/90/120 Hz, finalización única y entrega al siguiente propietario. Estas frecuencias son entradas de la prueba; no constituyen FPS medidos.

Pendiente de aceptación en dispositivo: abrir/cerrar rápido, pulsar otra burbuja durante el retorno, mensajes largos, álbumes, teclado visible y volver atrás. Comparar FrameTimeline/jank y p95/p99 en las mismas condiciones. No se ha construido una APK.
