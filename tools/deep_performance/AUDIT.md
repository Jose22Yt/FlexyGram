# FlexyGram — registro de ingeniería de rendimiento

## Fuente y decisión de integración

Revisión del 30 de octubre de 2026. Referencia inmutable: `cd2af16c8271e52738f0c4e726cf59862c637087` (PR136, Alpha1289). Rama independiente `perf/deep-purge-p0`, apilada sobre `feat/opexgram-context-spring`. **Una dependencia de código no equivale a aprobación, merge ni aceptación física.**

GitHub consultado directamente: PR119,120,130,132,135,136 siguen abiertos y draft. Main sigue en `db1bea24b`, un checkpoint documental antiguo; no contiene automáticamente los candidatos recientes. No se encontró una aprobación de integración más reciente que permita promoverlos. Se preserva la fuente de Work1 más reciente compilada como referencia de revisión, sin mover ninguna rama ajena.

Cadena verificada por historia git: PR119 restauración nativa → integración1282 que incorpora el primer toque de PR120 → sucesores Signature/Alpha1286 → PR131 identidad oficial → PR132 arranque/red/render/scroll → PR133–136 interfaz/contexto nativo. PR137 es una rama paralela de borrado aún sin integración real; no se incorpora. No se recupera el Flexy Motion Engine cancelado.

El propietario reportó lag al desplazarse entre mensajes con blur, glass, bordes y transparencias: esa ruta se convierte en la prioridad del lote. El reporte es evidencia de un síntoma, no una atribución demostrada a cada efecto.

## Alcance de la fase 1

Inventario de todo el árbol versionado, lectura dirigida de rutas de alto riesgo y revisión de las optimizaciones existentes. Esto **no significa revisión manual de cada línea**, perfil físico ni auditoría funcional completa. El inventario reproducible `inventory.json` distingue extensiones y namespaces. Los componentes de Android son vistas Java/Kotlin, Canvas, RecyclerView y JNI; CSS no es la tecnología de estas pantallas. El HTML de FlexyFiles usa WebView local restringido.

| Área/ruta real | Evidencia examinada y decisión | Prioridad / riesgo / estado |
| --- | --- | --- |
| Entrada, `ActionBarLayout.nativeInstantTouchDown`, `NativeInstantTouchTarget`, `NativeInstantTouchPolicy` | El hook conservador ya está integrado en esta cadena. Antes hacía hit testing/consulta de ventana aun cuando la política final rechazaba un modal, gesto u otro cierre. Añadir rechazo temprano con los mismos predicados, manteniendo el único cierre nativo y el evento original | P0 / bajo-medio / implementado; dispatch físico pendiente |
| Navegación `MainTabsActivity`, `GlassTabView` | La barra llama overrides a cada pestaña durante gestos, incluso cuando no participan. No invalidar si su selección visual efectiva no cambia; mantener el valor guardado para llamadas futuras | P0 / bajo / implementado |
| Colores de pestañas `GlassTabView.updateColors` | Se creaba un PorterDuffColorFilter aun con el mismo ARGB. Reutilizar solo el último filtro, por instancia; aplicar siempre a imágenes/texto para no romper reemplazos de avatar/icono | P0 / bajo / implementado |
| Composer/ajustes `ComposerSliderTrack`, `FlexySignatureSlider` | setProgress y onDraw pueden comunicar la misma fracción; el drawable invalidaba incluso sin cambio. No-op para la fracción/color iguales; no tocar táctil, accesibilidad ni geometría | P0 / bajo / implementado |
| Scroll `RecyclerListView`, `DialogCell`, `ChatMessageCell` | Conservar reciclado, fling, barras de voz cacheadas y voto ARR de PR132. No se demuestra un nuevo cuello de botella de bind/layout sin traza de chat real | P1 / medio-alto / perfil físico pendiente |
| Conversación `ChatActivity`, `MessageDrawable`, `BubbleFusion`, `SignatureBorderPath` | El drawable compartido retenía solo el contorno del último mensaje: alternar tamaños destruye la utilidad del cache de bordes parciales. Asociar el contorno al PathDrawParams nativo de cada celda y invalidar cuando se regenere la geometría, también en makePath. Paletas, clipping, blur, transparencia y pases de Fusion se conservan | P0 / medio / implementado y comparación gráfica aislada PASS |
| Contexto `BubbleTapMotion`, `SelectedBubbleMotion`, popup nativo | PR135/136 ya coordina resorte local, continuidad y cancelación. No reescribir curvas de Work1. Verificar temporalmente entrada/salida, pausa y nuevo DOWN con trazas | P1 / alto / validación Android aislada y física pendiente |
| Glass/blur `SignatureWallpaperBlur.Owner`, `ActionBar`, blur3 | Worker, LRU acotada, shader/matriz reutilizados, revelado finito y limpieza de owner ya existen. La capa de máscara de Fusion requiere medir GPU; no se elimina blur ni transparencia | P1 / medio-alto / GPU y memoria pendientes |
| Header `SignatureChatHeader`, `SignatureFusionSurface`, avatar mask | Paint/Rect/metrics ya reutilizados; máscara cachea shader en layout. Mantener controles nativos y diseño | P2 / medio / sin nuevo cambio |
| Inicio `ApplicationLoader`, `StartupAccounts`, `LaunchActivity` | Aprovechar elegibilidad lazy por cuenta, orden cero/seleccionada/resto y gate SQLite de PR132; bienvenida Signature ya es estática y no necesita EGL continuo | P1 / alto / checks PR132 repetidos; TTID/TTFD físico pendiente |
| Red `ApplicationLoader`, `ConnectionsManager`, `CoalescedTask`, `NetworkSnapshotAge` | PR132 ya corrige caducidad monotónica/coalescing en stageQueue. No añadir debounce, timeouts o otro reconector. Investigar espera real de stageQueue y concurrencia de snapshots antes de cambios nuevos | P1 / alto / sin nuevo cambio de red |
| Sincronización `MessagesController`, `MessagesStorage`, `SendMessagesHelper`, `NotificationsController` | Contratos críticos preservados byte a byte respecto a PR136; falta ejercicio de multicuenta, push, llamadas y recepción durante scroll | P0 si hay fallo / alto / funcional físico pendiente |
| Archivos `FilesWork`, `FilesCache`, `FilesCodeView`, `FlexyFilesSheet` | Apertura/filtro ya en worker cancelable; gutter dibuja líneas visibles con buffer de caracteres. No mover sin necesidad las operaciones transaccionales | P2 / medio / sin nuevo cambio |
| Studio `FlexyStudioStore`, transacciones | Trabajo explícito en globalQueue, recovery acotado. Diferir o eliminarlo sin estudiar journal rompería recuperación | P2 / alto / conservar |
| JNI/MTProto/Chaquopy | Inventario del árbol y contrato de no modificación; sin reescritura de protocolo ni de librerías heredadas | P1 solo con perfil / muy alto / no recompilado |
| Identidad y variantes | Beta `com.flexygram.messenger`, certificado público oficial `5a598fb5…d2ef66c`; Alpha conserva su identidad. Gradle, versión, firma, recursos y manifiestos intactos | P0 / muy alto / check de identidad repetido |
| CPU/RAM/SQLite/energía/temperatura | No hay dispositivo conectado ni trazas que justifiquen nuevas políticas de pools, caché o SQL. Evitar ajustes especulativos | P1 / alto / NOT_MEASURED |

