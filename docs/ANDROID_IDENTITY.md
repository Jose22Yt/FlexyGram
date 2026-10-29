# Identidad Android y coexistencia

| Elemento | Alpha | Beta prevista |
| --- | --- | --- |
| applicationId | io.github.jose22yt.flexygram.alpha | com.flexygram.messenger |
| Variante | connectedAlpha | beta |
| Nombre | FlexyGram Alpha | FlexyGram |
| Versión prevista | Alpha 1286 | 1.0.0-beta.1 / 1287 |
| Namespace de clases y R | org.telegram.messenger | org.telegram.messenger |
| Firma | Identidad Alpha existente | Certificado oficial registrado; PKCS12 bajo control del propietario |

`APP_PACKAGE` define la identidad Beta. Android Components fija explícitamente el applicationId Alpha y el Beta por variante. Los overrides de versión solo afectan a Beta. El namespace, JNI, clases, claves internas y formatos de preferencias no se renombran.

Los XML de autenticación, sincronización, MIME de contactos y shortcuts usan el paquete Beta en main y una copia Alpha en su overlay. Beta mantiene su overlay equivalente para que ambas identidades sean comprobables. Los providers y task affinities usan `${applicationId}`; las rutas de FileProvider y FlexyStudio siguen siendo relativas al sandbox. ContactsController, URI de compartir, servicios y accesos dinámicos obtienen la identidad en ejecución mediante BuildConfig o Context.

Las acciones técnicas y categorías heredadas, como `app.exteraless.action.*` y `org.telegram.messenger.SHORTCUT_SHARE`, conservan sus nombres porque sus productores y consumidores deben coincidir. Los intents explícitos y providers separan las aplicaciones. Los enlaces `tg:`, `t.me`, Telegram, TON y Wear mantienen su significado; Android puede pedir elegir una app si Alpha y Beta declaran el mismo enlace. No se inventa verificación de dominios ni asociación de App Links.

El flag histórico `CONNECTED_ALPHA` permanece verdadero también en Beta: actualmente protege la interfaz Signature, la política de registros privados, la desactivación del actualizador heredado y otras rutas de compatibilidad. No describe el canal de publicación. Cambiarlo rompería funciones existentes; esta misión no hace ese refactor. Los nombres técnicos y credenciales `ALPHA_*` usados solo por Alpha quedan aislados. Beta sobreescribe el cliente OAuth opcional con una entrada propia.

## Datos e instalación

Beta se instala como otra aplicación. No actualiza ni reemplaza Alpha. Sus sesiones, bases de datos, cachés, descargas privadas, claves de cifrado, preferencias, contactos de cuenta Android y tokens de notificaciones están aislados. Es necesario iniciar sesión nuevamente; los chats de nube volverán a sincronizarse tras autenticar. Los chats secretos, archivos solo locales y ajustes no se transfieren automáticamente. No se implementa lectura del sandbox de Alpha ni copia de sesiones o claves.

Alpha puede mantenerse instalada. El usuario debe revisar qué app atiende enlaces y contactos para evitar confusión o duplicados. Un archivo exportado voluntariamente solo puede importarse mediante las funciones que ya admita el cliente; no es una migración general de datos.

Las siguientes actualizaciones Beta deberán conservar **el mismo paquete y certificado**, con versionCode creciente. Perder la clave impide actualizar esa identidad de forma ordinaria. No se puede usar una firma temporal o el certificado Alpha como sustituto.

## Servicios y pendientes

Firebase/FCM, OAuth, Maps y servicios sujetos a paquete/certificado deben registrarse o actualizarse por el propietario. No se crearon proyectos, credenciales ni huellas ficticias. Passkeys y el actualizador heredado siguen con la política de seguridad de la base; no se anuncia un canal Beta automático. La distribución Beta seguirá siendo privada hasta autorización expresa.

La revisión de fuentes no prueba el manifiesto combinado, la instalación, login, notificaciones ni coexistencia real; esas verificaciones requieren la futura compilación autorizada y un teléfono ARM64.
