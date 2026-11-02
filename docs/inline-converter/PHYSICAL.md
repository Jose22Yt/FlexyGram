# Aceptación física pendiente — Poco X8 Pro, Android17 / HyperOS4

Usar exclusivamente una cuenta y conversación de prueba preparadas por el propietario. No desinstalar ni borrar datos. Instalar por el procedimiento Beta privado autorizado de Work 1. No publicar pantallas/trazas privadas.

1. Registrar commit exacto de la APK, compilación, locale/región, zona del dispositivo, frecuencia efectiva, escala de fuente, tema, batería y estado térmico. Confirmar ajuste general desactivado inicialmente. En el mismo chat verificar vínculos, menciones, correo/teléfono, pulsación prolongada, respuesta, selección, copia, scroll y reacciones antes de activar.
2. Activar las conversiones en Chat. Con locale es-CO y sistema métrico, enviar texto de prueba: `La reunión será a las 3:00 PM EST. Cuesta $45 USD. Recorrido 70 miles, carga 180 lbs, temperatura 32 °F.` Tocar cada expresión. Esperado: unidades ≈112,65 km, ≈81,65 kg y 0 °C; divisa honestamente no disponible; hora con fecha/origen/destino explícitos. Copiar sólo resultados reales.
3. Elegir COP/EUR, Asia/Tokyo/Automático y métrico/imperial; salir y volver, cerrar/reabrir el proceso sin borrar datos. Verificar los siete valores guardados y que desactivar la función mantiene los gestos originales. No se exige un reinicio para convertir.
4. Editar texto/entidades y reciclar celdas rápidamente. Probar respuestas y captions simples de foto/video, emoji antes de la expresión, texto RTL mezclado, tamaños de fuente grandes, números es-CO/en-US/fr-FR, mensajes extensos. Código, spoilers y citas especiales deben conservar Telegram. `$45`, URLs, hashtags, números telefónicos, offsets UTC+2 no implementados y unidades ambiguas `m`/`in` no se convierten.
5. `01:30 America/New_York` con fecha 2026-11-01 exige elegir offset; `02:30 America/New_York`, 2026-03-08 informa hueco; `15:00 CST` e `15:00 IST` exigen escoger zona. Cambiar fecha y confirmar que la etiqueta deja de afirmar que proviene del envío. Verificar cambios de día.
6. Tocar y arrastrar, mantener pulsado, multitouch, Atrás, salir de chat, rotar, teclado abierto, mensajes fijados, menú de reacciones, música activa y temas claro/oscuro. La cápsula debe cerrarse sin reabrirse por callbacks obsoletos. Revisar límites con cabecera, pin, Composer, dock, teclado y barras de sistema; ajustar geometría si el dispositivo demuestra solapamiento. Tomar capturas reales de ambos temas con datos de prueba.

## Medición sin inventar latencia

Reutilizar `tools/connected_alpha/performance/`; no inferir toque→resultado de framestats. Comparar la misma Beta base con candidato desactivado, activado y popover en uso. Alternar orden, ≥20 repeticiones, caché fría/caliente declarada, misma música/contenido/compilación y distribución de frecuencia efectiva. No cambiar escalas del sistema mediante scripts.

Ejemplo de telemetría existente (interacción manual durante cada ventana):

```sh
python -m tools.connected_alpha.performance.capture \
 --package com.flexygram.messenger --scenario messages_scroll --build-mode beta \
 --iterations 20 --confirm-test-device --theme dark --cache-state warm \
 --conversation-fixture inline-synthetic-v1 --workload-id inline-disabled-scroll-v1 \
 --music-state stopped --refresh-profile observed-device \
 --installation-state update --test-session-state prepared \
 --network-profile offline --sync-state idle --charging unplugged \
 --output build/performance/inline-disabled-dark.json
```

Repetir con IDs que documenten activado y popover; usar el mismo escenario/carga al comparar. Este colector no toca mensajes ni opera la UI. Revisar `capture --help` si evoluciona su contrato. Usar `perfetto` del laboratorio para plan FrameTimeline/CPU/RenderThread; trazas privadas. La frecuencia debe salir de los intervalos reales, no asumir 60/120/144 Hz.

El candidato incluye secciones Trace estáticas `Flexy.inline.scan` (lectura de regex en cola de fondo, sólo cache miss) y `Flexy.inline.open` (construcción/presentación del popup en main). No contienen texto/identificadores. Su duración mide trabajo CPU, no el primer fotograma presentado. Correlacionar el segundo scope con input y FrameTimeline para estudiar latencia real.

Registrar mediana/p95, distribución de frames y jank clasificado, memoria/GC y asignaciones cuando exista instrumentación válida. Capturar aparte los instantes de input y presentación del resultado para latencia táctil real; un frame de 8 ms no demuestra una respuesta táctil de 8 ms. Verificar ausencia de tareas continuas con función desactivada y en reposo. No declarar equivalencia de fluidez hasta medir estas variantes.