## Cambios P0 y reversión

Cinco archivos de producción, sin dependencia nueva, opción de Ajustes, temporizador ni callback permanente. Los cambios son independientes: revertir el bloque de admisión táctil, el cache/no-op de pestañas, los no-op del track o el cache de contorno por celda (MessageDrawable + invalidate de SignatureBorderPath) por separado. Conservar tests y overlay exacto con cada cambio que se integre. Los manifests históricos no se regeneran; `deep_performance_contract.py` proyecta únicamente bytes exactos revisados para auditorías anteriores y rechaza mutaciones desconocidas. Esa proyección no corre dentro de Android ni sustituye los nuevos tests de comportamiento.

1. **Entrada:** rechazo temprano de condiciones que la política final ya rechazaba. No cambia los bounds, el hit test, las exclusiones de previews/sheets/teclado, duración/curva ni dispatch de DOWN/UP. `onAnimationEndCheck(true)` sigue siendo el único dueño del cierre. No se sintetizan taps.
2. **Pestañas:** cache máximo de un filtro por View; una nueva tonalidad reemplaza la anterior. Texto e imágenes reciben siempre el valor actual, incluso tras nuevo avatar/icono. Overrides inactivos guardan el factor sin invalidar y los cambios visibles siguen invalidando.
3. **Sliders:** fracción normalizada y colores iguales no modifican estado ni piden redibujo. Cambios reales, draw, alpha/filtro, hitbox y SeekBar nativo siguen iguales. No se alteran sliders/diseño de Work1.

4. **Scroll de burbujas:** el contorno parcial y su shader viven en el PathDrawParams nativo de la celda, de forma lazy. El borde completo y el modo clásico no crean esa caché. Cada regeneración de la silueta invalida el contorno derivado; no se usa un mapa global por tamaños, bitmap por mensaje ni referencias de cuenta/conversación. El fallback sin caché nativa conserva el dibujo directo. Aumenta la memoria de geometría de las celdas que usan borde parcial; medir ese coste en el pool real. No elimina efectos ni reduce su calidad o fotogramas.

No hay cambio nuevo de red, cuenta, SQL, protocolo, contenido de mensajes, autenticación, llamadas, notificaciones, JNI, firma o paquete.

## Línea base y comparación reproducible

`run_probes.py` lee la fuente baseline exacta de git y la candidata del árbol. Compila/ejecuta los cuerpos reales de los métodos táctil/de pestañas y la clase completa del track con **dobles explícitos** de Android, ventana, jerarquía e imágenes. No son pruebas end-to-end de ActionBarLayout. `operation-results.json` conserva resultados deterministas, no microsegundos ni FPS.

