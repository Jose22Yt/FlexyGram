# P3/P4: adaptadores Android y JNI de lectura

Responsable: @Lukhou23. Rama independiente `preparation/android-session-adapters`, PR #36 apilado sobre #35. Base exacta: `985f8ec8f426225dfd7fba772272fd77e02b7fcf`. PR #34 comprobado en `36e27309bee4e6c27e3850321fa0c6c44e2acf42`. Se conservan fuentes, historial, GPL y créditos Telegram/Exteraless.

## Implementación

| Componente nuevo | Operación real implementada | Límite |
|---|---|---|
| AccountProbe / TelegramAccountAdapter | Inspección de slot fijo mediante AccountInstance, UserConfig, presencia de preferencias y tgnet.dat/.bak; disponibilidad de handles MessagesStorage/ConnectionsManager | No carga claves ni restaura cuenta; archivos nativos existentes significan revisión, no sesión confirmada ni permiso de borrado |
| OperationJournal | Máquina de estados, UUID de operación, revisiones, CAS y rechazo de operaciones interrumpidas/inciertas | Metadatos separados del formato original Telegram |
| AndroidJournalBackend | AtomicFile, FileLock para lectores/escritores, formato acotado y validado, ruta no-backup privada, rechazo en hilo principal | Semántica Android, persistencia ante apagado y filesystem real todavía pendientes |
| JournaledLocalSessionStore | Conecta el contrato SessionStore del núcleo con journal, probe y LocalSink sintético; revalida cuenta antes de escribir | No es un almacén MTProto ni activa UserConfig; COMPLETED no significa login |
| LoginFlowOwner | Cola serial, limpieza de entradas, cierre, cancelación, fallo tipado, owner retenible y recreación sin replay | Solo simulación local. Reintento exige nuevo owner y aprobación explícita, únicamente FAILED/CANCELLED |
| LoginActivityAdapter | Consume la LoginActivity original, valida slot, enlaza observador con Handler principal, callbacks locales y separación view/owner | No parchea los botones/páginas actuales ni crea otra UI; falta conectar los puntos nativos selectivamente |
| AndroidNativeBridge / SessionReadOnlyBridge.cpp | JNI real de lectura: política enlazada, PID/UID actuales, slot, aislamiento y máscara de capacidades; coherencia con Java | No llama getInstance nativo ni init. Informa explícitamente UNKNOWN para inicialización del motor |
| DeniedTelegramTransport | Denegación directa y por RequestCoordinator | No envíos ni cancelaciones JNI reales |

Las lecturas de presencia de cuenta se realizan **antes** de solicitar MessagesStorage: su constructor original puede abrir/recuperar DBs. No se afirma que ese efecto haya provocado un fallo observado en Android. La disponibilidad de handles no demuestra que una DB asíncrona esté abierta. Cambios concurrentes de sesión se reevalúan antes del commit local; un futuro commit real necesita garantías transaccionales adicionales.

## Diario y recuperación

`NONE -> STARTED -> WRITING -> COMPLETED / FAILED / UNCERTAIN`; desde STARTED también es posible FAILED/CANCELLED. Un objeto nuevo no adopta una operación pendiente. Reintento explícito solo desde FAILED/CANCELLED y con cuenta demostrada vacía. Un error de backend invalida ownership; no se adivina la revisión ni se borra el registro.

STARTED tras reinicio significa **activa o interrumpida**, no fallo confirmado. WRITING/UNCERTAIN significa que no se puede asegurar el resultado. COMPLETED es un recibo LOCAL; FAILED exige que el LocalSink declare fallo sin escritura. Si falla la evidencia de finalización después del sink, el controlador devuelve STORAGE_UNCERTAIN aunque el sink haya terminado. No hay restauración, borrado, logout, reset de claves ni revocación automática. Un cierre reentrante se difiere durante toda la escritura, incluida la fase de journal.

El estado de vista contiene attached, contador de adjuntos y ownerDestroyed. Una configuración nueva sustituye el Binding y conserva el owner, no el Fragment. El Bundle guarda solo un marcador de reinicio y slot. Un proceso nuevo queda RESTART_REQUIRED; no reinicia peticiones. Esta separación no sustituye el análisis de saveSelfArgs/estado de las páginas nativas de LoginActivity cuando se conecten los callbacks.

