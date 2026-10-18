# Identidad, configuración heredada y servicios

La revisión se refiere al commit `082aff3d0fc57ce90b0154fe76d9d7c796ed45a2`. No se modificó ninguno de estos ajustes. No se publican las credenciales literales que contiene el repositorio.

## Compartir `com.exteraless.app`

Android utiliza paquete, firma y UID para aislar y actualizar aplicaciones. [La documentación de firma de Android](https://developer.android.com/studio/publish/app-signing) explica las condiciones de continuidad de firma. En esta APK se verificó una firma Android Debug; no se conoce aquí el certificado de una instalación previa del usuario.

| Situación | Consecuencia plausible | Relación con el incidente |
| --- | --- | --- |
| Mismo paquete, firma diferente no admitida por su linaje | Android normalmente rechaza la actualización; no crea una segunda app del mismo paquete en el mismo perfil | No revoca por sí mismo sesiones Telegram. No pedir desinstalar para vencer el rechazo |
| Mismo paquete y firma/linaje aceptados | Actualización conserva datos de app: preferencias, bases de datos, claves, ajustes de plugins y cuentas locales | Podría reutilizar datos anteriores; no se sabe si esta instalación fue actualización ni si tuvo datos previos |
| Instalación después de desinstalar/borrar datos | Puede perder sesiones locales, chats secretos, archivos no sincronizados, plugins y configuración; ciertos respaldos podrían restaurarse | No autorizar este procedimiento en el teléfono personal para investigar. La nube de Telegram no preserva todo |
| Restauración/clonación/OEM/perfil de trabajo | Depende del sistema y del método; podría recuperar preferencias o archivos | Solo si se copió la misma auth key y se usó paralelamente sería relevante para duplicación; no se da por hecho |
| Paquete independiente, sin importación | Nuevo sandbox; no accede por el nombre al almacenamiento privado de Exteraless/Telegram | Reduce conflictos locales; no es una garantía de que Telegram acepte credenciales heredadas |

No se encontró `sharedUserId` en el manifiesto revisado. El namespace Java `org.telegram.messenger` no es el identificador de instalación. Usar el mismo paquete no concede acceso al sandbox de Telegram oficial, ni el mismo API ID fusiona sesiones. Los archivos multimedia compartidos y permisos de almacenamiento requieren una evaluación distinta de las claves en directorios privados.

[ContactsController.checkAppAccount L392–435](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/ContactsController.java#L392) enumera cuentas Android del tipo `BuildConfig.APPLICATION_ID`, elimina entradas locales sin usuario asociado y añade cuentas activas. [res/xml/auth.xml L4](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/res/xml/auth.xml#L4) fija `com.exteraless.app`. Es integración AccountManager/contactos de Android, no `account.resetAuthorization` remoto. En una identidad futura deben concordar autenticador, sync adapters, authorities y permisos; cambiar únicamente applicationId sería insuficiente.

## Inventario de configuración heredada

| Configuración | Hallazgo | Riesgo / medida propuesta |
| --- | --- | --- |
| Telegram API | Fallback ID 6/hash fuente; selector personalizado persistente; rama de variables de entorno incompleta | Exigir propiedad/procedencia, no permitir autenticación por fallback. API Hash no es la auth key del usuario |
| Firebase | `TMessagesProj/google-services.json` declara un único cliente para `com.exteraless.app`; proyecto heredado, sin titularidad FlexyGram acreditada | Notificaciones, restricciones de paquete/certificado y gobierno de datos deben configurarse para identidad propia. No llamar contraseña de cuenta a su API key |
| OAuth, Huawei y SMS/passkeys | BuildVars contiene identificadores de servicios heredados; SafetyNet está vacío; `SUPPORTS_PASSKEYS` usa SDK>=34 y comentario de soporte para IDs oficiales | Validar registro de paquete/certificado y compatibilidad para el cliente propio; desactivar rutas no soportadas en diagnóstico si se aprueba |
| Maps/Glyph | Defaults heredados/de prueba y precedencia de propiedades/entorno | Restricciones por paquete/certificado pueden fallar sin implicar compromiso de sesiones |
| Copias de seguridad | allowBackup/restoreAnyVersion y BackupAgent explícito | Política propia para tokens y migración antes de usar cuentas; no asumir sandbox nuevo tras una reinstalación con restauración |
| Proxies | ConnectionsManager toma la configuración persistida y puede iniciar transporte proxy local | Registrar solo si estaban habilitados y su procedencia, nunca su contraseña. Cambio de red no prueba duplicación de claves |
| Billing, mapas y otros servicios | BillingController, osmdroid, controladores de proxy, LinkCleaner y M3prewarm aparecen en inicialización | Revisar necesidad, hilos y endpoints; no se verificó todo el tráfico de todas las dependencias |

## Push, Firebase y telemetría

[ApplicationLoader.initPushServices L513 y siguientes](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/ApplicationLoader.java#L513) programa trabajo después del inicio, obtiene el proveedor y solicita token. `GooglePushListenerServiceProvider` inicializa Firebase y solicita FCM con trabajo en cola y callback; [GcmPushListenerService](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/GcmPushListenerService.java) recibe actualización/mensaje.

[MessagesController.registerForPush L16514 y siguientes](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/MessagesController.java#L16514) prepara `account.registerDevice`, token de transporte y secreto push generado, además de otras cuentas locales. Registrar un dispositivo para recibir push es código esperado de un cliente. No es la RPC que termina todas las autorizaciones.

El manifiesto declara `firebase_analytics_collection_deactivated=true` (L950), colección de identificador publicitario desactivada (L953) y Crashlytics desactivado inicialmente (L999). `AndroidUtil.shouldEnableCrashlytics` exige `!BuildConfig.DEBUG` y preferencia de reportes de fallos: no hay base para afirmar que Debug subió automáticamente los secretos de los logs a Crashlytics. El manifiesto fusionado previo incluye `FirebaseInitProvider` no exportado; hay inicialización de componentes antes de `Application.onCreate`, aunque ello no prueba una subida de datos personales.

Un proyecto Firebase ajeno puede producir dependencia operativa y fallos por configuración/restricciones. El token FCM, el secreto push, el API Hash Telegram, la auth key MTProto y los tokens de bots son objetos diferentes. La ruta push comprueba autenticidad antes de `SESSION_REVOKE`; no se halló una revocación global causada simplemente por compartir proyecto Firebase. Se requiere auditoría posterior de tráfico con datos sintéticos para valorar exposición real de cada servicio.

## Respaldo y tokens

[AndroidManifest L111–113](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/AndroidManifest.xml#L111) habilita respaldo, `restoreAnyVersion` y `.BackupAgent`. [BackupAgent L11–21](https://github.com/Jose22Yt/FlexyGram/blob/082aff3d0fc57ce90b0154fe76d9d7c796ed45a2/TMessagesProj/src/main/java/org/telegram/messenger/BackupAgent.java#L11) registra explícitamente `saved_tokens` y `saved_tokens_login` mediante SharedPreferencesBackupHelper. AuthTokensHelper L111/L121 llama `dataChanged` al guardar tokens.

Esto es una inclusión explícita de material de futuro inicio de sesión en el mecanismo de respaldo. No demuestra que el respaldo se ejecutara, que alguien lo accediera ni que se restauraran todas las claves de `tgnet.dat`. No se infiere “se respaldan todas las sesiones MTProto” a partir de allowBackup. La política efectiva puede depender del transporte de backup y del OEM. Propuesta: diagnóstico sin restauración/importación de secretos y revisión separada de conservación y eliminación, antes de construirlo.

## Actualizador original

`GitHubUpdater.java` fija `exteraless/exteraless` (L47), contempla comprobaciones por intervalo/canal y descarga APK (L364 y siguientes); la instalación L433 usa intent y FileProvider. `LaunchActivity.checkAppUpdate` (L6183 y siguientes) alcanza este actualizador si no hay canal de metadatos alternativo. No se ejecutó ninguna consulta o instalación de esa ruta en esta auditoría.

No se identificó en la ruta revisada una verificación propia de hash/firma de la APK descargada antes del intent; el instalador Android conserva sus comprobaciones de firma/paquete y consentimiento. Por tanto, no es una instalación silenciosa ni se afirma que pueda saltarse la firma de nuestra APK. Sí existe riesgo de procedencia y confusión de actualizaciones para FlexyGram, especialmente si se reutilizara una firma aceptada. La propuesta futura es retirar ese destino del diagnóstico y definir un canal propio explícito, sin implementar nada ahora.

## Configuración de seguridad

El manifiesto permite tráfico HTTP (`usesCleartextTraffic=true`, L128, con comentario para el navegador) y `network_security_config.xml` permite cleartext con CA de sistema. Esto amplía la superficie de componentes HTTP; no significa que las claves Telegram viajen automáticamente sin cifrar, que todos los destinos usen HTTP ni que exista un TrustManager que acepte cualquier certificado. La revisión no certifica el código de red completo.

Debuggable/JNI Debuggable aumentan posibilidades de inspección y el coste de herramientas, especialmente en un dispositivo con depuración habilitada. No hacen los archivos privados accesibles a cualquier app Android ordinaria por sí solos. No se solicitan root, extracción de sesiones ni un bugreport completo para investigar.

## Identidad futura propuesta, pendiente de aprobación

Reservar una identidad independiente bajo control del responsable, por ejemplo `io.github.jose22yt.flexygram.diagnostic` como candidato, no como registro ya realizado. Separar la variante de diagnóstico de la futura identidad de producción. Usar firma diagnóstica propia y una política de rotación/documentación; no guardar claves de firma en Git. Mantener los créditos de origen y la dirección de @Lukhou23.

Inventariar applicationId, manifest placeholders, providers/FileProvider, permisos propios, AccountManager/sync adapters, deep links, redirect OAuth, Firebase, Maps, push, backup, directorios compartidos y actualizador. No importar ni migrar automáticamente datos de Exteraless/Telegram. Definir configuración sin fallback y autenticación bloqueada hasta disponer de credenciales propias y revisión. Un cambio de paquete aislado no corrige los logs de secretos, las dependencias ni todas las identidades de servicios.