- 1.049.080 combinaciones/variantes del hook: misma decisión de cierre; los 20 flags combinatorios son un barrido sintético de exclusiones, **no una distribución de uso ni un porcentaje de mejora**. El coste de travesía dentro de NativeInstantTouchTarget se simula como una llamada, no como tiempo real.
- 10.000 actualizaciones de paleta y transiciones/reemplazos de imagen: mismos colores y destinos.
- 10.000 cambios de override: mismo estado; los cambios visuales invalidan.
- 2.800 comparaciones de comandos de dibujo del track con cinco densidades, clipping de fracción y max cero; no equivalen a píxeles de GPU.
- Los conteos de 1.000 llamadas repetidas muestran eliminación de trabajo redundante bajo esa condición únicamente.

```bash
python3 tools/deep_performance/run_probes.py
python3 -m unittest discover -s tools/connected_alpha -p test_deep_performance.py -v
python3 tools/connected_alpha/run_checks.py
python3 tools/performance_p0/run_checks.py
python3 tools/performance_p0/check_wiring.py
python3 tools/identity/check_identity.py
```

Requiere historia git accesible y JDK con jdk.compiler; fixtures históricos también requieren javac en PATH. El módulo media debe estar en el SHA del gitlink, sin checkout parcial. `verification.json` registra exactamente los comandos y resultados ejecutados. No confundir compilación aislada contra android.jar con Gradle, DEX, ensamblado nativo o APK completa.

## Evidencia específica de scroll y efectos

`ScrollEffectsCacheTest` compila el MessageDrawable de PR136 y el candidato con gráficos nativos de Robolectric/API35; tema/servicios/fuente de blur siguen aislados. El contador de reconstrucciones se inyecta únicamente en la copia de SignatureBorderPath compilada por el test; no entra en producción. El test anterior y el nuevo ejecutan el mismo algoritmo de contorno.

- 12 celdas de tamaños distintos × 100 repeticiones: 1.200 reconstrucciones antes, 12 después, para cada uno de los cuatro lados parciales y ambas direcciones. Es un conteo de operaciones sintético, no FPS, tiempo de scroll ni porcentaje de mejora global.
- Los píxeles comparados coinciden para bordes completos/parciales, cinco posiciones, Fusion 0/1/2, dos temas, tres densidades y alfa 0/77/255. Se verifica además resize, agrupación, cambios de cola, makePath y reutilización de caché.
- El borde completo predeterminado ya evitaba PathMeasure: no se atribuye a esta corrección una mejora de contorno en ese modo. Blur ya calcula su kernel fuera de UI y reutiliza una fuente acotada por conversación; sus costes GPU/matrices/composición quedan para perfil real. Transparencias y clipping siguen pudiendo cargar la GPU: no se declara resuelto todo el lag.
- 47 tests gráficos Android aislados: cero fallos, errores u omisiones. No es compilación ARM64 completa ni ejecución en Android17/GPU del Poco.

Reproducción: `python3 tools/connected_alpha/bubble_visual/run.py --sdk-root /ruta/android-sdk --maven /ruta/mvn`.

## Verificación del lote

373 métodos de pruebas de fuentes/host PASS; suite general 144 PASS /31 omisiones opcionales por corpus externo/R8; 47 pruebas Android aisladas PASS sin fallos, errores u omisiones. P0 contra API37, identidad, wiring nativo y auditoría exacta PASS. Comandos y hashes de los cinco archivos de producción: `verification.json`. La prueba histórica de Work1 conserva su comparación byte a byte salvo la proyección exacta de la nueva API de invalidación; el comportamiento candidato se verifica además por geometría, caché y píxeles.

## Aceptación física y siguiente problema

No hay Poco/ADB en este entorno. Arranque frío/tibio/caliente, toque-a-visible, abrir/cerrar chat, pestañas, carga/sincronización/reconexión, p50/p95/p99, jank/FrameTimeline, CPU, RAM/GC, batería y temperatura quedan **NOT_MEASURED**. No se promete mejora de Internet ni se declara una experiencia perfectamente fluida.

Próximo paso de mayor impacto: traza comparativa de navegación y scroll real, con previews/teclado, inversión rápida de fling, multitap, cierre interrumpido, recepción de mensajes y blur frío/caliente, seguida por ocupación de stageQueue durante cambios Wi-Fi/datos y reanudación. Usar misma identidad Alpha existente y entrega privada autorizada, sin PKCS12 Beta ni nueva firma. Preservar sesiones/datos. Medir 60/90/120 Hz realmente observados sin forzarlos; 20+ repeticiones comparables y orden ABBA, y sesión sostenida de 15–30 minutos. El comparador existente de PR132 tiene baseline propia: **no usarlo sin actualizar explícitamente la procedencia a PR136** para este nuevo par.

No se bloquea la primera revisión del código esperando métricas inexistentes, pero no se da aceptación física ni se fusiona este lote. No se integra PR137 ni se promueve Beta. No se solicita ni utiliza material privado, ni se compila/publica APK en este lote.
