# P0.3b — Firebase y servicios push independientes

FlexyGram 1.0, creado y dirigido por @Lukhou23. Créditos originales conservados.

## Integración y estado

PR #6 aprobado en `20dbf92e430cc816fd41ebe021ff4a5223897650`, integrado exclusivamente en develop: **`3f95ed2826c5316e11b0380a0f731b21505033c0`**. Árbol de base verificado: `6c40f1fdbbfdd9006f2a370632709a08bb84749b`. Rama `security/paso-3-p03b-firebase-push`, destinada a revisión, sin fusión automática.

**Sigue siendo exclusivamente Diagnostic:** sin INTERNET, autenticación, proveedores push activos ni publicación de APK. Se mantienen P0.1, P0.2 y P0.3a. La validación Android real/16 KB y [el bloqueo de beta](../security-p03a/VALIDACION-ANDROID-PENDIENTE.md) siguen pendientes. No se reintentó iniciar un emulador inexistente.

## Inventario de configuración y servicios heredados

| Elemento | Hallazgo | Corrección / estado |
|---|---|---|
| google-services.json | Proyecto `exteraless`, project number/sender ID `335004274031`, paquete `com.exteraless.app`, Firebase app ID `1:335004274031:android:e06325b96c4b17732eac9a`, bucket `exteraless.firebasestorage.app`; una clave cliente API, sin OAuth client. | Eliminar del árbol vigente e ignorar copias. No se reproduce la clave. La eliminación no revoca credenciales ni borra el historial Git. |
| Google Services | Plugin no aplicado desde P0.2; no hay evidencia de que la mera presencia del JSON lo activara. | Sin aplicar. No se auto-descubren recursos/configuraciones heredadas. |
| FCM 25.1.2 | initializeApp(context) y default FirebaseApp sin validación de proyecto propia. | Opciones explícitas y comprobación de proyecto/app ID/sender/API key del default antes de pedir o aceptar tokens. Una instancia ajena se rechaza, no se borra ni reconfigura. |
| Crashlytics 20.1.0 | Llamadas desde arranque y opción de ajustes. | Guarda independiente siempre false. Autorizar FCM no autoriza telemetría. No se cambia presentación/navegación del ajuste. |
| Firebase/FCM IPC | FirebaseInitProvider, FirebaseMessagingService, InstanceIdReceiver, ComponentDiscoveryService y transport scheduling retirados/deshabilitados por P0.2. | Mantener restricciones. FCM, Analytics y Crashlytics auto-init/collection false. |
| UnifiedPush Connector 3.3.4 | Primer distribuidor instalado elegido automáticamente; gateway heredado `https://p2p.belloworld.it/`; override por preferencias. | Sin elección automática ni gateway por defecto. Solo distribuidor/gateway de configuración privada aprobada, con coincidencia de distribuidor guardado en callbacks. |
| Logs UnifiedPush | Endpoints completos, Throwable, mensajes de error y reason podían revelar datos. | Eventos fijos y clase de error; no endpoints, payload, claves ni razón arbitraria. |
| SharedConfig | pushString2/pushAuthKey y metadatos en preferencias privadas. | Lectura solo si scope propio coincide. Sin configuración no cargar/escribir esos campos; no eliminar datos por falta de configuración. |
| nkmrcfg / WebPush | Token simple y claves privada/pública/auth, además del estado de distribuidor. | Material marcado con FlexyGramPushScope; no cargar claves sin procedencia del scope propio. Backup/importación P0.3a sigue sin permitirlos. |
| Register/unregisterDevice | Rutas directas y colas en PushListenerController/MessagesController. | Guardas antes de procesamiento, persistencia o transporte, incluidas llamadas directas. Sin solicitudes Telegram en pruebas. |
| Fallback local | ApplicationLoader podía iniciar NotificationsService/alarma cuando faltaba proveedor. | Sin configuración aprobada no se inicia. Servicio sigue deshabilitado en diagnóstico. |
| Huawei | Constante heredada sin proveedor propio aprobado. | Denegado; no usa fallback ajeno. |

No hay evidencia nueva que atribuya el incidente original a la APK. La presencia de estas rutas no demuestra ejecución. Los identificadores públicos anteriores no son autorización para utilizar esos proyectos.

## Configuración privada y protección ante ausencia

`PushServicesPolicy` exige identidad propia, scope, proveedor autorizado y ausencia de aislamiento. Los campos generados del diagnóstico son dos booleanos false y ocho strings vacíos. Ni preferencias ni un archivo privado pueden habilitar servicios en esta variante.

`gradle/push-services.gradle` prepara la resolución de una variante futura, sin crearla. Entrada única `FLEXYGRAM_PUSH_CONFIG_FILE`, con precedencia de local.properties sobre entorno; no combina fuentes. Sin archivo: ambos proveedores desactivados. Ruta suministrada en diagnóstico: error genérico **antes de abrirla**. Se rechazan archivos ausentes/grandes, JSON malformado, campos desconocidos/service accounts, paquete ajeno/diagnóstico, ownerApproved ausente/false, proyecto no flexygram-*, sender/app ID incoherentes, clave cliente mal formada y gateway sin HTTPS o con userinfo/query/fragment/puerto no aprobado o fallback heredado.

