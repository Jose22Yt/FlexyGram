# Fluidez: diagnóstico y primera intervención

Base: `41ec915549ddeea4bbe53eb6ade6d20114b1dc4b`.
Rama: `share/flexygram-settings-motion-menus`. Trabajo local, sin APK.

## Diagnóstico: hechos y costes por medir

Se inspeccionaron callbacks de transición de DialogsActivity/ChatActivity, medición de la lista principal, entrada multilínea, cabecera, menús de mensajes, efectos de borrado, blur y filas de ajustes. No equivale a haber ejecutado todas las pantallas.

1. **Trabajo evitable demostrado:** `DialogsActivity.checkUi_filterTabsVisible()` solicitaba layout de la lista cada vez que cambiaba el alpha de pestañas. La medición de esa lista calcula su padding con `getFilterTabsVisibilityFactor(false)`: excluye explícitamente la búsqueda. Por ello la búsqueda podía repetir mediciones de filas sin cambiar la reserva de espacio. La opacidad no debe dirigir ese layout. El coste en milisegundos requiere trazas.
2. **Creación repetida demostrada en ajustes:** `Settings2Cell` reconstruía icono y cuatro drawables en binds/agrupación. La mejora local conserva instancias por fila y actualiza solo estado cambiado. Detalles y pruebas en `SETTINGS_ROW_REUSE.md`.
3. **Coste potencial pendiente de medir:** la apertura de chat actualiza partes visibles y prepara blur; al terminar llegan actualizaciones, teclado y ayudas. Se conserva su orden: mover callbacks sin separar dependencias puede romper mensajes visibles o sincronización. No se identificó aquí una operación concreta de red/disco síncrona que justifique trasladar este bloque completo a otro hilo. Las vistas y su medición son trabajo del hilo principal.
4. **Coste potencial pendiente de medir:** `DeleteMotionOverlay.capture()` captura la vista en bitmap antes de borrar; hasta cuatro overlays pueden coexistir, cada captura limitada a 900.000 píxeles. Dibujar una vista en software y subir texturas puede costar CPU/GPU. No se mueve View.draw a un worker: no es seguro. Se conserva el efecto y se propone medir capturas antes de introducir otro mecanismo.
5. **Animación no implica aceleración del render:** `FastMotionTiming` reduce duraciones con la preferencia actual. No reduce por sí mismo el coste de layout, dibujo o trabajo de cada frame. La comparación debe repetir ambos estados de la preferencia.

## Plan priorizado

| Etapa | Archivo y métodos | Cambio / motivo | Verificación |
| --- | --- | --- | --- |
| Quick win, aplicado | DialogsActivity: checkUi_filterTabsVisible, createView | Cachear el factor de geometría sin búsqueda; pedir layout solo cuando cambie; invalidar caché al recrear vista. Alpha/scale siguen el factor visual. | Prueba ejecuta métodos reales: búsqueda completa, reversa, filtro, panel lateral, lista temporalmente ausente, recreación. Perfetto debe mostrar menos traversal/measure durante búsqueda sin alterar posición de filas. |
| Quick win, aplicado previamente en este árbol | Settings2Cell: updateCard, bindIcon, bind, dispatchDraw/updateForeground | Conservar fondos/iconos por fila; actualizar geometría y tema; corregir textos de filas visibles al cambiar tema. | Contadores de creación sobre 10.000 repeticiones, cambio de Resources/Configuration/tema/densidad. Verificar ripple y esquinas con interacción real. |
| Medium, pendiente | Adaptadores de mensajes y diálogos: notificaciones de datos | Medir qué eventos fuerzan binds completos; introducir payloads o DiffUtil sobre snapshots estables solo donde identidad y contenido estén definidos. Nunca pasar listas mutables activas a un diff de fondo. | Mensajes entrantes, edición, eliminación, selección, carpetas y conservación de scroll; comparar bind/measure por evento. |
| Medium, pendiente | DeleteMotionOverlay: capture/runNativeDelete; SignatureWallpaperBlur: publicación/reveal | Medir captura, subida de textura y callbacks de efectos simultáneos. Evaluar presupuesto compartido y agrupación de animación según resultado. | Misma escena y cantidad de overlays, CPU/GPU, memoria y detach/cancelación, sin retrasar el borrado real. |
| Deep, pendiente | Apertura/transiciones y scroll completo | FrameTimeline/Perfetto antes de cambiar planificación, layers o medidas. Separar main, RenderThread, GPU, GC y bloqueos. | Ensayos repetidos a 60/120 Hz, frío/caliente, IME y temperatura equivalente. |

