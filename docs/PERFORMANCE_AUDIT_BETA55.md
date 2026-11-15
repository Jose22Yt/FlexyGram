# Auditoría de rendimiento de flexyGram, posterior a beta 55

Base revisada: `217044b997a999a5a0ce1041939413f0bf81950a` (beta 55, código 1344).
Alcance: arranque, carga de la lista de chats y captura del fondo para blur/liquid glass.
Las correcciones de esta revisión son posteriores a la APK beta 55; esa APK no las contiene.

## Resultado y prioridades

| Prioridad | Defecto confirmado | Corrección implementada | Alcance real |
| --- | --- | --- | --- |
| P1 | `MessagesController.loadDialogs` activa `loadingDialogs` pero no lo libera cuando falla la petición de red. Las siguientes llamadas salen sin solicitar datos. | Liberar el estado en UI, notificar la lista y limitar nuevos intentos de red durante 3 segundos por carpeta. Invalidar callbacks antiguos al limpiar la cuenta. | Recuperación de errores transitorios. No acelera una respuesta de Telegram que todavía está pendiente. |
| P1 | Con plugins habilitados, `PluginsController.init` llama a `watchdog.recoverAfterCrash` durante `postInitApplication`. Ese método consulta, abre, lee y borra un archivo en el hilo de arranque. | Recuperación y arranque del watchdog en la cola serial del motor, antes de Python y de cargar plugins. Contexto y preferencias siguen disponibles de inmediato. | Elimina esa E/S de `Activity.onCreate`. Si el motor está deshabilitado, esta ruta ya no se ejecutaba. |
| P2 | El capturador de `DialogsActivity` era una lambda que heredaba `captureCalculateHash = unsupported`. La caché del supresor nunca podía reutilizar el fondo aunque no cambiase. | Implementar el hash con la misma geometría y opacidad de la captura. Reutilizar contenido limpio; mantener captura cuando cambia. Durante scroll, contenido sucio, búsqueda no compatible y overlays de transición, usar el camino conservador. | Evita registros redundantes cuando el fondo permanece igual. No reduce artificialmente la frecuencia de actualización durante el scroll. |

No se ha demostrado que uno de estos defectos explique por sí solo todos los tirones o todo el tiempo de arranque de un dispositivo real.

## Archivos y decisiones

- `TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java`: estado de carga y espera mínima de reintentos por carpeta. La espera no retrasa lecturas locales y no crea temporizadores ni un bucle automático de solicitudes. Un evento posterior de scroll/reanudación puede volver a solicitar datos. No se alteran mensajes ni posiciones de paginación.
- `TMessagesProj/src/main/java/app/exteraless/plugins/PluginsController.java`: ejecutar recuperación en `PythonPluginsEngine.runOnEngine`. Comprobar de nuevo que el motor siga habilitado antes de iniciar y antes de cargar plugins.
- `TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java`: implementar el contrato de caché del capturador. Si la lista está desplazándose o ya se sabe que cambió, evitar además recorrer todos sus hijos para calcular un hash inutilizable.
- `TMessagesProj/src/main/java/org/telegram/ui/Components/blur3/utils/Blur3Utils.java`: calcular el hash en coordenadas relativas al mismo padre y con la misma opacidad que el dibujo. Reutilizar un `RectF` propiedad del capturador; no asignar un rectángulo en cada llamada.

No se deshabilitaron los efectos visuales ni se movieron controladores nativos de Telegram a hilos ajenos a su contrato.

## Evidencia reproducida

`tests/test_performance_root_causes.py` compila y ejecuta los bloques Java de producción con colas y objetos Android controlados:

1. El hilo llamador no realiza la recuperación del watchdog ni inicia Python. La cola ejecuta recuperación antes del inicio. Inicializaciones repetidas no duplican trabajo; deshabilitar el motor mientras espera impide iniciarlo.
2. Un error de red libera el estado de carga en UI. 10.000 intentos dentro de la espera no crean peticiones adicionales. Otra carpeta y la caché local siguen disponibles. Un callback anterior a limpiar la cuenta no libera una petición de la nueva sesión. La respuesta vacía correcta conserva su callback.
3. Dos regiones, fondo sin cambios y 10.000 llamadas: el contrato anterior produce 20.000 registros; el nuevo produce 2. Cambios de contenido, posición, suciedad, búsqueda y transiciones siguen provocando capturas. Durante 10.000 llamadas con scroll activo no se recorre el contenido para calcular su hash. Una display list descartada se vuelve a generar.

Estas cifras cuentan trabajo del algoritmo con objetos de prueba. No son fotogramas medidos, tiempo de GPU, latencia de apertura ni una promesa de FPS.

Verificación ejecutada:

```bash
PATH=/workspace/work/bin:$PATH FLEXY_AI_JAR_DIR=/workspace/work/ai-deps \
  /workspace/work/review-venv/bin/python -m pytest tests/ -q -ra
```

Resultado: **497 passed, 43 skipped**. Las omisiones incluyen comprobaciones que necesitan SDK Android o corpus externos. También se ejecutó `git diff --check`.

No se ha compilado una APK nueva con esta revisión. La compilación completa Android y la medición en dispositivo siguen pendientes; la compilación JVM de los bloques no sustituye esas comprobaciones.

## Qué falta para afirmar que la app completa es fluida

Hace falta una captura antes/después con el mismo dispositivo, compilación optimizada, cuenta y escenario. No es correcto atribuir todos los tirones al blur por su apariencia ni afirmar que cambiar un parámetro soluciona el problema global.

La ruta de arranque todavía contiene inicialización nativa, idioma/configuración, controladores y recursos de tema en el hilo principal. Parte de ese trabajo es necesario y tiene dependencias de UI. No se ha medido cuál domina su duración: no debe trasladarse todo a un executor sin conservar esos contratos.

El repositorio ya incluye un generador de configuración y consultas Perfetto:

```bash
python tools/connected_alpha/performance/perfetto.py \
  --package com.flexygram.messenger --seconds 30 --out-dir work/performance-trace
```

Esto genera el plan; no captura por sí mismo una traza. Validar por separado:

- Arranque frío y caliente: tiempo a primera pantalla, primera lista utilizable y finalización de carga. No confundir encolar SQLite con mostrar filas.
- Lista de chats: mismo recorrido y misma cantidad de datos; comparar fotogramas con jank y percentiles, separando UI, RenderThread y GPU.
- Conversación: apertura con historial frío/caliente y scroll con texto, imágenes, stickers y audio.
- Blur y liquid glass: comparar el mismo recorrido con ambos efectos activos e inactivos; revisar su coste en la traza antes de reducir calidad.

Criterio de cierre: compilación Android correcta, sin regresiones funcionales y mejora observada de latencia/jank en estos escenarios. **Todavía no se aprueba la afirmación de que el rendimiento global esté resuelto.**