Ejemplos intencionalmente incompletos: [Firebase](../../config/flexygram-firebase.example.json), [UnifiedPush](../../config/flexygram-unifiedpush.example.json). Copiar fuera del repo como flexygram-push.private.json, completar únicamente servicios aprobados y usar su ruta cuando una variante autenticable tenga revisión independiente. Una configuración combinada requiere ambos bloques completos. No marcar ownerApproved sin autorización verificable.

La validación de esquema y ownerApproved no prueban propiedad IAM ni permiso para operar un gateway. Eso requiere comprobar consola del responsable, paquete/firma/restricciones API y consentimiento del distribuidor. No se hizo aquí. Firebase app ID no es applicationId Android. El hash de scope separa configuraciones; no es cifrado, firma ni prueba de propiedad.

Nunca introducir service accounts/FCM HTTP v1 credentials en el APK. Las claves cliente Firebase tampoco se incorporan al diagnóstico. La futura habilitación requiere revisar manifiesto/registrars y no puede obtenerse con un cambio de preferencia o archivo privado solamente.

## Resultados observados y reinicio del entorno

Antes del reinicio del entorno de Work se ejecutaron realmente:

- **26 pruebas aprobadas, 0 fallidas, 0 omitidas**, incluidas las 22 regresiones anteriores y 4 pruebas nuevas de configuración/policy/callbacks/artefactos. Sin cuentas ni servicios reales.
- Gradle ARM64 completo incremental con JNI/Chaquopy, sin NATIVE_TARGET=SKIP: **BUILD SUCCESSFUL 3m49s**, 244 tareas (15 ejecutadas/229 al día). Segunda construcción de las fuentes finales: **BUILD SUCCESSFUL 1m25s**, 244 tareas (7 ejecutadas/237 al día).
- Manifiesto fusionado y binario: **dos permisos**, INTERNET ausente, **89 componentes**, solo launcher habilitado/exportado; FCM/Analytics/Crashlytics flags false. Diez campos de configuración push false/vacíos.
- APK interno SHA256 `acb96b3ac2a58e6e35eb1703ce7978d45de5d5c45bb3867b62ae7860d60bc82f`: 14 847 entradas ZIP/IMY, 7 archivos anidados; cero coincidencias de la clave Firebase retirada/canarios, sin google-services.json embebido y logs dirigidos sin valores sensibles. No se instaló ni distribuyó.

**El entorno temporal se reinició después de estas comprobaciones.** Se perdieron el SDK/NDK/cachés, APK y logs completos locales antes de publicar los cambios. El blob exacto de MessagesController ya se había conservado en GitHub (`f2eadba5c5b412c0d375e1a226748b09df7f86ee`); los demás cambios y pruebas se reconstruyeron aplicando las transformaciones documentadas a la base de integración. No se presentan logs reconstruidos como originales. [Resumen observado](evidence/observed-before-reset.json) indica su procedencia y limitaciones.

Tras la recuperación se volvieron a ejecutar **tres pruebas focalizadas** sobre la policy/callbacks de producción con dobles, manifiesto fuente/guardas y scanner sintético. [Log real conservado](evidence/recovery-checks.log). No hay caché Groovy/Android para repetir aquí la suite completa o la compilación. **Antes de fusionar este PR debe volver a compilarse su commit publicado y ejecutarse la suite completa en un entorno aprovisionado**, además del bloqueo Android/beta independiente. No se afirma correspondencia binaria recertificada entre el APK perdido y el commit recuperado.

## Dos hallazgos que impiden declarar el APK libre de claves cliente

El scanner genérico detectó dos claves cliente heredadas en traducción: `tw.nekomimi.nekogram.translate.source.GoogleTranslator.translate` y `app.nekogram.translator.GoogleAppTranslator.translateImpl`. Se identificaron referencias const-string de DEX; no se publican valores ni se verifica su validez en servidores.

No pertenecen a Firebase/push ni se introdujeron en P0.3b. **La comprobación global de ausencia de claves cliente NO pasa**, aunque los controles dirigidos de Firebase/canarios/logs sí pasan. El informe mantiene este resultado como fallido. No se eliminan o parchean traductores/submódulos indiscriminadamente. El hallazgo debe resolverse con servicios autorizados antes de beta autenticable, mediante revisión separada.

## Riesgos y límites pendientes

- No hay ejecución Android, captura real de tráfico, restauración de framework/OEM ni certificación 16 KB.
- La futura configuración propia y flujo FCM/UnifiedPush real no se han validado. Se deben probar scope/cachés SDK, rotación, restore con fixtures y consentimiento.
- Tokens y claves WebPush usan sandbox privado y exclusiones de backup; no equivale a cifrado Keystore ni resistencia a root.
- Retirar un archivo no revoca claves de Exteraless ni elimina su historial. No se opera sobre servicios ajenos.
- Scanner dirigido no certifica ausencia universal de secretos; los dos hallazgos de traductores permanecen.
- No se cambia actualizador, animaciones, diseño ni rendimiento. Main intacta, PR #2 abierto, Actions sin habilitar, sin APK/Release. Detenerse para revisión del PR.

Fuentes primarias: [Firebase FCM/auto-init](https://firebase.google.com/docs/cloud-messaging/android/get-started), [opciones Firebase explícitas](https://firebase.google.com/docs/projects/multiprojects), [required Firebase options](https://github.com/firebase/firebase-android-sdk/blob/main/firebase-installations/REQUIRED_FIREBASE_OPTIONS_ANDROID.md), [UnifiedPush Connector](https://unifiedpush.org/kdoc/connector/).
