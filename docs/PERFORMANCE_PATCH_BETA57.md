# Parche beta 57 (1346): reacciones, memoria y compatibilidad MIUI

Destino solicitado: `codex/flexygram-beta-glass`. Integra beta 55, el parche intermedio y beta 56, cuya compilación Android fue verificada en Actions `43729118872`.

## Correcciones reproducidas en código

- **Blur del popup de duración de reacción:** se comparaba el ancho/alto del bitmap reducido a 1/12 con las dimensiones completas del decor, causando recapturas en sucesivos layouts. Ahora se conservan dimensiones de origen y solo se prepara un trabajo a la vez. La captura de vistas permanece en UI y el kernel de blur corre en un worker de baja prioridad con una sola plaza de espera. Un resultado perteneciente a una ventana cerrada o a otro tamaño no se publica. Los bitmaps privados descartados se reciclan; los ya publicados se retiran por GC para respetar a HWUI.
- **Capas temporales de reacciones:** se registran las vistas realmente promovidas y su tipo anterior. La restauración recorre ese registro, incluso si cambia `cascadeAnimation`, y respeta cambios posteriores de otro propietario. Retirar/desconectar una ventana cancela sus animadores y libera sus referencias.
- **Propiedad del estado global de emoji hardware:** las operaciones nativas llevan un propietario débil; cerrar una ventana anterior no reanuda la cola de imágenes ni desactiva el modo hardware de una ventana nueva. Se conservan los métodos públicos anteriores. La tarea de inicio se retira antes de ejecutarla, conservando una tarea nueva creada reentrantemente.
- **Conversaciones destruidas:** después de `onFragmentDestroy` y de separarse la vista de la ventana, se detienen scroll y animaciones, se retira el adaptador y se vacían caché/pool privados. Si RecyclerView está calculando layout, la operación espera al siguiente turno de UI. No se vacían chats activos/pausados ni se modifica el historial o la pila de navegación.
- **Partículas:** la generación de bitmaps recuerda el color con el que terminó, evitando regenerarlos por la primera comprobación de color. Traslación y rotación usan tiempo transcurrido monotónico, con límite de salto, en vez de un intervalo de refresco congelado al construir el drawable. Un segundo dibujo con la misma marca de tiempo no vuelve a avanzar la simulación.
- **MIUI:** `NotificationBadge.XiaomiHomeBadger` omite `Class.forName("android.app.MiuiNotification")` desde API 34. Conserva el broadcast de compatibilidad cuando el launcher lo admite, y protege su envío frente a `SecurityException`.

## Qué no demuestra el diagnóstico aportado

El aviso de BLAST sobre el máximo de buffers indica contrapresión y no demuestra por sí solo que glass retenga cuatro buffers. La aplicación no debe liberar manualmente buffers que pertenecen a HWUI/SurfaceFlinger. Este parche corrige rutas concretas de retención de capas y vistas; no presupone que sean el único origen del aviso.

El 93,14 % y los percentiles de `dumpsys gfxinfo` son cifras aportadas por el usuario; no se recibió aquí el volcado bruto para recalcularlas. Tampoco son intercambiables con el 8,74 % de `App Deadline Missed` medido en una superficie de la traza anterior. No se afirma un porcentaje de mejora, FPS garantizados ni eliminación total de jank.

## Verificación

`tests/test_reactions_update57.py` compila y ejecuta los métodos/clases de producción afectados con dobles Android y colas controladas. Cubre reentrada, dos ventanas, cambio de modo de animación, restauración de capas, retirada fuera de layout, API 33 frente a 34–37, colas de blur saturadas, fallos, cambios de tamaño y cierre de la ventana. La batería completa y el workflow de la rama verifican la integración. Consultar el resultado de la ejecución asociada al commit antes de afirmar que su APK esté lista.

La validación de rendimiento requiere comparar beta 55 con la nueva versión en el mismo recorrido/dispositivo. El workflow genera una APK con firma de prueba; una actualización de distribución necesita conservar la clave de firma de la instalación existente.
