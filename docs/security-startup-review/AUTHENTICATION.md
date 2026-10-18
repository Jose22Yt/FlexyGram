# Autenticación y sesiones

Fuente: commit `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2`. Todas las referencias relativas a código están bajo `TMessagesProj/`. Los enlaces fijan ese commit; las líneas no describen necesariamente versiones futuras. No se publican valores de API Hash, tokens ni claves.

## Configuración efectiva y entrada al protocolo

En [build.gradle, L156–186](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/build.gradle#L156) se definen un API ID y API Hash de fallback. `local.properties` tiene precedencia sobre las variables de entorno y el fallback. Hay un defecto de configuración: las variables Telegram solo se consultan dentro de `if (properties != null)`; el `else` contempla Maps/Glyph, pero no Telegram. Una configuración de entorno aparentemente completa puede acabar usando el fallback si no existe ese objeto de propiedades.

El `BuildConfig` generado de la compilación conservada confirma `APP_ID=6`, hash igual al fallback del fuente, `DEBUG=true` y `DEBUG_TOOLS=false`. Se comparó la igualdad sin volcar el hash. [BuildVars, L45–55](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/BuildVars.java#L45) sustituye sus valores iniciales por los generados: su inicializador `APP_ID=4` no es el valor efectivo de esta compilación.

[NekoXConfig, L45–62](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/tw/nekomimi/nekogram/NekoXConfig.java#L45) puede seleccionar credenciales personalizadas guardadas en preferencias (`customApi=3`); por defecto usa BuildConfig. No se conoce esa preferencia en el teléfono ni se solicita extraerla. El valor compilado no basta para probar qué credencial utilizó una instalación restaurada o actualizada.

[LoginActivity, L3184–3253](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/ui/LoginActivity.java#L3184) prepara `auth.sendCode` con API ID/hash efectivos, teléfono y ajustes. Usa los tokens futuros guardados en `codeSettings.logout_tokens`. El inicio con código pasa por `auth.signIn` (L4996); el flujo passkey vuelve a incluir la configuración API (L8571). No se ejecutó ninguno de estos flujos.

Telegram exige credenciales propias para un cliente distribuido: [obtención de API ID](https://core.telegram.org/api/obtaining_api_id) y [condiciones API](https://core.telegram.org/api/terms). La reutilización es un riesgo confirmado de identidad/configuración; no demuestra qué regla de seguridad se activó, ni convierte automáticamente ese API ID en una clave de cuenta o bot.

## ConnectionsManager, claves y almacenamiento

| Etapa | Código y condiciones | Interpretación |
| --- | --- | --- |
| Instancia por cuenta | [ConnectionsManager.java L231–293](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/tgnet/ConnectionsManager.java#L231) | Selecciona `filesDir` o `files/accountN`, carga UserConfig y prepara idioma, fabricante/modelo, versión de app y SDK |
| Inicialización JNI | Mismo archivo L746–790 | Introduce API ID, proxy seleccionado, paquete, certificado, instalador, push, zona horaria, red y clase de rendimiento. La huella del certificado no es la clave de autorización |
| Configuración persistida | [ConnectionsManager.cpp L3697–3732](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/jni/tgnet/ConnectionsManager.cpp#L3697), carga L380 y guardado L494 | Lee configuración nativa de los directorios de esa instalación; no busca automáticamente el almacenamiento privado de Telegram oficial |
| Archivo nativo | [Config.cpp L31–91](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/jni/tgnet/Config.cpp#L31) | Lectura/escritura binaria del estado, incluyendo `tgnet.dat`; hay protección de directorio/UID de Android, no se encontró envoltura adicional de Keystore en esta ruta |
| Serialización de auth keys | [Datacenter.cpp L537–587](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/jni/tgnet/Datacenter.cpp#L537) | Guarda claves permanentes/temporales y sus identificadores; su conservación tras actualización/restauración es relevante |
| Creación y asociación | `jni/tgnet/Handshake.cpp` (DH, entre otras operaciones L754); `Datacenter.cpp` L1414 y siguientes | Handshake y asociación a datacenter. Se revisó la ruta; no se certifica toda la implementación criptográfica |
| Migración entre datacenters | `Datacenter.cpp` L1442–1453 | `auth.exportAuthorization` seguido de `auth.importAuthorization` para datacenters de la misma cuenta; es código normal, no importación de otra app |
| Metadatos de conexión | `ConnectionsManager.cpp` L3186–3240 | `initConnection` incluye API ID, modelo/sistema/idioma y parámetros de paquete/certificado/instalador. Son metadatos enviados a Telegram; no prueba de exfiltración a un tercero |

No confundir las sesiones MTProto de transporte (incluido `TL_destroy_session` en `ConnectionsManager.cpp` L2743) con autorizaciones de dispositivos. Reutilizar API ID/hash no reutiliza por sí solo las auth keys. Copiar/restaurar la misma clave privada sí puede ser relevante, pero no se observó que hubiera ocurrido.

## Mapa de terminación de autorizaciones

Se buscaron construcciones y referencias en Java, C++ y el árbol Python. Las declaraciones TL no se contabilizan como ejecuciones. Los controles de interfaz son condiciones de los call sites ordinarios; no constituyen una barrera contra un plugin con capacidades suficientes o un proceso comprometido.

| Operación | Ubicación exacta | Quién la alcanza y condición |
| --- | --- | --- |
| `auth.resetAuthorizations` | [SessionsActivity.java L357 y L397](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/ui/SessionsActivity.java#L321) | Selección de terminar otras sesiones y confirmación positiva del diálogo. Dos rutas de esa pantalla; no llamadas desde ApplicationLoader/LaunchActivity de arranque |
| `account.resetAuthorization` | `SessionsActivity.java` L526 | Confirmación positiva del diálogo de una autorización seleccionada, enviando su hash |
| `account.resetAuthorization` | `SessionsActivity.java` L582 | `UndoView.hide`: solo con `!apply` y objeto de autorización presente. Es una ruta de la pantalla/estado de deshacer; no interpretar el nombre del argumento como prueba de una acción ocurrida |
| `account.resetAuthorization` | `SessionsActivity.java` L614 | Callback `onSessionTerminated`; [SessionBottomSheet.java L249–260](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/ui/SessionBottomSheet.java#L249) solo lo llama tras pulsar y confirmar Terminate |
| `account.resetAuthorization` | [UnconfirmedAuthController.java L381–400](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/UnconfirmedAuthController.java#L381) | `UnconfirmedAuth.deny`, autorización no bot; `updateList(false)` L230 y `deny` L285. [UnconfirmedAuthHintCell L180](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/ui/Cells/UnconfirmedAuthHintCell.java#L180): botón No. Para bot utiliza `updateConnectedBot` con deleted |
| `auth.logOut` | [MessagesController.java L16445–16480](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java#L16445) | Única construcción localizada, dentro de `performLogout(type==1)`. `type==0/2` limpian estado sin enviar esa RPC. No equivale a terminar todas las demás autorizaciones |

Los disparadores revisados de `performLogout` incluyen LogoutActivity (L193, usuario), `PasscodeHelper` (L29, coincidencia con contraseña de pánico configurada y cuentas permitidas), PushListenerController (L277, push descifrado `SESSION_REVOKE`), ConnectionsManager Java (L949–957, delegado nativo) y varias rutas locales de UI/estado. El código de pánico puede cerrar varias cuentas de esta app, no todas las autorizaciones de sus otros dispositivos. No se probó que el usuario lo activara.

La expiración de avisos de autorización no confirmada, `UnconfirmedAuthController` L121–130, **elimina avisos de la caché**, no llama a `deny` ni revoca automáticamente. Quitar un bot conectado o bloquearlo tampoco equivale a invalidar su token Bot API o congelarlo en Telegram.

Las reglas actuales de [auth.resetAuthorizations](https://core.telegram.org/method/auth.resetAuthorizations) y [account.resetAuthorization](https://core.telegram.org/method/account.resetAuthorization) incluyen restricciones para autorizaciones recientes. Su presencia exige considerar la antigüedad de la sesión al evaluar una hipótesis; no se prueba ni se elude esa restricción. [auth.logOut](https://core.telegram.org/method/auth.logOut) termina la autorización desde la que se usa, no es la operación global anterior.

## Errores y revocaciones recibidas

En [ConnectionsManager.cpp L1511–1542](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/jni/tgnet/ConnectionsManager.cpp#L1511), un 401 distinto de `SESSION_PASSWORD_NEEDED`, en el datacenter principal/en migración y con conexión genérica/cuenta activa, lleva a `delegate->onLogout` y limpieza local. Otros datacenters pueden volver a autorizarse. La rama 406 con `currentUserId==0` y texto `AUTH_KEY_DUPLICATED` limpia la clave de ese datacenter. Java publica el cierre local en UI y hace `performLogout(0)` si corresponde. Son reacciones a un error recibido; no prueba de que el cliente haya ordenado revocar otros dispositivos.

Telegram documenta [AUTH_KEY_DUPLICATED](https://core.telegram.org/api/errors) cuando una misma clave se usa para sesiones principales paralelas en conexiones no multimedia; puede suceder con IP iguales o diferentes, con excepciones documentadas de configuración. El servidor invalida la clave. No equivale a compartir API ID, a usar dos clientes con claves independientes ni, necesariamente, a cambiar de IP. No existe registro de ese error en este incidente.

Un push `SESSION_REVOKE` pasa por comparación de key ID, descifrado AES-IGE y comprobación del message key (`PushListenerController` L127–155) antes del dispatch de L273. FCM transporta el mensaje: su token no es una auth key MTProto. No se encontró una ruta que acepte ese comando como texto libre por tener el mismo paquete Firebase. Esto tampoco certifica todos los componentes push ni elimina el riesgo de una clave push expuesta.

## Hallazgos de secretos

1. **Confirmado, prioridad P0:** [AuthTokensHelper L83–86](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/AuthTokensHelper.java#L83) concatena `future_auth_token` en un log cuando `DEBUG_VERSION` es verdadero. La representación UTF-8 puede ser parcial o perder bytes, pero sigue siendo información sensible. El camino se alcanza al guardar una autorización exitosa desde LoginActivity L1733. No está protegido por `DEBUG_PRIVATE_VERSION`.
2. **Confirmado, prioridad P0:** [PushListenerController L137 y L152](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/PushListenerController.java#L127) imprime `SharedConfig.pushAuthKey` completa en hexadecimal al fallar comprobaciones de descifrado, condicionado por `LOGS_ENABLED`. Puede importar también en variantes no depurables con logs activados.
3. También se encontraron registros de token FCM (`GcmPushListenerService` L40), CAPTCHA (`CaptchaController` L77) y token de acceso al servidor local de desarrollo (`src/main/python/dev_server.py` L48–56). Son secretos de distintos dominios; no llamarlos todos “API Hash” o “token de bot”.
4. [FileLog L605–632](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/FileLog.java#L605) envía mensajes a Logcat y, cuando existe writer, a archivo. `LOGS_ENABLED` se activa por defecto en Debug cuando se inicializa BuildVars con contexto. Los volcamientos RPC completos sí tienen una guarda adicional `DEBUG_PRIVATE_VERSION` (FileLog L127), falsa en esta base; no se afirma que todos estén habilitados. El redactor de objetos no elimina secretos ya concatenados en cadenas.

Telegram explica que un [future auth token](https://core.telegram.org/api/auth) válido puede permitir volver a entrar sin código, o requerir la contraseña 2FA si existe. Su persistencia para ese flujo es legítima; imprimirlo o respaldarlo sin una política propia requiere revisión. `saved_tokens_login` y `saved_tokens` son preferencias privadas serializadas en hexadecimal, no cifrado adicional de aplicación demostrado en este helper. El agente de respaldo se describe en CONFIGURATION.md.

**No se accedió a logs personales ni se encontró una filtración consumada.** Que un sink pueda recibir secretos no prueba que una tercera persona los leyera, que se enviaran a un servidor externo ni que ocasionaran los efectos reportados. No se debe solicitar un Logcat completo de esta APK autenticada para investigar este hallazgo.
