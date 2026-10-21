# Preparación P3/P4 de FlexyGram — sin conectar Telegram

Responsable: @Lukhou23. Base fijada: `36e27309bee4e6c27e3850321fa0c6c44e2acf42` del PR #34, comprobada antes de trabajar. Créditos, licencias, fuentes y comportamiento actuales de Exteraless/Telegram conservados. No se modifican el PR #34, sus archivos compartidos de Java/JNI, Gradle, manifiestos ni variantes. Este cambio añade un módulo fuente sin registrar, tests, cuatro parches sin aplicar y estas evidencias.

## Componentes implementados y su frontera

El código ejecutable está en `TMessagesProj_Modules/telegram-session-core/src/main/java/io/github/jose22yt/flexygram/session/`.

| Componente | Contrato comprobado |
|---|---|
| SessionScope | Identidad fija por variante y slot 0–9; claves lógicas de almacenamiento diferentes entre variantes/cuentas. No usa UserConfig.selectedAccount ni teléfonos |
| ClosedRuntime | Rechaza capacidades abiertas, API ID/hash no vacíos, aislamiento ausente y atestación distinta. Su decisión es siempre DENIED para Telegram, restauración, logout y revocación; no hay grant, preferencia ni flag que abra la red |
| RequestCoordinator | Consulta la política antes de inicializar/enviar a un puerto TELEGRAM; solo se suministran dobles LOCAL_SIMULATION. Rechaza otra cuenta, operaciones destructivas y cambios a dominio Telegram. Tickets con propietario, sin cancelar otro coordinador aunque coincida el ID numérico |
| Coordinación asíncrona | Buffer de respuesta síncrona hasta que submit devuelva un handle válido; si el adaptador responde y luego falla, no se acepta el éxito. Primera respuesta reservada bajo lock, duplicadas/tardías descartadas, cancelación antes del handle respetada. Sin retries, fallback de proveedor ni resets de claves |
| AuthenticationController | Inicialización sobre slot vacío y comprobación posterior; inicio/verificación locales, reentrada rechazada, generaciones contra callbacks antiguos, staging, commit local explícito y CAS. Error de escritura no supone rollback: STORAGE_UNCERTAIN bloquea reintentos. Nunca activa UserConfig ni borra/revoca sesiones |
| AuthUiRelay | Observador sustituible y liberado al destruir/recrear UI; revisiones impiden estados viejos, incluso publicaciones y ejecuciones desordenadas. Snapshot solo contiene scope lógico, fase, fault enumerado y revisión; nada de códigos, identidad, challenge o tokens |

Los puertos son contratos para adaptadores revisados, **no una sandbox frente a código malicioso que mienta sobre su dominio**. No se suministra ningún adaptador de red. El adaptador Telegram futuro debe declarar TELEGRAM como constante y seguir denegado por ClosedRuntime. No se debe mapear una preferencia a LOCAL_SIMULATION para disfrazar un transporte real. Una futura autorización real requiere otro cambio de código revisado; la política de esta entrega no puede concederla.

Input/Reply poseen copias de char[] y las limpian al terminar/cancelar; los listeners reciben respuestas prestadas, válidas solo durante el callback. Es limpieza de mejor esfuerzo: no certifica borrado forense del heap ni de copias que cree un adaptador. No se transfieren mensajes de excepciones a logs ni snapshots. Los errores de adaptador, observador y ejecutor conservan enums/contadores; errores fatales de la VM no se presentan como recuperación segura garantizada.

SessionStore es un **contrato**, no una implementación cifrada Android. Su commitLocalIfEmpty se prueba con material sintético; no define un formato alternativo de auth_key ni reemplaza la persistencia de Datacenter. No debe copiarse una clave MTProto a esas cadenas/arrays para improvisar una integración real.

## Auditoría del código original y bloqueos

Referencias relativas a la base fijada; nombres de métodos permiten localizar cada ruta aunque cambien líneas posteriores.