AtomicFile por sí solo no proporciona bloqueo; por eso ambas operaciones toman FileLock. Referencias de plataforma: [AtomicFile](https://developer.android.com/reference/android/util/AtomicFile), [Context.getNoBackupFilesDir](https://developer.android.com/reference/android/content/Context#getNoBackupFilesDir()). Los registros contienen únicamente metadatos no secretos; este módulo no implementa cifrado de sesiones ni debe recibir claves reales.

## Validación de este HEAD

Código y tests: `29248617be6a20f4748f12d281eef2cae2292f6b` (el README del módulo y estas evidencias se añaden después, sin cambiar código).

- **77 pruebas nuevas**, normales y con -O: 154 ejecuciones, sin fallos/omisiones finales.
- **9 regresiones existentes** reejecutadas normales y con -O para los cuatro parches, resolución API y frontera: 18 ejecuciones. No se presentan como pruebas nuevas.
- Total ejecutado final: **86 distintas / 172 ejecuciones**. No se suman las 110 históricas ni los subcasos/compilaciones como tests distintos.
- Java real compilado con JDK21 y --release 8, además de compilación con el modo de fuente predeterminado JDK21; se compila también AccountInstance original sin cambios. UserConfig, MessagesStorage, ConnectionsManager y framework son dobles explícitos en ejecución host.
- JNI nuevo ejecutado de verdad en JVM Linux contra VariantPolicy.cpp real y cabecera cerrada. No JNI en Android/ARM64. Se comprueban UID/PID/política/capacidades, slot inválido directo, biblioteca ausente, llamadas denegadas y ausencia de símbolos de transporte.
- Fragmento CMake nuevo compilado en host con visibilidad oculta y exports.map original: exporta las dos entradas JNI. Una política abierta falla en static_assert; otra variante falla en configuración.
- Referencias Android compiladas contra android.jar real API24 (hash fijado), usando clases Java de --release 8. Esto **no** certifica Java-library compatibility, desugaring D8, minSdk24 de toda la app, API37 ni ejecución Android.

Durante la sesión se perdió un workspace antes de publicar; sus logs preliminares no se usan como evidencia final. Se recuperó el código, se publicaron checkpoints y se repitió la validación final completa. Los primeros ensayos detectaron errores de dobles Java y la falta de MethodHandles al usar el bootclasspath antiguo con javac21; la prueba final valida símbolos Android con el SDK real y declara su alcance limitado. No se fingió un PASS de compilación Android. Comandos, hashes e inventarios finales están en [evidence](evidence/results.json).

La única actualización de una prueba anterior amplía su inventario a los tres directorios nuevos y añade la comprobación de que el nuevo módulo siga sin registrar. Continúa exigiendo igualdad de los originales compartidos. La prueba nueva de frontera compara con #35 y rechaza cualquier otro archivo modificado, salvo esa prueba de inventario.

## Revisión selectiva de los cuatro parches

No se aplicaron al checkout ni a #34; solo a copias temporales. PR #34 conserva el mismo código fijado, por lo que no hubo que cambiar su contexto.

| Parche de #35 | Comprobación reejecutada | Requisito de integración |
|---|---|---|
| 0001 UserConfig null | Método original y corregido compilados: rechazo antes de mutar | Revisar callers Android; no prueba la causa de CRASH-001 |
| 0002 reset/retry implícito | Rama privada simulada: error entregado sin cleanup(true) ni resend | Flag original false; no atribuir incidentes ni eliminar recuperación protocolaria legítima |
| 0003 selección API realAlpha | Aislamiento conserva 0/vacío; fuera de él rechaza ID0/6/pareja inválida y overrides heredados | No acredita propiedad de credenciales ni habilita red |
| 0004 logs Java/JNI | Expresiones activas originales/corregidas compiladas con canarias; sin tokens/teléfono/hash en los sinks corregidos | Revisar además error.text, excepciones SDK y logs nativos restantes; no es certificación universal |

Las nueve regresiones cubren también apply --check y el resolver API existente. Cada parche tiene SHA-256 en el recibo. Su revisión estática y host no sustituye una compilación Android después de aplicarlo selectivamente.

## Traspaso exacto para Work 2

1. Conservar su compilación #34. Revisar #35 y después #36 como cambios apilados; no fusionar automáticamente. El módulo no se registra por estos commits.
2. Después de estabilizar P1/P2, registrar únicamente para realAlpha las fuentes main del núcleo, main del nuevo módulo y android del nuevo módulo. No añadirlas a Diagnostic/BetaDevelopment/Production. Esto requiere un cambio Gradle posterior revisado, no incluido aquí.
3. Revisar y aplicar por separado `TMessagesProj_Modules/telegram-session-android/integration/0001-realalpha-read-only-jni.patch`. Solo añade el fragmento al target realAlpha después de creado. El exports.map original permite Java_*; no se cambia. No aplicar los cuatro parches de seguridad por lote sin revisión.
4. Mantener la carga NativeLoader original; AndroidNativeBridge no la ejecuta. En el worker existente, leer atestación con contexto de aplicación y slot fijo, construir TelegramAccountAdapter y AndroidJournalBackend. Ante UNKNOWN/UNAVAILABLE o artifacts existentes, detener el flujo sin limpiar archivos. No usar selectedAccount en callbacks.
5. Para ensayos sin red, usar exclusivamente un TransportPort LOCAL_SIMULATION revisado y un LocalSink sintético; los únicos ejemplos ejecutables están en tests y no deben convertirse en persistencia real. Crear JournaledLocalSessionStore y LoginFlowOwner con worker asíncrono, nunca Runnable::run en Android.
6. Conectar los eventos de las páginas originales de LoginActivity a los métodos locales únicamente en el ensayo revisado. El callback de render debe conservar las páginas nativas. No llamar onAuthSuccess/setCurrentUser por LOCAL_COMPLETE. Cerrar Binding al destruir vista; retener solo owner en configuración; al finalizar, destroyOwner; tras muerte de proceso, restoreAfterProcessDeath. Una cancelación no es logout.
7. Compilar realAlpha ARM64 completo con JNI/Chaquopy, ejecutar D8 y verificadores existentes, y validar arranque, DB, JNI y ciclo de vida en Android autorizado. Este PR no hace esa compilación ni entrega APK.

## Bloqueos antes de conexión real

Faltan cuatro conjuntos de integración/revisión, no una simple preferencia:

1. Validación Android P1/P2 de Work 2 y posterior integración/compilación del puente y adaptadores. Probar carga en ARM64, API24/actual y ciclo de vida real.
2. Persistencia nativa: enlazar journal/epoch con el material del handshake original, distinguir claves nuevas de preexistentes, commit/recuperación entre Config, UserConfig y MessagesStorage, sin nuevos formatos de auth_key. El LocalSink de aquí **no resuelve** ese commit real.
3. Transporte/autenticación: puerto Telegram revisado, cancelación por propietario/slot/token sin revocación, errores tipados seguros, mapeo TLRPC y LoginActivity completo (2FA/QR/signup/recuperación), y aplicación/revisión de los parches de logging/API. Mantener operaciones sobre otras sesiones denegadas.
4. Pareja API propia desde configuración privada aprobada, nueva política revisada por variante, verificaciones del binario y autorizaciones independientes para firma/instalación y prueba de conexión/cuenta. No se necesitan ni solicitan secretos en este PR.

No se habilita INTERNET, autenticación, MTProto, push, Firebase, plugins ni servicios externos. No se cambian políticas/variantes, main/develop, #34, APK anteriores o Actions; no hay firma, instalación ni distribución. La política JNI existente conserva sus bytes y la nueva integración permanece sin aplicar.

## Defecto de compilación corregido durante esta revisión

Una regresión adicional compiló las fuentes con el modo predeterminado de JDK21 y reprodujo una ambigüedad entre OperationJournal.Record y java.lang.Record (20 errores del compilador, un test fallido; no 20 tests). Se corrigió con importaciones explícitas en dos adaptadores y el arnés. Las 77 pruebas finales incluyen este modo y --release 8; el log previo se conserva en evidence/jdk21-before-fix.log. No se afirma que el Gradle Android de Work 2 haya sufrido ese error: no se ejecutó su compilación.
