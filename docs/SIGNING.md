# Firma oficial de FlexyGram Beta

El propietario confirmó haber generado la clave en su teléfono y tener acceso a ella. El asistente recibió **solo el certificado público y un informe de comprobación pública**, nunca el PKCS12 ni contraseñas. Certificado verificado el 29 de octubre de 2026 con Java y OpenSSL.

| Campo | Identidad registrada |
| --- | --- |
| Paquete Beta | com.flexygram.messenger |
| Alias aprobado | flexygram-release |
| Almacén privado esperado | PKCS12, bajo control del propietario |
| Clave pública | RSA-3072 |
| Algoritmo del certificado | SHA256withRSA |
| Sujeto / emisor | CN=FlexyGram Release Key, OU=@Lukhou23 |
| Vigencia UTC | 2026-10-29 22:39:21 a 2054-03-16 22:39:21 |
| SHA-256 | 5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c |

Fuentes públicas de la configuración: [identity.properties](../config/signing/identity.properties) y [flexygram-release.cer](../config/signing/flexygram-release.cer). El certificado contiene únicamente la clave pública. No demuestra por sí mismo el alias del almacén ni su custodia, y no incorpora un applicationId Android: la asociación con el paquete se fija en la configuración del proyecto. La compatibilidad aquí es de fuentes/configuración, no una APK firmada o instalada.

## Protección de identidad

Gradle exige que el certificado del PKCS12 tenga la huella que coincide con la identidad pública registrada. Una variable externa no puede sustituir esa huella: si `FLEXYGRAM_RELEASE_CERT_SHA256` se proporciona, debe coincidir. Se conservan PKCS12 real, una sola entrada, alias fijo, RSA-3072, autofirma SHA256withRSA/CN, vigencia y prueba de correspondencia privada/pública en memoria. Debug y Alpha siguen rechazados. La firma Alpha permanece intacta.

El verificador Java y el asistente local también fijan esta huella. **El asistente ya no genera claves**: únicamente verifica, recupera y respalda el PKCS12 oficial existente. Si el original falta, debe recuperarse desde un backup; no se sustituye por otra identidad.

## Entradas para una futura compilación autorizada

| Entrada privada/configuración | Valor o uso |
| --- | --- |
| FLEXYGRAM_RELEASE_KEYSTORE | Ruta al PKCS12 oficial fuera del checkout |
| FLEXYGRAM_RELEASE_STORE_PASSWORD | Contraseña privada del almacén |
| FLEXYGRAM_RELEASE_KEY_ALIAS | flexygram-release |
| FLEXYGRAM_RELEASE_KEY_PASSWORD | Contraseña privada de la entrada |
| FLEXYGRAM_RELEASE_CERT_SHA256 | Opcional; si existe, debe coincidir con el pin registrado |
| FLEXYGRAM_GOOGLE_AUTH_CLIENT_ID | OAuth propio de Beta, opcional |

No se han cargado secretos ni configurado servicios externos. Si posteriormente se autoriza incorporar la clave a Actions, usar un entorno protegido `flexygram-beta` con revisión del propietario y restricciones verificadas. El PKCS12 podrá transportarse exclusivamente como secreto protegido `FLEXYGRAM_RELEASE_KEYSTORE_B64`; base64 no cifra. Decodificar fuera del checkout, comprobar el pin y limpiar inputs incluso al fallar. No imprimir el entorno, activar trazas de secretos, cachear la clave ni subirla como artefacto. El nombre de un entorno no garantiza sus protecciones: deben verificarse antes de cargar el material privado.

Firebase, Maps y OAuth deben registrarse por el propietario para el paquete Beta y esta huella cuando corresponda. No se reutilizan credenciales Alpha ni se crean registros externos automáticamente.

## Comprobaciones sin Android

```bash
java tools/signing/VerifySigning.java certificate config/signing/flexygram-release.cer 5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c
python3 tools/signing/check_verifier.py
python3 tools/identity/check_identity.py
```

Para verificar el PKCS12, el propietario puede usar el modo interactivo `keystore` o el [asistente local](../tools/signing/README_LOCAL.md). La clave privada no debe enviarse al asistente.

Pendientes: confirmación de dos backups independientes y su recuperación, acceso al PKCS12 en el entorno futuro autorizado, validación real de Gradle y firma/payload de una futura APK. No se ha compilado, firmado ni publicado una APK/AAB. [Informe de alcance](SIGNING_CUSTODY_REVIEW.md).
