# Auditoría estática del arranque y variantes

**No hay tiempos medidos.** La lentitud de primera apertura se conoce por observación del usuario. No se atribuye a una compilación defectuosa, a Python, a una dependencia nativa ni a una operación particular sin trazas. Un build exitoso solo prueba la finalización del proceso de compilación.

## Rutas y candidatos para instrumentar

Fuente fijada: `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2`. Paths bajo `TMessagesProj/src/main/java/`, salvo indicación.

| Ruta / ubicación | Hilo y trabajo observado | Qué medir posteriormente |
| --- | --- | --- |
| [ApplicationLoader.onCreate L350–436](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java#L350) | Entrada de Application en hilo principal: infraestructura/logs, NativeLoader L388, native_setJava L394, detector ANR en Debug L408, configuración osmdroid, iconos, proxies, LinkCleaner/M3prewarm | Duración inclusiva y por bloque, archivos, binder, CPU y partes que delegan a workers; invocar un inicializador no prueba que todo su trabajo sea síncrono |
| [LaunchActivity.onCreate L432–488](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/ui/LaunchActivity.java#L432) | VM StrictMode/LeakDetector bajo flags Debug; postInitApplication L446 antes de super.onCreate L482; recursos Theme L487–488 | Camino crítico hasta primer frame, coste de verificaciones, inflación y creación de temas |
| [ApplicationLoader.postInitApplication L230–346](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java#L230) | Guardia applicationInited; invocada desde Activity en UI y también para procesar push; configuración, LocaleController, receptores, Monet, PluginsController, helpers, telemetría, MediaController y Billing | Llamadas síncronas, arranque provocado por push antes de UI, prioridad de colas y esperas |
| Bucle postInit L312–327 y L333–345 | Recorre `UserConfig.MAX_ACCOUNT_COUNT=10`: UserConfig, MessagesController, ConnectionsManager; contactos/descargas. Algunas acciones solo en cuentas activadas, no diez cuentas autenticadas | Distinguir instanciación y lectura por slot de red/sincronización real. Comparar fixture sin cuentas y fixture sintético controlado |
| [ConnectionsManager.java L231–293 y L746–790](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java#L231) | Construcción síncrona, preferencias/PM/datos del dispositivo, llamada JNI. Nativo `init` llega a `loadConfig` (C++ L3732) | I/O de config por slot, binder de PackageManager, carga nativa y trabajo delegado a red |
| SharedConfig.measureDevicePerformanceClass L1852–1890 | El método llamado en init lee frecuencias CPU por sysfs con RandomAccessFile (L1877), memoria e información de dispositivo | Contar llamadas y su coste en hilo principal; no asumir que un resultado cacheado evita esta llamada directa |
| [NativeLoader.initNativeLibs L113 y siguientes](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/NativeLoader.java#L113) | Método synchronized/idempotente; System.loadLibrary primero. Si falla, fallback de extracción ZIP y carga desde files/lib (helper L62) | Linker/JNI_OnLoad e I/O. El fallback no se da por ejecutado solo por existir |
| [MessagesStorage L247–251](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/MessagesStorage.java#L247) | Crea storageQueue y publica openDatabase(1), que no se ejecuta entero en UI | Apertura/migraciones en worker; `ensureOpened` (L163) usa latch, así que un llamador podría esperar si llega antes. Probar el llamador concreto con trazas |
| Theme/recursos/fondo | Theme.createCommonResources/createDialogsResources y carga wallpaper (LaunchActivity L592), temas dinámicos desde postInit | Primera decodificación, I/O, GPU/shaders, cachés; separar fondo asíncrono de bloqueo del frame |
| Push | initPushServices programa retraso de 1 s; obtención de token con cola/callback | Binder/servicios y solapamiento. Un timeout configurado de 60 s no prueba bloqueo de UI durante 60 s |

La espera a NativeLoader presente dentro de openDatabase pertenece a storageQueue; no atribuirla al hilo principal sin una espera aguas arriba. La inicialización de recursos y SQLite puede tener efectos de primer uso, pero faltan datos para cuantificarlos.

## Python y plugins: condiciones reales

[PluginsController.init L119–136](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/app/exteraless/plugins/PluginsController.java#L119) retorna si el motor no está habilitado. `isEngineEnabled` L168 usa **false por defecto**. Modo inseguro (L207) y desarrollador (L235) también son opt-in. Una instalación con preferencias conservadas puede tener otros valores; no se leyó su estado en el teléfono.

[PythonPluginsEngine L61 y L114–140](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/app/exteraless/plugins/PythonPluginsEngine.java#L114) usa ejecutor de un hilo `plugins-engine`, prioridad menor que normal. `ensureStarted` publica `Python.start(AndroidPlatform)` e import de plugin_loader allí; publica el pin de PythonThreadState en UI; el callback de arranque está documentado para el executor. Con motor habilitado se revisan watchdog/recuperación, permisos, escaneo y callbacks APP_START. Extracción/imports pueden consumir CPU/I/O en background y competir con UI; no prueba de bloqueo directo ni de que ocurriera en esta primera apertura.

Los hooks de envío de peticiones y `PluginSinkGate` implementan controles de permisos, incluidos grupos sensibles TL_auth/TL_account. El modo inseguro y la ejecución de código extensible requieren tratamiento de confianza; no se certifica un aislamiento equivalente al sandbox de otro UID. No hay inventario de plugins instalados en el teléfono ni evidencia para culpar a uno.

Si se habilita modo desarrollador, PythonPluginsEngine llama a `start_dev_server`. `src/main/python/dev_server.py` escucha por defecto en loopback `127.0.0.1:42690`, requiere token salvo ping y puede admitir herramientas de desarrollo. El token se escribe en archivo privado y también en log. Loopback no impide conexiones de otras apps del mismo teléfono; la autenticación del servidor importa. No se asume que estuviera iniciado ni que fuera accesible desde la red externa. En diagnóstico propuesto debe permanecer apagado y sus secretos no deben registrarse.

## Diferencias reales entre variantes

Fuente: [build.gradle L241–270](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/build.gradle#L241), BuildVars y LaunchActivity. Solo Debug fue compilado y comprobado como archivo; no se generaron ni probaron Staging/Release.

| Propiedad | Debug actual | Staging / Release declarados |
| --- | --- | --- |
| debuggable / jniDebuggable | true / true | false / false |
| minifyEnabled / shrinkResources | No se activan, defaults false | true / true |
| Reglas R8 | No se activa el pipeline de minificación de esas variantes | proguard-android-optimize y proguard-rules.pro |
| multidex | true | true |
| Fallbacks de dependencias | Variante Debug | release, staging, debug; revisar resolución efectiva antes de comparar |
| Firma | Release si hay keystore configurado; si no, Debug. Archivo real firmado Debug | La misma política de fallback: el nombre Release no garantiza firma de producción |
| DEBUG_VERSION, isBetaApp | Activados por tipo/BuildConfig.DEBUG | No activados por esos flags |
| Logs | Activados por defecto al inicializar BuildVars con contexto; sinks sensibles encontrados | Pueden activarse por preferencia persistida; quitar secretos debe cubrir todas las variantes |
| Herramientas | ANRDetector y rutas LeakDetector/VM StrictMode condicionales; DEBUG_TOOLS generado false | No se asume esa instrumentación; Crashlytics puede activarse por preferencia en no Debug |

**No todos los binarios nativos Debug carecen de optimización.** En esta compilación, `.cxx/Debug/21e6c3z6/arm64-v8a/CMakeCache.txt` identifica Debug, pero flags DEBUG específicos están vacíos y `build.ninja` contiene, por ejemplo, `-Oz` en numerosos objetos. [jni/CMakeLists.txt L7–11, L112, L155 y L205](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/jni/CMakeLists.txt#L7) define flags propios, optimizaciones y símbolos `-g`. El runtime Python se prepara por un script independiente en Release; los prebuilts mantienen sus propios flags. No se afirma que todo JNI use -O0 o que pasar a Release vuelva más rápido cada componente.

R8 puede reducir tamaño y trabajo de carga; también necesita reglas correctas para reflexión, JNI, hooks y Chaquopy. Es una expectativa técnica por validar, no una mejora medida ni una garantía de equivalencia. El primer uso además puede implicar trabajo ART, extracción, creación de archivos/cachés, shaders y carga de servicios. No se ha establecido cuáles se ejecutaron ni cuánto tardaron.

## Medición propuesta, no ejecutada

Definir separadamente: instalación/primer lanzamiento con datos nuevos, cold start después de matar proceso, warm y hot start; primer frame (TTID), pantalla realmente lista (TTFD con criterio/reportFullyDrawn coherente) y disponibilidad de red posterior. No mezclar la espera de autenticación o red con tiempo hasta primer frame.

Tras aprobar una identidad y variante seguras, usar Perfetto para correlacionar hilo principal, sched, binder, ART/class loading, disco, linker y workers. Añadir secciones Trace con nombres constantes por bloque, sin IDs de cuenta, rutas privadas ni payloads. Logcat solo del proceso diagnóstico limpio, con lista de etiquetas permitidas y marcadores de tiempo, después de corregir sinks de secretos. Recoger fallos del linker/Python como tipo/módulo y stack saneado, no variables o datos de mensajes.

Macrobenchmark debe apuntar a una variante **no depurable y profileable**, cercana a Release. No suprimir la validación de Debug para presentar su número como resultado representativo. Medir Debug con el mismo protocolo externo/Perfetto y etiquetarlo como diagnóstico. Para separar efectos: A) comparar debuggable true/false con las demás opciones iguales; B) comparar luego la variante con R8/recursos optimizados. Son factores distintos.

Mantener mismo commit, fixture sin cuentas, estado de plugins, red, política de caché/compilación, firma de prueba controlada y dispositivo; cada variante usa su sandbox nuevo. Registrar diferencias de applicationId/flags inevitables. Declarar CompilationMode (None/Partial/Full según objetivo), perfiles base y warmups; proponer 10–30 repeticiones por escenario, mediana y percentiles adecuados al tamaño de muestra, sin descartar atípicos sin criterio. Controlar temperatura, batería, tareas de fondo y orden alternado. No ejecutar Actions para ello. Ninguno de estos experimentos está ejecutado o aprobado para implementación todavía.

Fuentes primarias: [Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview), [tiempo de inicio Android](https://developer.android.com/topic/performance/issues/launch-time), [Perfetto](https://perfetto.dev/docs/). Las propuestas instrumentan la arquitectura original; no autorizan optimizaciones ni el Paso 4.
