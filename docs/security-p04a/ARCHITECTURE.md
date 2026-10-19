# Arquitectura propuesta — sin activación

## Dos identidades, capacidades explícitas

Usar una dimensión de flavors `environment`: `diagnostic` y una futura `production`; conservar buildTypes debug/staging/release para depuración/optimización. **Release no significa autenticable**, y producción tampoco concede push, traducción o plugins por defecto. No crear una matriz de variantes innecesaria: habilitar solo combinaciones revisadas; variante desconocida o configuración inválida falla cerrada.

| Propiedad | Diagnostic | Futura producción (propuesta no implementada) |
|---|---|---|
| applicationId | `io.github.jose22yt.flexygram.diagnostic` | `io.github.jose22yt.flexygram.app`, sujeto a aprobación del responsable y comprobación de disponibilidad |
| Etiqueta/recursos | FlexyGram Diagnostic, recursos propios identificables | FlexyGram, icono adaptativo/monocromo/round/splash/aliases propios revisados |
| Telegram API | ID=0, hash vacío, autenticación y transporte bloqueados Java/JNI | Par propio válido obligatorio para compilar variante operativa; ausencia/par parcial/ajeno rechaza build; cuenta de laboratorio solo tras autorización posterior |
| Red | Sin permiso INTERNET; sockets/transporte bloqueados | Permiso y transportes necesarios solo tras revisión; no heredar permisos sensibles/exportados en bloque |
| Traducción | Política y fachada diagnóstica deniegan todas las entradas | Política por proveedor autorizado y adaptadores reales revisados; proveedor no disponible informa error explícito sin fallback heredado |
| Push | Sin proveedores, callbacks, registro ni reutilización de tokens | Opcional, desactivado por defecto; autorización y configuración independientes de autenticación |
| Firma | Clave de laboratorio diagnóstica propia | Clave estable de distribución propia; nunca fallback al debug diagnóstico |
| Datos | Sandbox/accountType propios; ninguna sesión | Sandbox/accountType distintos de Diagnostic, Exteraless y Telegram oficial; sin migración automática de sesiones |
| Copias | Sin backup/restauración de credenciales | Mismo mínimo seguro; exportación de ajustes permitidos por allowlist, nunca auth keys/tokens |

La identidad propuesta no se ha registrado en tienda ni implica que se controle un dominio. Confirmarla con @Lukhou23 antes de emitir una firma o artefacto autenticable. No cambiar namespace/paquetes fuente para lograr aislamiento Android.

## Separar sin debilitar P0 anteriores

Conservar en código común P0.1 (redacción de secretos), P0.3a (descarte de restauraciones, allowlist de ajustes), comprobaciones de autorización, scope de tokens y fallos cerrados. Separar únicamente las denegaciones exclusivas de diagnóstico:

1. Definición de capacidades inmutable generada desde Gradle por variante, sin flags en preferencias, intents, plugins o archivo descargable. Coherencia Java/JNI mediante pruebas y entradas de build; distintos intermediarios CMake evitan reutilizar objetos diagnósticos en producción o viceversa.
2. Manifiesto común mínimo y overlays revisados por flavor. Diagnostic conserva todas las eliminaciones de permisos/componentes y el launcher necesario. Producción solo declara componentes y permisos justificados, con guardas en los métodos también. No usar matchingFallbacks que seleccionen un módulo diagnóstico como implementación productiva ni recuperar componentes por un overlay incompleto.
3. Extraer contratos mínimos de traducción a API compartida, manteniendo firmas/catalogues/conversiones y compatibilidad de Translator, HTMLKeeper y TLRPC. Selección mutuamente exclusiva de implementaciones; `diagnosticImplementation` para la fachada actual y futura implementación productiva fuente autorizada. Ningún duplicado de clases `app.nekogram.translator`, módulo de laboratorio, constructor de inyección de pruebas ni AAR heredado en producción. Microsoft/DeepL conservan sus contratos y requieren transporte/autorización reales revisados; no presentarlos como operativos por compilar una fachada.
4. Inventariar todos los checks DiagnosticPolicy/BuildConfig y el literal nativo, denegaciones locales Google, policy universal de traducción, comprobaciones de grafo/preBuild y plugins/Python/dev-server. Clasificar qué permanece común y qué requiere implementación por flavor, con pruebas positivas de transporte falso autorizado y negativas de bypass. No hacer un cambio global true→false ni abrir plugins/servicios heredados al habilitar autenticación.
5. Un build productivo incompleto debe rechazarse o permanecer deshabilitado como variante; no producir una APK aparentemente autenticable que conserve silenciosamente sockets o adaptadores permanentemente denegados.