| Archivo / método | Hecho por inspección | Conservar / adaptar después |
|---|---|---|
| tgnet/ConnectionsManager.java constructor (233), sendRequest (420), init (759) | Aislamiento retorna antes de inicializar; RPC entrega 403 local antes de sendRequestInternal | Conservar serialización, delegados, colas y transporte. Añadir decisión por variante/operación, sin poner isIsolated=false globalmente |
| tgnet/ConnectionsManager.cpp sendRequest (1968), init (3700); ConnectionSocket.cpp openConnection (477), openConnectionInternal (625) | Guardas nativas deniegan; dos capas de sockets protegidas | Conservar MTProto, criptografía, handshakes/DC y recuperación protocolaria. Habilitación futura debe ser coherente con Java y exclusiva de realAlpha |
| AccountInstance / BaseController | Controladores derivados del currentAccount final del objeto | Vincular cada flow a ese slot, sin consultar selectedAccount desde callbacks tardíos. Verificar bounds antes de acceder a arrays nativos/Java |
| UserConfig.loadConfig (305), saveConfig (150), clearConfig (475) | Restauración bloqueada por aislamiento. saveConfig usa doOnIdle/editor.apply; clearConfig borra preferencias | Preservar esquema y sandbox; impedir importaciones/limpiezas automáticas. Inspección futura debe considerar UserConfig, DB y archivos nativos, no solo currentUser |
| MessagesStorage constructor (328–335) | cache4.db/WAL/SHM usan directorio privado y subdirectorio accountN para slots distintos de 0 | Conservar DB/esquema, confirmar paths Java/JNI dentro del nuevo UID/paquete y recuperación de fallos; no reutilizar datos de Exteraless |
| LoginActivity.onAuthSuccess (1710–1747) | setUserId, clearConfig, setCurrentUser/saveConfig y cleanup/putUsers de DB son pasos separados | Conservar UI/formatos/ramas nativas; separar validación de respuesta, commit, efectos y navegación. La secuencia observada no demuestra por sí sola pérdida de datos |
| LoginActivity (3248–3250, 8573–8574), NekoXConfig.currentAppId/currentAppHash (49–57) | Se consultan getters; fuera del aislamiento pueden elegir customAppId/hash de preferencias | Pareja propia validada por gradle/telegram-api.gradle, con precedencia de una sola fuente; el parche 0003 evita el override legado en realAlpha, sin habilitarlo |
| ConnectionsManager.cancelRequest (686), cleanup (697), switchBackend (838) | Llamadas JNI directas. switchBackend nativo (2063) cambia DC/backend, limpia datacenters y puede exit(1) | No exponer estos wrappers como autorización general. Cancelar solo tokens del flow/slot, notifyServer=false al cerrar UI; nunca cleanup(true) o switchBackend como recuperación improvisada |
| SessionsActivity (357/397, 526/582/614); MessagesController.performLogout (16446) | Rutas explícitas de resetAll/reset individual y logout. Hay confirmaciones de UI y acciones sobre bots conectados | Mantener denegadas y fuera del login. En el futuro consentimiento específico y alcance visible; no deducir que estas rutas causaron el incidente reportado |
| ConnectionsManager.init (761–769), callbacks/hook de sendRequestInternal (438+) | Lee proxy/WebProxyTransport; hay intercepción ghost/plugins y callbacks de error | Primera conexión revisada no debe activar proxy, hooks, push, facturación o SDK externos por preferencias heredadas. Revisar además HTTP auxiliares y endpoints, sin habilitarlos aquí |

La limpieza **local** de claves MTProto no equivale a `auth.resetAuthorizations` ni demuestra cierre de otras sesiones. Las rutinas nativas de recuperación tienen usos protocolarios legítimos; no se eliminan indiscriminadamente.

## Hallazgos reproducidos y parches sin aplicar

| Prioridad | Evidencia / parche | Alcance exacto |
|---|---|---|
| Alta, antes de login real | 0004-redact-native-and-login-sensitive-diagnostics.patch | Tres sinks activos: LoginActivity:3188 future_auth_token (rama DEBUG_VERSION); :10437 teléfono/phone_code_hash; ConnectionsManager.cpp:2246 integrity token. Los originales exponen una canaria sintética en los fixtures; los reemplazos conservan nombres de operación/slot sin valores. No se ejecutó el flujo Android ni hubo tokens reales |
| Alta, antes de API propia | 0003-realalpha-ignore-legacy-api-preferences.patch | Getters de realAlpha toman una pareja BuildConfig válida, rechazan ID 0/6/hash inválido fuera del aislamiento y no aceptan overrides de preferencias. En modo aislado siguen devolviendo 0/"". No acredita propiedad de la pareja: eso necesita revisión del responsable |
| Media, endurecimiento de contrato | 0001-userconfig-reject-null-before-mutation.patch | Método original reproducido con null: asigna currentUser=null y después lanza NPE en user.id dejando clientUserId anterior. El parche rechaza antes de mutar y conserva las llamadas válidas. No prueba que algún caller Android haya pasado null ni explica CRASH-001 |
| Media, rama privada inactiva por defecto | 0002-no-implicit-auth-key-reset-retry.patch | Rama original CONNECTION_NOT_INITED reinicia claves/reenvía automáticamente si DEBUG_PRIVATE_VERSION=true. Fixture reproduce ese caso; parche conserva entrega normal del error. En BuildVars el flag es **false** por defecto; no se afirma que ocurriera en las APK entregadas |

