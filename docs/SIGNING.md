# Firma oficial de FlexyGram

**Estado real:** la nueva clave no se ha generado. No existe huella oficial Beta registrada por esta misión. Gradle está preparado para exigir una identidad propia; ninguna APK ha sido firmada ni verificada.

## Custodia por el propietario

El propietario debe generar y conservar la clave en su equipo o almacén seguro permanente. No la generes en un runner o sesión efímera como única copia. Conserva dos copias cifradas separadas y las contraseñas en un gestor seguro; comprueba la restauración antes de usarla para un lanzamiento. La Library, los PR y los artefactos públicos no son una entrega apropiada de claves privadas.

Ejemplo **para ejecutar localmente por el propietario**, fuera del repositorio, usando JDK 21. `keytool` solicitará las contraseñas sin incluirlas en el comando:

```bash
keytool -genkeypair -keystore /ruta/privada/flexygram-release.p12 -storetype PKCS12 -alias flexygram-release -keyalg RSA -keysize 3072 -sigalg SHA256withRSA -validity 10000 -dname "CN=FlexyGram Release Key"
keytool -list -v -keystore /ruta/privada/flexygram-release.p12 -storetype PKCS12 -alias flexygram-release
```

Con PKCS12 usa la misma contraseña de almacén y clave cuando lo exija el proveedor JDK. El nombre del certificado no sustituye la verificación de su huella. Anota la SHA-256 pública mostrada, la fecha y el alias en el registro de lanzamiento; solo el certificado público y su huella pueden compartirse. No se genera un certificado a nombre de terceros.

## Configuración privada

| Entrada | Contenido |
| --- | --- |
| FLEXYGRAM_RELEASE_KEYSTORE | Ruta absoluta al PKCS12, fuera del checkout |
| FLEXYGRAM_RELEASE_STORE_PASSWORD | Contraseña del almacén |
| FLEXYGRAM_RELEASE_KEY_ALIAS | Alias de la clave oficial |
| FLEXYGRAM_RELEASE_KEY_PASSWORD | Contraseña de la clave |
| FLEXYGRAM_RELEASE_CERT_SHA256 | Huella pública SHA-256 fijada por el propietario |
| FLEXYGRAM_GOOGLE_AUTH_CLIENT_ID | Cliente OAuth Beta, opcional |

Se admiten variables de entorno o `local.properties`; no añadas valores reales a ejemplos ni registros. `LOCAL_PROPERTIES` base64 sigue el mecanismo existente, pero base64 no cifra secretos. Las rutas con barras invertidas en Properties deben escaparse o usar `/`.

El gate previo a `preBetaBuild` exige clave privada accesible, certificado vigente, huella correcta, JSON Firebase del paquete Beta y credenciales Telegram válidas en formato. Rechaza el certificado Alpha conocido y el certificado Android Debug. No demuestra por sí mismo que una clave sea de propiedad legítima: la custodia y la aprobación de la huella corresponden al propietario. La verificación de una APK resultante queda pendiente.

## Preparación de CI futura

No se crean ni modifican secretos de GitHub en esta misión. En una fase posterior autorizada, usar un entorno protegido Beta con las entradas anteriores y un secreto `FLEXYGRAM_RELEASE_KEYSTORE_B64`. El runner deberá decodificarlo en `$RUNNER_TEMP`, fuera del checkout, exportar su ruta, verificar la huella antes de compilar y borrar inputs/archivos privados incluso al fallar. Evitar `set -x`, volcado del entorno, caches con credenciales y subida del PKCS12 como artefacto. Base64 solo transporta el archivo.

Los secretos Alpha no se renombran ni se copian a Beta. No existe un pipeline nuevo de publicación automática. Antes de entregar cualquier APK futura debe existir un verificador Beta revisado que compruebe paquete, versión, firma y payload completo, además del transporte privado autorizado.

## Procedimiento completo y comprobador sin Android

Sigue [SIGNING_OWNER_CUSTODY.md](SIGNING_OWNER_CUSTODY.md) para generar una sola vez en un dispositivo propio, crear dos backups cifrados, probar su restauración y confirmar la custodia. `tools/signing/VerifySigning.java` inspecciona localmente el PKCS12 sin exportar su clave privada, o verifica únicamente un certificado público DER. No genera claves ni procesa APK/AAB.

La política revisada exige alias `flexygram-release`, un único par de claves en PKCS12 real, RSA-3072, certificado autofirmado SHA256withRSA con CN `FlexyGram Release Key`, vigencia y huella fijada. Verifica la correspondencia privada/pública con un desafío en memoria. La clave y su huella siguen pendientes: todavía no existe una identidad Beta confirmada.

Para la futura carga autorizada en GitHub Actions, preparar un entorno `flexygram-beta` con revisión del propietario y acceso restringido a la rama aprobada cuando las capacidades de la cuenta/repositorio lo permitan. Secretos: `FLEXYGRAM_RELEASE_KEYSTORE_B64`, `FLEXYGRAM_RELEASE_STORE_PASSWORD`, `FLEXYGRAM_RELEASE_KEY_PASSWORD`. Variable pública fijada: `FLEXYGRAM_RELEASE_CERT_SHA256`; alias fijo `FLEXYGRAM_RELEASE_KEY_ALIAS=flexygram-release`. En el runner, `FLEXYGRAM_RELEASE_KEYSTORE` será una ruta temporal fuera del checkout. Las claves de Telegram, Firebase y OAuth siguen siendo entradas separadas. Verifica disponibilidad de las protecciones antes de cargar material privado: el nombre del entorno por sí solo no lo protege. No se han creado esos recursos ni cargado secretos en esta tarea.