## Credenciales privadas y firma

El responsable obtendrá **su propia aplicación Telegram** mediante el procedimiento oficial en my.telegram.org, aceptando las condiciones de Telegram. Se hace fuera de esta sesión y de pruebas: no se solicitan contraseñas, códigos, API Hash o sesiones por chat/issues/PR. Registrar solo responsable, finalidad y confirmación de autorización, sin valores. [Procedimiento oficial](https://core.telegram.org/api/obtaining_api_id).

Mantener API ID/API Hash fuera de Git mediante archivo privado fuera del checkout o inyección de entorno segura, una sola fuente/par completo, permisos de archivo restringidos y mensajes de error sin valores. El API ID es un identificador de cliente; el API Hash es una credencial cliente que debe tratarse confidencialmente. Si se incluye en una APK puede extraerse: guardar fuera del repositorio evita su exposición en Git, **no la convierte en secreto inextraíble del cliente**. Nunca poner claves administrativas, cuentas de servicio o credenciales servidor dentro del APK. Ofuscación no sustituye autorización. Revisar escáner: rechazar claves heredadas y secretos servidor, permitir únicamente los identificadores cliente propios previstos con comprobación de procedencia sin imprimir valores.

Crear clave de firma Android estable del proyecto, bajo custodia de @Lukhou23, fuera de Git/workspace/logs. Documentar certificado público SHA-256, alias no sensible, responsable, canal de distribución y recuperación; custodiar copias cifradas separadas y acceso mínimo. La clave privada/contraseñas no son documentación pública. Para Play distinguir clave de firma de app y upload key; para sideload conservar continuidad de certificado. No reutilizar clave de Exteraless, Telegram ni diagnóstico, ni firmar producción con debug si falta configuración: abortar. Definir versionCode monotónico por canal; el literal actual 1261 y APP_VERSION_CODE=7175 son dos fuentes que deben unificarse antes de publicar. [Firma oficial Android](https://developer.android.com/studio/publish/app-signing).

## Datos, servicios y atribuciones

IDs diferentes generan sandboxes diferentes, pero no garantizan por sí solos separación de rutas externas, providers o AccountManager. Generar autoridades/accountType y namespaces de tokens desde applicationId; sin sharedUserId, importación automática de sesiones ni búsqueda de directorios Exteraless. Nunca cambiar o borrar datos de otra app. Copias cloud y device-to-device excluyen credenciales; restauración framework/OEM se prueba con fixtures, conservando SettingsBackupPolicy y formato de ajustes aprobado. Una futura política ampliable no debe habilitar copias de claves por defecto. Keystore Android puede proteger material local, pero no resuelve copias o migraciones por sí solo.

FCM futuro: proyecto Firebase controlado por FlexyGram, aplicación Android con ID/certificado correctos, recursos privados por variante, inicializadores revisados antes de obtener token; crash reporting requiere autorización aparte. UnifiedPush futuro: distribuidor y gateway expresamente autorizados, nunca fallback automático. Scope incluye identidad/configuración; al cambiar, invalidar uso del token almacenado antes de callbacks/registro. Sin configuración, ambos apagados y sin solicitudes de token. No se contacta ningún servicio aquí.

Traducción productiva: preferir API oficial de Telegram cuando el contrato y las condiciones lo permitan, y un servicio oficial mediante backend propio como alternativa de cobertura, tras revisión de privacidad/cuotas. La primera queda ligada a una sesión autorizada, disponibilidad/límites del servidor y derechos sobre textos; el segundo conserva mejor un contrato multilenguaje general, pero implica coste, operación y envío de texto al proveedor/backend. Traducción local opcional reduce envío externo, con límites de idiomas/modelos/licencias/tamaño y posible pérdida de HTML/formato. Ninguna está implementada; elegir tras pruebas sintéticas de HTMLKeeper, cancelación, errores, TLRPC, límites y consentimiento. No restaurar las claves Google retiradas, identidades ajenas o fallbacks silenciosos para completar funciones.

Mantener LICENSE y avisos originales y preparar relación componente→licencia→versión→fuente→obligaciones de redistribución, incluido código fuente correspondiente cuando proceda. Créditos de los autores originales y dirección de FlexyGram por @Lukhou23 deben coexistir. Recursos propios no autorizan borrar autoría ni cambiar licencias de terceros.
