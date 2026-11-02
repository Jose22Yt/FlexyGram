# Identidad pública AntiTerm — 30 de octubre de 2026

El propietario solicita conservar la identidad AntiTerm existente y acepta el riesgo de exposición anterior. Este registro no certifica confidencialidad retroactiva ni custodia completa. No se genera una clave, no se cambian contraseñas y no se repiten respaldos.

## Evidencia comprobada

El certificado DER recibido coincide exactamente con SHA-256 `e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015`. Se comprobaron bytes DER sin material sobrante, RSA-3072, SHA256withRSA, autofirma válida, sujeto/emisor CN=FlexyGram Release Key / OU=@Lukhou23 y vigencia UTC 2026-10-30T23:00:20Z a 2054-03-17T23:00:20Z. El informe original recibido se conserva en `config/signing/public-verification.json` y declara `private_key=NOT_CHECKED`, `custody=OWNER_CONFIRMATION_REQUIRED`, `android_apk=NOT_TESTED`.

El certificado anterior `5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c` queda en el historial Git y deja de ser aceptado para esta propuesta de Beta. Alpha permanece intacta. El certificado no incorpora un applicationId; su asociación con `com.flexygram.messenger` y el alias esperado `flexygram-release` pertenece a la configuración y debe comprobarse contra el PKCS12 real.

## Pendientes reales

- No se recibió ni abrió PKCS12 ni contraseña. La posesión y correspondencia privada/pública siguen pendientes de la comprobación real. El modo interactivo `keystore` permite comprobarlas sin ejecutar el asistente de respaldos.
- El propietario informa que conserva respaldos cifrados y recuperación. No se inspeccionaron sus contenidos ni destinos. No se cambia `REVALIDATION_PENDING` ni se declara `OWNER_ATTESTED_AFTER_TWO_RESTORES` por editar metadatos públicos.
- No se validaron Firebase, secretos protegidos ni APK real en este cambio. La auditoría Actions #5 corresponde al lanzador anterior y no aprueba esta nueva fuente.

## Ruta de aprobación

Esta propuesta deriva exclusivamente de PR #141 (`aeb6b5fc01f6332ab82194e311b52a19d702a81e`), conservando sus fuentes Android y optimizaciones. Actualiza certificado, pines, herramientas públicas, documentación y contratos de comprobación. El ZIP local contiene solo herramientas y certificado público.

La infraestructura en main conserva su fuente fijada al PR141 original, por lo que todavía rechaza esta identidad. Tras revisión independiente de esta propuesta se necesitará un PR de infraestructura que fije el nuevo commit revisado y sus hashes exactos, conservando las protecciones y el bloqueo por secretos pendientes. No se introduce un SHA configurable por input ni un bypass del pin. No se fusiona toda la aplicación en main para activar el workflow.

La carga privada se hará únicamente mediante los siete secretos del entorno protegido `flexygram-beta`, con aprobación independiente y limpieza temporal. No se compila, firma ni publica una APK en esta propuesta.
