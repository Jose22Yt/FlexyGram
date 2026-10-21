# realAlpha: primer fallo físico de arranque

Estado: **arranque FALLIDO en Android; causa raíz todavía NO confirmada**. Informe del usuario del 21 de octubre de 2026: Poco X8 Pro, Android 17, HyperOS 4. Pantalla negra breve, regreso al escritorio, reproducible; nunca muestra lista de chats. La grabación fue mencionada, pero no se ha inspeccionado ni sustituye una excepción/motivo de salida.

APK afectada: `FlexyGram-realAlpha-offline-test-temporary-signed.apk`, 113081095 bytes, SHA-256 `c4f89fbe374f39d57fb98f73ef92ac9d493ee2061343669b59a8eab179cb9fb9`; certificado `f5dd0e790d56652758e38cf0c905633645d4ec4a45973cd6979ddb62f0c4e398`. Respaldo 105081156 bytes, SHA-256 `7ababd3649679397e224cd0d8d8e2cb8f31c1c6b16487712ec535aa37315a830`. No se sustituye ni se vuelve a firmar. La clave temporal ya no existe.

Base: PR #37, HEAD `8f8c25234a973c5dfaf411978b2d4f5c2173ff93`, código `50d82ba07adfe4acd251fb5761f1334050fb3ff9`. Rama independiente: `fix/real-alpha-startup-diagnostics`. No modificar/fusionar PR #37, main o develop.

## Hallazgos comprobados en el código

| Tramo | Evidencia y alcance |
|---|---|
| Antes de Activity | Android crea Application y proveedores del proceso. `ApplicationLoader.attachBaseContext` establece contexto; `onCreate` inicializa AndroidUtilities y carga NativeLoader, llama `ConnectionsManager.native_setJava(false)`, instala handlers y configura recursos/utilidades. Puede fallar antes de RealAlphaActivity. |
| JNI | NativeLoader captura errores de carga y conserva mensajes internamente; `ApplicationLoader` convierte un UnsatisfiedLinkError posterior en otro RuntimeException sin causa. Los 96 ELF estáticamente aptos no prueban JNI_OnLoad, ART o linker de este teléfono. |
| Policy/bootstrap | RealAlphaPolicy exige identidad/scope/capacidades cerradas. La APK afectada pasó esos contratos compilados. Eso reduce la hipótesis de identidad de compilación equivocada, sin probar esta ejecución. RealAlphaBootstrap comprueba todos los slots vacíos antes/después de inicializar. |
| Evidencia perdida | **Confirmado**: `RealAlphaBootstrap.ensure` captura RuntimeException/Error y lanza `FLEXYGRAM_REAL_ALPHA_INITIALIZATION_FAILED` sin causa. No es posible recuperar el error original a partir de esa envoltura. No se debe reintroducir una causa cruda que pueda contener datos privados. |
| Post-init | `applicationInited=true` se asigna antes de completar LocaleController, configuración, Glyph, plugins, controladores, MediaController y contactos/descargas. Un fallo deja inicialización parcial. No se añade un reintento ni se limpia configuración para ocultarlo. |
| Controladores sin cuenta | Se construyen controladores para todos los slots; ConnectionsManager Java evita native_init en aislamiento, pero getters como native_isTestBackend/getCurrentTime siguen pasando por JNI. El C++ tiene salidas `exit(1)` ante errores de epoll/pipe. Son rutas auditadas, **no la causa probada**. Transporte y sockets MTProto siguen denegados. |
| Glyph | El constructor reconoce fabricante Nothing y `init` retorna si no está soportado; esto hace menos probable un bind OEM en el Poco. No prueba ausencia de un error de carga de clase, ni cambia el mínimo declarado API33 del AAR, ni certifica API24. |
| LaunchActivity | El Intent se reemplaza por ACTION_MAIN sin extras. El finish temprano para ACTION_SEND/MULTIPLE no corresponde a ese flujo. Se heredan navegación y callbacks originales, sin introducir otro motor. No se descartan otros finish/cierres sin evidencia. |
| DialogsActivity | El factory realmente crea DialogsActivity; normalmente LaunchActivity sin cuenta abre LoginActivity. Se fuerza una ruta sin cuenta que las pruebas host doblaban. onFragmentCreate/createView acceden a controladores, privacidad, historias, tema y recursos; pueden fallar síncrona o asíncronamente. `MessagesStorage.loadUserInfo` sí retorna para user null: esa llamada concreta no demuestra un NPE. No hay base para declarar que todos los demás supuestos de cuenta sean seguros. |

