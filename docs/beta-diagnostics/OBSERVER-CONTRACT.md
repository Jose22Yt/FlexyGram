# Contrato nuevo de observación, sin activar instrumentación en la app

No modifica los contratos históricos del laboratorio. Define únicamente la
entrada del nuevo analizador. Work2 deberá implementar/revisar el productor en
una variante de prueba o usar observación externa equivalente antes de medir.

Cada línea JSON tiene exactamente:

```json
{"id":"r001","op":"chat_open","phase":"request","timestamp_ns":1000000000,"clock":"android_monotonic_ns"}
```

Ese timestamp es un ejemplo sintético. No incluir dialog_id, user_id, textos,
URLs, cuentas, tokens ni argumentos de navegación. ID opaco único por ejecución,
1..64 caracteres ASCII alfanuméricos/guion/underscore; reloj entero nanosegundos,
no decreciente en el flujo. Serializar eventos de varios hilos preservando el
orden observado; informar pérdidas, sin bloquear el hilo UI para escribir.
No instalar un hook global de toques ni cambiar las rutas de navegación.

Operaciones admitidas: startup, chat_open, chat_close, rapid_tap,
transition_interrupt, theme_light y theme_dark. Fases:

| Fase | Significado y punto de observación |
|---|---|
| request | Harness u observador inicia la acción, antes de solicitar navegación; no equivale a contacto físico con la pantalla |
| accepted | La ruta revisada admite la operación; para presentFragment, distinguir retorno true de entrada al método |
| presented | Endpoint acordado de escena visible/frame completo, con criterio idéntico en los tres clientes |
| cancelled | Cancelación confirmada del ID de transición anterior; no presentación exitosa |
| timeout | El observador no alcanzó el endpoint en el límite del escenario; no es automáticamente ANR |

Un request puede terminar cancelled/timeout sin accepted. Presented requiere
accepted previo. Un ID admite una sola aceptación y una sola terminación.
No reasignar un evento a otro ID porque el original desapareció. Un request
sin terminación queda incomplete; no inventar su duración final.

Animator puede entregar callbacks de cancelación y finalización: el observador
ha de emitir sólo una terminación, y evitar presented cuando la animación fue
cancelada. El analizador rechaza duplicados/orphans en vez de suavizarlos.
Registrar también el nuevo request que sustituye al anterior en pruebas rápidas.
La cancelación se mide request→cancelled, separada del tiempo de escena nueva.

Puntos para futura integración, no hooks implementados en esta rama:

- DialogsActivity: justo antes de solicitar ChatActivity; ID nuevo en cada acción.
- ActionBarLayout.presentFragment/closeLastFragment: aceptación real, no sólo tap.
- ChatActivity.onTransitionAnimationEnd: **no usarlo sin contrastar el frame
  visible**; puede finalizar la animación antes/después del contenido requerido.
- Tema: separar petición de cambio, reconstrucción de vista y primer frame del
  tema solicitado. No deducirlo de un cambio de preferencia aislado.
- Startup: endpoint de primera escena utilizable definido por el protocolo.
  Carga JNI/Python aparte; un proceso vivo no demuestra primer frame correcto.

En metadata.conditions.event_endpoint identificar el endpoint exacto:
`frame_callback_v1` o `video_visible_v1`, por ejemplo. No mezclar ambos. Un
callback de render no prueba presentación física; para input-to-photon se
necesita vídeo sincronizado/dispositivo de medición y otro protocolo revisado.
No etiquetar una marca externa como reloj Android sin calibración verificada.

Relojes: System.nanoTime/CLOCK_MONOTONIC para eventos internos. No usar
System.currentTimeMillis para duraciones; no sustituirlo por elapsedRealtimeNanos
sin transformar relojes. Epoch de Logcat y ventana ns de gfxinfo son independientes.

El productor debe registrar `observer_lost_events=0` **sólo si lo verificó**.
Si se satura una cola o se pierde un registro, incrementar el contador. Si no
puede verificarse, usar null; el comparador bloquea null/unknown y valores>0.
No fijar ese campo a0 para hacer pasar una comparación. Ejecutar una prueba de
sobrecarga del observador antes de confiar en sus resultados.
