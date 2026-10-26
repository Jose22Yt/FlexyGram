# Actualizador: auditoría y preparación desactivada

Base: Alpha1274 `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. No se activa, reemplaza ni modifica el actualizador de producción ni la entrega privada.

## Problemas demostrados en GitHubUpdater

| Método | Evidencia de código | Impacto |
| --- | --- | --- |
| REPO/API/RELEASES_URL | `app/exteraless/updater/GitHubUpdater.java:REPO` apunta a exteraless/exteraless | Fuente ajena al futuro canal oficial de FlexyGram |
| check/fetch/download | Las tres entradas tienen gate CONNECTED_ALPHA antes de consultar/descargar | Protección vigente conservada. No afirmar que el código heredado está activo en la Alpha |
| latest | `prerelease` permite o excluye prereleases; no separa Alpha de Beta | No sirve como política de canales de FlexyGram |
| pickAsset | Selección por nombre/ABI, con fallback universal/any | No demuestra paquete, arquitectura real, procedencia ni compatibilidad |
| compareVersion/isNewer | Compara tres números de etiqueta; después commits/fecha | No usa como guardia el versionCode realmente firmado del APK; puede ofrecer un archivo antiguo/incompatible |
| client/getJson/download | OkHttp permite redirecciones por defecto; la URL del asset no tiene allowlist propia | HTTPS inicial no basta para autorizar cualquier destino o URL recibida |
| download → install | Tras copiar bytes llama al instalador; no hay comprobación propia de SHA256, certificado, paquete o versionCode | Android conserva sus controles de instalación, pero esta ruta no valida previamente la oferta como actualización oficial |

No se diagnostica una vulnerabilidad explotada ni se afirma una descarga real desde upstream en Connected Alpha. Son límites verificables del código que impedirían reutilizarlo sin revisión para Beta.

## Implementación preparada

`tools/connected_alpha/prebeta/staged/FlexyUpdatePolicy.java` es una política Java compilable y probada, **fuera del árbol de aplicación y sin llamadas desde producción**. `runtimeEnabled()` siempre devuelve false. No contiene red, instalador, scheduler, preferencias ni observadores.

Valida repositorio exacto `Jose22Yt/FlexyGram`; canal elegido explícitamente; tags versionados Alpha/Beta/estable; coherencia draft/prerelease; nombre del asset; HEAD de40hex; tamaño positivo con límite512MiB; SHA256; URL HTTPS canónica sin credenciales, puerto, query, fragmento o rutas codificadas; paquete compatible; versionCode estrictamente superior al instalado y en el rango admitido. No acepta una etiqueta bonita como prueba de versión.

Por defecto conserva el paquete Alpha `io.github.jose22yt.flexygram.alpha` y el certificado autorizado `c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c`. Las tres pistas son canales de selección separados, no nuevos applicationId. Antes de Beta debe decidirse si se conservará esa identidad instalable; un paquete nuevo no puede considerarse actualización con sesiones conservadas sin una migración distinta y probada. La rotación de certificados no está habilitada.

`verifyDownloaded` comprueba bytes/tamaño/SHA antes de aceptar evidencia del archivo verificado. El contrato de `ArchiveVerifier` exige verificación criptográfica real de la firma APKV2 y extracción fiable de package/versionCode/signers. Un campo `verified=true` de JSON descargado **no es evidencia**. `validateArchive` exige exactamente el certificado actual autorizado y los metadatos esperados; rechaza firmas múltiples/desconocidas. Las pruebas de política usan evidencia sintética explícitamente identificada. Otra prueba usa AAPT2, keytool y apksigner reales para comprobar V2 de un APK mínimo efímero firmado con un certificado de prueba, rechazarlo como certificado oficial y detectar manipulación. No es una compilación de FlexyGram ni usa su clave.

## Bloqueos de activación

Faltan el adaptador Android criptográfico auditado, autenticación de metadatos de publicación, descarga/cancelación, límites de red, inmutabilidad de bytes y conexión al instalador del sistema. No basta con `getPackageArchiveInfo()` como sustituto no demostrado de una verificación criptográfica. En Android habrá que usar una implementación verificada compatible o una ruta de PackageInstaller cuya garantía se haya comprobado; no trasladar una herramienta de escritorio como si existiera en el dispositivo.

La descarga futura debe rechazar redirecciones automáticas y validar cada salto/destino de assets; un dominio CDN genérico permitido no acredita por sí solo el repositorio de origen. Los metadatos deben estar vinculados al release/HEAD y a hashes publicados por una fuente autorizada; un SHA en el mismo JSON no autentica al autor. Mantener bytes en almacenamiento privado, verificar desde el mismo contenido inmutable que se entrega a PackageInstaller y revalidar antes del consentimiento de instalación evita TOCTOU. Limitar almacenamiento/tiempo, cerrar streams y borrar fallos/cancelaciones. No bajar a HTTP ni recurrir a otro repositorio si la fuente oficial falla.

Esta política es una pieza preparada, **no un actualizador de producción completo**. El gate Connected Alpha y la entrega privada permanecen exactamente como en Alpha1274. Alpha, Beta y estable necesitarán publicaciones verificables y selección explícita; no habrá upgrades cruzados silenciosos ni downgrade para volver de canal. Una instalación que ya tenga versionCode mayor no debe ofrecerse como destino de otra menor.

Referencia primaria: [Android apksigner](https://developer.android.com/tools/apksigner), [firma y compatibilidad de actualización](https://developer.android.com/studio/publish/app-signing). No se genera ni distribuye una APK del cliente en esta misión.

## Otras rutas y publicación heredada

`LaunchActivity.checkAppUpdate` deriva a GitHubUpdater cuando `BaseRemoteHelper.hasMetadataChannel()` es falso. `CHANNEL_METADATA_ID=0` y `CHANNEL_METADATA_NAME=""` mantienen deshabilitada la fuente Telegram heredada; `UpdateHelper.checkNewVersionAvailable` también comprueba esa condición. Conservar esos guards y revisar todas las rutas si se configura metadata en el futuro, no solamente GitHubUpdater. El canal NagramX empleado para paquetes de emoji no debe confundirse con una fuente autorizada de binarios.

`.github/workflows/release.yml` conserva un workflow heredado para pushes a main: incluye artefactos APK, prerelease público con título Exteraless y envío opcional a Telegram; `publish` tiene default true. Esto no es el workflow privado Connected Alpha ni se ejecuta desde esta rama. Antes de integrar cambios funcionales a main, debe revisarse/retirarse esa publicación heredada mediante una tarea separada. No hay base para asegurar que sus secretos o destinos estén configurados: no se han consultado. Esta auditoría no la dispara ni la modifica.