No se ha observado el stack del dispositivo. No se atribuye el fallo a Glyph, firma, INTERNET, HyperOS, JNI o falta de cuenta por el aspecto de la pantalla. Tampoco se considera que los tests host hayan ejecutado los inicializadores reales de Android.

## Corrección de observabilidad revisable

No se propone un arreglo especulativo del crash. Se prepara `realAlphaStartupDiagnostic`:

- Build type opt-in `startupDiagnostic`, solo flavor realAlpha. Paquete **`io.github.jose22yt.flexygram.realalpha.startupdiagnostic`**, siempre unsigned. Requiere `-PflexygramRealAlpha=true -PflexygramRealAlphaStartupDiagnostics=true`, ARM64 real.
- Launcher `StartupReportActivity`, UI mínima Android sin inicializar Telegram. Una Application diagnóstica omite deliberadamente `ApplicationLoader.onCreate` en el proceso del informe.
- La Activity real y el proveedor jlatex viven en `:startup_probe`. Ese proceso sí ejecuta ApplicationLoader y la ruta nativa original; no se simula JNI ni la lista. El probe no es exportado ni launcher.
- Una transformación exacta, con hashes de entrada/salida, añade etapas a copias generadas de siete fuentes. **No cambia los bytes de las fuentes compartidas/flavor originales.** Solo el compilador de esta variante sustituye esas copias; Kotlin/Java dependen explícitamente del generador. Otros builds no reciben marcadores.
- Etapas: attach/Application, JNI, policy, slots, post-init/config/Glyph/plugins/controladores/Media, LaunchActivity, factory DialogsActivity, fragment/createView/retorno, resume/primer dibujo/destrucción/finish. Retorno de un método no significa que toda tarea asíncrona haya terminado.
- El bootstrap registra la categoría y cadena sanitizada **antes** de descartar la causa. NativeLoader registra fallos observados, que pueden ser recuperables; `OBSERVED` no equivale a crash. El handler diagnóstico evita guardar el Throwable crudo en CrashLog.
- Se escribe un diario atómico limitado a 16 KiB en `getNoBackupFilesDir`, dentro del paquete diagnóstico. Solo categorías cerradas, alias de clase aprobados y números de línea acotados. No mensajes, nombres arbitrarios de método/clase, rutas, filenames, nombres de hilos, user IDs, sesiones o argumentos. Las líneas corresponden a las copias generadas reproducibles desde `startup-overlays.json`.
- Android API30+ consulta `getHistoricalProcessExitReasons(getPackageName(), 0, 8)` y filtra exactamente `:startup_probe` y el último intento solicitado. Solo motivo/status numéricos; no getDescription ni getTraceInputStream. No se pide DUMP, READ_LOGS, bugreport o acceso a otras apps. No se intenta consultar el UID de la realAlpha anterior.
- En API24–29 no existe esa API: solo etapas/errores Java y ausencia de evidencia de salida. No se declara compatibilidad de ejecución de estas APIs ni Android17 sin prueba física.

El proceso del informe puede reabrirse después del fallo del probe. No es garantía frente a que el SO mate todo el UID o falle la carga de la propia Application antes de attach. En ese caso se informa esa limitación; no se pide un bugreport completo.

## Interpretación limitada de la próxima evidencia

