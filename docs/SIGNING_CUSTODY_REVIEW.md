# Registro público de firma — 29 de octubre de 2026

## Evidencia recibida

El propietario confirmó generación local y acceso con PASS/POSSESSION_VERIFIED. Se recibieron `flexygram-release.cer` y `public-verification.json`, ambos públicos. El JSON recibido muestra PASS para el certificado, `private_key=NOT_CHECKED`, `custody=OWNER_CONFIRMATION_REQUIRED` y `android_apk=NOT_TESTED`. No es un informe de inspección de PKCS12 ni de doble recuperación. No se recibió ninguna clave privada o contraseña.

El certificado DER tiene SHA-256 **5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c**. Coincide exactamente con la huella indicada por el propietario y con el JSON. OpenSSL y el verificador Java comprobaron el certificado; RSA-3072, SHA256withRSA, autofirma válida y CN=FlexyGram Release Key / OU=@Lukhou23. Vigencia UTC: 2026-10-29T22:39:21Z a 2054-03-16T22:39:21Z. No es el certificado Alpha conocido.

## Registro implementado

- `config/signing/flexygram-release.cer`: solo certificado público DER.
- `config/signing/identity.properties`: asociación del paquete `com.flexygram.messenger`, alias aprobado `flexygram-release`, PKCS12 y SHA-256 oficial.
- Gradle exige coincidencia con el pin y el certificado público. El entorno no puede introducir una huella alternativa. Se conservan las protecciones contra claves Debug/Alpha, tipo/algoritmo/alias y correspondencia de clave privada.
- Verificador y asistente local fijan esta identidad. La generación local de nuevas claves se retira: una pérdida requiere recuperar el PKCS12 original, no regenerar.
- Toolkit actualizado con código y certificado públicos, sin PKCS12, contraseñas o backups. No se reescribe el historial.

## Alcance real

La clave fue generada por el propietario, no por el asistente. El propietario conserva el PKCS12. No hay entrega ni custodia privada por este entorno. El alias, la presencia y acceso a la clave privada se volverán a comprobar cuando el propietario ejecute la inspección del PKCS12 o se autorice un entorno de firma. El asistente verificó únicamente el certificado público; no atribuye a este archivo una prueba de posesión privada.

Un certificado X.509 no incluye el applicationId de Android. La asociación con Beta se comprueba en Gradle y metadatos; RSA-3072/SHA256withRSA son coherentes con la política del proyecto. La compatibilidad definitiva requiere una futura compilación autorizada y verificación de APK/manifiesto/firma. No se afirma instalación ni actualización probada.

Pendiente: confirmación de dos backups cifrados independientes y su recuperación; configuración de servicios propios de Beta; autorización separada de carga a Actions; futura compilación y validación Android. La falta de confirmación de backups no impide registrar el certificado público, pero impide declarar la custodia completa.

No se genera otra clave, no se lee el PKCS12, no se cargan secretos y no se compila/empaqueta/firma/publica APK/AAB. CI se omite con `[skip ci]`; comprobaciones de fuentes y certificado realizadas localmente.