Los cuatro parches se aplicaron **solo a copias temporales** en las pruebas, con git apply --check, y se probaron sus métodos/expresiones originales y corregidos. No se aplican por scripts ni a Work 2. Requieren revisión antes de integrar y compilación Android posterior. Las expresiones de logging se verificaron también fuera de comentarios; el nonce de una antigua ruta comentada no se presentó como sink activo.

Pendientes de seguridad: revisar logs de errorText y excepciones SDK (FileLog.e(Throwable) puede incluir mensajes/causas), mapeo completo de errores 2FA/signup/QR/recuperación, recuperación transaccional entre archivos nativos/DB/prefs, carga JNI y bridge de atestación de solo lectura en Android. Los tests P0.1 anteriores no certificaban todos estos sinks. No se atribuye el incidente de sesiones/bots a ningún hallazgo sin evidencia de ejecución.

## Resultados finales

Código verificado: `bf4468cccc6eba8d1efb2a14f911e96559d09d28`. **101 pruebas distintas aprobadas** en Python3.11 normal y `-O`: 202 ejecuciones finales, cero fallos y cero omisiones. Son 90 pruebas del coordinador/controlador/UI y bytecode, nueve de integración/parches/resolución API y dos de C++/política nativa. No se suman los bucles, subcasos o repeticiones preliminares como tests distintos.

Los 15 blobs de código, tests, parches y README del módulo publicados se verificaron contra los hashes Git locales; SHA-256 de cada archivo y lista de métodos en `evidence/results.json`. La primera versión del arnés tuvo un error de compilación por variable duplicada (cero tests ejecutados, un error de setUpClass); se corrigió y se conserva el log inicial. Los resultados finales anteriores corresponden a ejecuciones posteriores completas, no a ese intento fallido.

Referencias directas inmutables: [mutación nula de UserConfig](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/src/main/java/org/telegram/messenger/UserConfig.java#L274), [retry/reset privado](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java#L517), [getters API legados](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoXConfig.java#L49), [token de login](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L3188), [teléfono/hash](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L10437), [token de integridad nativo](https://github.com/Jose22Yt/FlexyGram/blob/36e27309bee4e6c27e3850321fa0c6c44e2acf42/TMessagesProj/jni/tgnet/ConnectionsManager.cpp#L2246).

## Validación y uso por Work 2

Ver evidence/ para comandos, versiones, hashes e inventario de métodos. Todo es host: JDK21 con bytecode --release 8, Python3.11 normal/-O, Groovy del Gradle fijado, CMake y C++ del host. Se compiló VariantPolicy.cpp real y se consumió su declaración en Java; se ejecutaron las cuatro entradas de guardas nativas con colas ficticias. Eso **no** ejecuta MTProto completo, JNI en Android, almacenamiento Android ni certifica minSdk24 por sí solo. No se repiten las 62 regresiones de PR #34 ni su compilación.

1. Puede revisar/cherry-pickear este módulo, tests y documentación como archivos nuevos después de estabilizar P1/P2; al no estar registrado, no cambia su APK actual. No hay que aplicar los parches con el cherry-pick.
2. Revisar e integrar separadamente los cuatro parches sobre el HEAD que esté compilando; resolver contexto sin sobrescribir sus cambios. Añadir un puerto JNI de lectura para la atestación y los adaptadores Android de almacenamiento/UI, con pruebas instrumentadas.
3. UI: conservar LoginActivity y sus métodos/páginas. Enlazar eventos tipados con su handler principal; mantener el controller durante recreación y cerrar Binding al destruir la vista. Tras muerte de proceso restaurar solo recreationMarker; nunca códigos, hashes, teléfonos ni peticiones. No repetir automáticamente login al recrear.
4. Puerto Telegram futuro: mapear owner+slot+epoch+ticket a token nativo, entregar errores seguros/una sola terminal, no reenviar tras cancelación. No implementar close como logout, reset de claves, cambio de backend o revocación. Mantener la persistencia criptográfica original y revisar el commit de cuenta antes de setCurrentUser/navegar.
El adaptador de persistencia deberá distinguir una sesión preexistente del material de handshake creado por el flujo actual mediante un journal/epoch propio. Encontrar una auth_key nueva tras inicializar MTProto no basta para clasificarla como una sesión anterior ni como una cuenta autorizada; esta correspondencia aún no está implementada.

5. Solo después: nueva política revisada y explícita, pareja API propia desde fuente privada, construcción unsigned/verificación, firma/instalación autorizadas por hash y aprobación independiente para una prueba de conexión/cuenta. No hace falta ni se solicita un API Hash, teléfono o código para revisar este PR.

No hay un cliente conectado nuevo, APK, clave ni firma en esta entrega. Production y las variantes existentes permanecen bloqueadas/intactas. No se fusiona ningún PR ni se habilita Actions.
