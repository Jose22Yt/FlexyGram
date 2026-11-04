# Revisión de rendimiento sobre la beta actual

Base: `b0fbc63a810f07d8d99427982805926fa0f93d2c`, punta comprobada de `codex/flexygram-beta-glass`. Se conservan las tarjetas agrupadas, iconos compactos, modos independientes de vidrio, contraste de las horas y velocidad visual ×0,01. No se cambia la identidad, firma, distribución ni versión. No se compila APK ni se publica esta revisión.

## Problemas corregidos

1. **Objetos temporales en las secciones animadas.** `RecyclerListView.drawSectionsBackgrounds` creaba un `Section` por fila en cada recorrido; `SectionsDrawer.calculateGroup` generaba otro array por grupo y ordenaba incluso entradas ya ordenadas. Ahora las filas reutilizan pequeños objetos numéricos por lista, los grupos reutilizan buffers por profundidad de dibujado y la ordenación se ejecuta solo si hace falta. Los callbacks genéricos heredados todavía pueden producir boxing: no se afirma que todo el renderizador Android sea allocation-free.
2. **Interferencia entre dibujos anidados.** `SectionsDrawer` compartía un array de grupos estático. Un callback que dibujara otra lista podía sustituir los grupos pendientes del dibujo exterior. Los estados por hilo/profundidad quedan aislados; `finally` libera el estado incluso si un callback falla. Las listas de filas también se vacían en `finally`.
3. **Vida de imágenes publicadas.** `SignatureWallpaperPreview` reciclaba inmediatamente el bitmap publicado al sustituirlo/cerrar la vista. Un drawable obtenido previamente o un dibujo retenido por HWUI puede seguir refiriéndose a ese bitmap. Ahora se suelta la referencia de la vista y se deja liberar el recurso cuando todos sus consumidores lo abandonen, igual que la política existente de `SignatureWallpaperBlur`. Se siguen reciclando resultados cancelados antes de publicar. Las notificaciones tardías sobre vistas separadas ya no preparan otra vista previa.

Los pools conservan únicamente geometría numérica, con un máximo de 128 objetos/buffers por lista o profundidad de dibujado. Las entradas mayores se dibujan correctamente con temporales y el contenedor de grupos extraordinariamente grande se libera después. No se guardan referencias a vistas, cuentas, Canvas o conversaciones. Esta pequeña retención reduce creación repetida de objetos; no demuestra por sí sola una reducción de PSS total.

## Evidencia y límites

- Suite general: **254 pruebas aprobadas y 33 omitidas** por condiciones opcionales del entorno.
- Regresiones nuevas ejecutan el código real extraído de las secciones: geometría/alpha con renderizado anidado, recuperación tras excepción y reutilización de objetos sin crecimiento mientras no aumenten las filas.
- La regresión de previews ejecuta el helper de producción completo con dobles explícitos de Android: un frame publicado sigue utilizable tras sustituir/cerrar; un resultado aún no publicado se descarta; cerrar cancela el trabajo pendiente y no recicla el fondo original.
- Se actualizó la prueba Canvas Android existente para dibujar una referencia publicada después del cierre. **Esa prueba Android no se ejecutó en esta revisión**: el entorno no tiene Maven/Robolectric preparado. La prueba JVM de propiedad no equivale a HWUI/RenderThread real.
- `tools/performance_current/render_allocation_probe.py` compara 2.000 geometrías/alphas contra la base exacta y mide asignaciones por hilo con HotSpot. Requiere el commit base disponible localmente. Resultados en `render-allocation.json`.
- ADB está disponible, pero la consulta detectó **0 dispositivos utilizables**. No se recogieron trazas ni métricas de un teléfono.
- Son medidas JVM de un recorrido sintético, con 10.000 iteraciones de calentamiento y 10.000 medidas por caso, no de la aplicación Android completa. El JIT, el boxing y el tamaño de las filas afectan los resultados. No son FPS, PSS, arranque, batería ni temperatura del teléfono.

Reproducción, con Java 21 y pytest:

```sh
python -m pytest tests/ -q
python tools/performance_current/render_allocation_probe.py
```

## Siguientes prioridades, antes de cambiar de lenguaje

| Prioridad | Trabajo | Motivo / condición |
| --- | --- | --- |
| Alta | Perfetto FrameTimeline, CPU de main/RenderThread y asignaciones/GC durante abrir chat, volver y scroll | Separar carga, CPU, GPU y pausas del recolector. Usar también el laboratorio existente `tools/connected_alpha/performance/`, misma carga, frecuencia real, estado de caché y temperatura. |
| Alta | Comparar una compilación de producción optimizada y perfiles ART de arranque | La ruta actual `ui-beta-debug.yml` usa `assembleDebug` con C++ Release y manifest no depurable, pero no activa por ello R8/shrinkResources. Evaluar R8 respetando JNI, reflexión y plugins, y generar Baseline Profiles en un dispositivo. No se han generado perfiles ficticios. |
| Media | Reutilizar iconos y fondos de filas de ajustes al hacer bind/cambiar tema | `Settings2Cell.bind` vuelve a crear el icono; `updateCard` reconstruye fill, máscara, ripple e inset. Es trabajo comprobable en el código; su impacto real necesita trazas y pruebas de ripple/tema antes de cambiarlo. |
| Media | Presupuesto y cancelación de copias de wallpaper/escáneres | Previews y blur comparten `Utilities.globalQueue` con otras tareas. Medir saturación y coalescer trabajo redundante o usar una cola existente apropiada; no añadir pools sin límite. El blur ya tiene caché de dos entradas y captura compartida. |
| Media | Ensayos con presión de memoria y temperatura | Respetar límites de Android y medir mientras se calienta; forzar frecuencias o acelerar duraciones no vence el throttling. Cualquier adaptación visual requiere aceptación y conservar las elecciones del usuario. |
| Posterior | Rust en un módulo CPU aislado, solo si el perfil lo justifica | Comparar con Java/Kotlin/ART y el C++ ya existente, incluyendo coste JNI, copias y conversión de texto. No reescribir la interfaz ni crear un segundo motor de blur por moda. |

El proyecto ya contiene componentes nativos C/C++, por ejemplo FFmpeg, códecs y voz en `TMessagesProj/jni/CMakeLists.txt`. Rust puede aportar seguridad de memoria y control de costes en módulos nuevos, pero no elimina por sí solo bloqueos de UI, layouts repetidos, sobredibujado o límites de GPU. El rumor de una reescritura completa de Discord no se ha corroborado en esta revisión; los dos artículos oficiales históricos consultados respondieron HTTP 403. No se atribuye un anuncio nuevo al CTO sin una fuente verificable.

La escala ×0,01 se conserva. Cambia duración de presentación; no demuestra que el cálculo de cada fotograma sea cien veces más rápido. La aceptación final debe medir el cliente completo en un teléfono antes de prometer fluidez, ahorro de memoria o rendimiento térmico.