| Evidencia | Conclusión permitida |
|---|---|
| ERROR con NULL_POINTER, SECURITY, RESOURCE_NOT_FOUND, etc. | Excepción Java observada en la etapa/alias/línea indicados; usar cadena original sanitizada, no solo la envoltura. |
| UNSATISFIED_LINK / CLASS_INITIALIZER / CLASS_NOT_FOUND | Fallo de enlace/carga/inicialización Java observado; no confundir con SIGSEGV. |
| Exit reason 5 (CRASH_NATIVE) | Android clasificó el proceso como crash nativo. No identifica por sí solo biblioteca o instrucción. |
| Exit reason 4 (CRASH) | Android clasificó crash de proceso, normalmente Java; correlacionar con ERROR y etapa. |
| Exit reason 1 (EXIT_SELF) | Salida del proceso iniciada por sí mismo; no demuestra quién llamó exit, ni que sea un finish de Activity. |
| ACTIVITY_FINISHING | La Activity se destruyó con isFinishing; su proceso puede seguir vivo. No equivale a un crash. |
| Exit reason 7 (INITIALIZATION_FAILURE) | Inicialización fallida según Android; investigar etapa/proveedor. |
| Exit reason 6/3/2 (ANR/LOW_MEMORY/SIGNALED) | Distinguir de excepción Java. Una señal sin más datos no identifica el defecto. |
| No registro de salida | Evidencia insuficiente: retención/permiso/tiempo del sistema o proceso todavía vivo. No inferir crash nativo. |
| FIRST_DRAW | Se observó dibujo de la ventana; el usuario aún debe confirmar la lista nativa visible y estabilidad. No basta para aprobar funcionalidad. |

Los números se comprobaron contra android-37/android.jar; referencias oficiales: https://developer.android.com/reference/android/app/ActivityManager#getHistoricalProcessExitReasons(java.lang.String,int,int) y https://developer.android.com/reference/android/app/ApplicationExitInfo .

## Verificación y límites de entrega

Las pruebas del perfil original permanecen. Las nuevas pruebas cubren sanitización (mensajes/frames falsos), cadena de causas cíclica acotada, journal acotado/corrupto, no-op del perfil original, identidad diagnóstica exacta y recuperación de causa desde bootstrap; otro gate rechaza identidades ajenas, INTERNET, IPC abierto y restauración. Los resultados concretos de build/gates están en el recibo de evidencia, no se deducen de esta descripción.

El nuevo verificador `review_startup_apk.py` exige la identidad diagnóstica explícita; el verificador realAlpha unsigned anterior queda intacto y debe rechazar la APK diagnóstica. Verificar manifiesto fusionado y binario, BuildConfig cerrado, DEX de las clases nativas/diagnóstico, hooks compilados, JNI/Chaquopy reales, 96 ELF ARM64 con aceptación 4/16 KiB, hashes reconstruidos y ausencia de firma. No sustituir un gate por una búsqueda de strings aislada.

No se firma, distribuye o instala este nuevo artefacto sin autorización específica. La clave anterior no se puede recuperar ni reutilizar. El paquete nuevo permite instalarlo al lado de la APK afectada; **no desinstalar, actualizar, borrar datos o restaurar sesiones** de esa APK. Nueva firma/entrega/instalación se revisarán por su SHA y certificado. Internet, login, restauración y MTProto siguen cerrados.

Una vez que exista evidencia física suficiente, preparar la corrección mínima para la causa observada en otra revisión; probar primero esta ruta, después la navegación/estabilidad. La instrumentación no significa que se haya corregido el arranque original.

## Resultado de esta preparación

78 casos host distintos aprobados en modo normal y `-O` (56 existentes y 22 nuevos). Build ARM64 completo aprobado, con JNI/Chaquopy reales y wheels aprobados de 16 KiB. Gates del manifiesto fusionado/binario, BuildConfig, DEX, hooks compilados, JNI/Chaquopy, escáner y 96/96 ELF 4/16 KiB aprobados; cero dependencias/símbolos/versiones faltantes. Helper Linux debugpy separado. Firma ausente. No es evidencia de ejecución Android.

Unsigned diagnóstica: 116699043 bytes, SHA-256 `c52933e38c286fe83814399936018eeea00c9166c741bd424af4988de4ccaaf6`. Respaldo local independiente: 105101730 bytes, SHA-256 `985cf8e170fc89a12bbc7cab68f31d8a6b2482d15f7df19e16305c101dcde02a`; CRC y APK interna verificados. Sin entrega de este binario, sin firma y sin claves nuevas. La APK afectada y su respaldo conservan los hashes anteriores. Detalle en `EVIDENCE.json`.