No se añade una capa hardware indiscriminada a listas con contenido dinámico: puede aumentar texturas, memoria y overdraw. Usarla temporalmente requiere un subárbol estable, evidencia de ahorro y liberación/restauración en final, cancelación y detach. Las animaciones de muelle y borrado ya usan postOnAnimation/Choreographer; no se añade otro reloj. No se sustituye toda animación por un solo animator sin conocer sus propietarios y cancelación.

## Cambio de lista, exactamente

`lastFilterTabsLayoutFactor` empieza en NaN. Cada actualización visual conserva alpha, scale y visibilidad existentes y consulta aparte el factor usado por la medición. Solo solicita layout si ese factor cambia y existe la página. Si falta la página, no consume el cambio. Se reinicia al recrear las vistas. Las actualizaciones de posición del contexto siguen ejecutándose.

La primera llamada puede solicitar una medición adicional de inicialización. Los cambios geométricos reales conservan requestLayout: eliminarlo durante esos cambios exigiría rediseñar el contrato del padding/scroll, fuera de esta intervención de bajo riesgo. No se promete eliminar todo layout de toda animación.

## Verificación local final

- Suite: **275 aprobadas, 33 omitidas y 9 subtests aprobados**. Comando: `python -m pytest tests/ tools/connected_alpha/test_flexystudio.py tools/connected_alpha/test_composer_reference.py -q`, con JDK 21.
- Métodos reales de pestañas ejecutados con dobles explícitos: sin nuevas solicitudes tras inicializar durante 120 pasos de entrada y 120 de salida de búsqueda. Los cambios reales de reserva de espacio siguen solicitando medición.
- Sintaxis Java de DialogsActivity y Settings2Cell comprobada con el parser de javac 21; Settings2Cell compilada contra android.jar API 37 con servicios del proyecto sustituidos por dobles. No equivale a compilar todo el módulo.
- `git diff --check` limpio; parche completo exportado y comprobado contra el árbol mediante `git apply --reverse --check` (solo validación).

## Aceptación en dispositivo

ADB comprobado: **0 dispositivos conectados**. No hay medidas físicas ni compilación integrada en esta intervención.

- Ejecutar la misma carga y configuración antes/después, con varias repeticiones; registrar refresco real y estado térmico.
- Abrir/cerrar búsqueda con carpetas visibles y ocultas; interrumpir y revertir a mitad. Revisar animación, primera fila, offsets y posición de scroll.
- Abrir chat y volver repetidamente; scroll con texto, fotos, audio y mensajes largos; abrir/cerrar teclado y escribir texto multilínea.
- Cambiar carpeta y desplegar panel lateral durante búsqueda; probar orientación, RTL, fuente grande y recreación.
- Ajustes: scroll, búsqueda, claro/oscuro, pulsación sostenida sobre tarjetas/ripple, distintas densidades.
- Capturar FrameTimeline y main/RenderThread, sched y GC con Perfetto. Comparar p50/p95/p99 de frames, porcentaje de frames con deadline perdido, traversal/measure, CPU y pausas GC; registrar latencia input→presentación.
- Presupuesto orientativo del intervalo: 16,67 ms a 60 Hz y 8,33 ms a 120 Hz. No es todo tiempo disponible para main; evaluar los deadlines reales de la traza.
- Vigilar memoria/PSS y coste GPU además de FPS: desplazar trabajo a GPU puede empeorar consumo y estabilidad térmica.

Las pruebas host usan el código real con dobles declarados y verifican solicitudes, recursos y comportamiento; no simulan HWUI, IME ni composición real. La aceptación de fluidez queda pendiente de esas mediciones.
