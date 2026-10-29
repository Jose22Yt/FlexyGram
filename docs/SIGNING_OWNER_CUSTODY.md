# Generación y custodia por @Lukhou23

## Estado y condición de cierre

No se ha generado una clave oficial en el entorno temporal. No hay entrega privada, dos copias comprobadas ni huella Beta disponibles. Esta misión prepara la alternativa autorizada: generación directamente en un equipo/dispositivo del propietario. La firma solo se considerará establecida cuando el propietario confirme acceso al original y a ambas copias, y se contraste el certificado público.

Nunca envíes el PKCS12, contraseñas o backups al chat, a un comentario o a un PR. La única entrada necesaria para revisión externa será el **certificado público DER `.cer`** y su SHA-256, junto con el resultado público del verificador. Un certificado permite comprobar la identidad pública; no acredita por sí solo custodia de la clave o copias de seguridad.

## Alternativa automatizada

Para el flujo guiado, usa [README_LOCAL.md](../tools/signing/README_LOCAL.md) y `python3 tools/signing/owner_wizard.py`. La herramienta genera únicamente en una terminal propia, conserva el original si se interrumpe, cifra dos copias y exige dos restauraciones más confirmación del propietario. Los pasos manuales siguientes siguen disponibles.

## 1. Preparación local

Usa un dispositivo propio actualizado, almacenamiento cifrado y una sesión sin grabación de pantalla ni registro de terminal. Requisitos: JDK 21 (`java` y `keytool`), `age` oficial y acceso al código del PR #131. Los ejemplos siguientes son para una terminal POSIX (Linux/macOS o Android con una terminal y JDK compatibles). En Windows usa rutas y controles de acceso equivalentes; no ejecutes comandos de otra plataforma sin adaptarlos.

Si ya existe un almacén oficial, **detente y verifícalo**: este procedimiento no autoriza reemplazarlo ni regenerarlo. El alias y el certificado deben conservarse para todas las versiones.

Crea en un gestor de contraseñas una contraseña aleatoria exclusiva de al menos 32 caracteres ASCII para el PKCS12. No la derives del nombre de la app. Conserva además las contraseñas de los backups, distintas de la del PKCS12, con recuperación del gestor que no dependa exclusivamente del mismo teléfono.

Desde la raíz del repositorio, define una carpeta privada fuera del checkout; `mkdir` debe fallar si ya existe para evitar reutilización accidental:

```bash
umask 077
FG_SIGN_DIR="$HOME/FlexyGramSigning"
mkdir -m 700 "$FG_SIGN_DIR"
java -version
keytool -help
age --version
```

No continúes si falló un paso o falta una herramienta. No uses runners, almacenamiento compartido de Android ni una carpeta pública/sin cifrar para el original. Los comandos de generación, cifrado y recuperación de este documento **no se han ejecutado por el asistente**.

## 2. Generar una sola vez

```bash
keytool -genkeypair -keystore "$FG_SIGN_DIR/flexygram-release.p12" -storetype PKCS12 -alias flexygram-release -keyalg RSA -keysize 3072 -sigalg SHA256withRSA -validity 10000 -dname "CN=FlexyGram Release Key,OU=@Lukhou23"
```

Introduce y confirma la contraseña del gestor cuando `keytool` la solicite. No la pongas en `-storepass`, `-keypass`, scripts o variables de shell. Usa la misma contraseña de almacén y entrada para la compatibilidad PKCS12/JDK. Confirma que el comando termina correctamente y guarda el original sin moverlo a Git.

## 3. Verificar el original y exportar solo lo público

Desde la raíz del repositorio:

```bash
java tools/signing/VerifySigning.java keystore "$FG_SIGN_DIR/flexygram-release.p12"
keytool -exportcert -keystore "$FG_SIGN_DIR/flexygram-release.p12" -storetype PKCS12 -alias flexygram-release -file "$FG_SIGN_DIR/flexygram-release.cer"
java tools/signing/VerifySigning.java certificate "$FG_SIGN_DIR/flexygram-release.cer"
```

El verificador exige un PKCS12 con una única entrada privada `flexygram-release`, RSA de 3072 bits, certificado autofirmado SHA256withRSA, CN exacto, vigencia actual y separación del certificado Alpha conocido. Comprueba la correspondencia de clave privada y certificado mediante un desafío aleatorio en memoria. Eso no firma una APK/AAB ni publica material privado. El modo manual no usa contraseñas por argumentos ni tuberías y necesita terminal interactiva. La alternativa automatizada owner_wizard.py transmite la contraseña solo en el entorno de su proceso hijo al modo keystore-env, sin guardarla ni imprimirla.

`keytool -exportcert` sin `-rfc` exporta un certificado DER público, **sin la clave privada**. Ambos informes deben dar la misma SHA-256. Guarda esa huella pública y copia su valor de 64 dígitos hexadecimales en la siguiente variable; no copies una contraseña:

```bash
FG_CERT_SHA256='REEMPLAZAR_POR_LA_HUELLA_PUBLICA_DE_64_HEX'
java tools/signing/VerifySigning.java keystore "$FG_SIGN_DIR/flexygram-release.p12" "$FG_CERT_SHA256"
java tools/signing/VerifySigning.java certificate "$FG_SIGN_DIR/flexygram-release.cer" "$FG_CERT_SHA256"
```

`PASS` con `private_key=POSSESSION_VERIFIED` acredita acceso local en ese momento. `private_key=NOT_CHECKED` en el modo certificado es intencional. El verificador no declara confirmada la custodia. Un fallo no debe resolverse generando otra clave por ensayo.

## 4. Dos backups cifrados y separados

Cifra dos copias independientes usando `age -p`. Solicita contraseñas por terminal; elige frases fuertes del gestor y consérvalas fuera del soporte del backup. No uses argumentos o variables para esas contraseñas.

```bash
age -p -o "$FG_SIGN_DIR/flexygram-release-backup-A.p12.age" "$FG_SIGN_DIR/flexygram-release.p12"
age -p -o "$FG_SIGN_DIR/flexygram-release-backup-B.p12.age" "$FG_SIGN_DIR/flexygram-release.p12"
```

Los archivos A y B son inicialmente archivos de preparación. **Todavía no son dos copias independientes bajo custodia.** Copia A a un soporte bajo tu control y B a otro dispositivo/soporte separado físicamente (por ejemplo, unidad externa guardada y segundo almacenamiento privado). No guardes ambas únicamente en el teléfono original. Conserva el original protegido y las contraseñas con un mecanismo de recuperación separado. La capa PKCS12 más el cifrado age no elimina la necesidad de proteger las contraseñas.

Registra localmente ubicación de A/B, fecha, SHA-256 pública y responsable, sin publicar rutas privadas ni contraseñas. No hace falta subir los backups a GitHub o a este chat.

## 5. Probar recuperación desde cada soporte real

Recupera **el archivo cifrado leído desde cada destino final**, no solo la copia que quedó en la carpeta de preparación. Sustituye las rutas de ejemplo por las de tus soportes. Usa nombres nuevos; nunca descifres encima del original:

```bash
age -d -o "$FG_SIGN_DIR/recovered-A.p12" /ruta/al/soporte-A/flexygram-release-backup-A.p12.age
cmp "$FG_SIGN_DIR/flexygram-release.p12" "$FG_SIGN_DIR/recovered-A.p12"
java tools/signing/VerifySigning.java keystore "$FG_SIGN_DIR/recovered-A.p12" "$FG_CERT_SHA256"
age -d -o "$FG_SIGN_DIR/recovered-B.p12" /ruta/al/soporte-B/flexygram-release-backup-B.p12.age
cmp "$FG_SIGN_DIR/flexygram-release.p12" "$FG_SIGN_DIR/recovered-B.p12"
java tools/signing/VerifySigning.java keystore "$FG_SIGN_DIR/recovered-B.p12" "$FG_CERT_SHA256"
```

Exige éxito del descifrado, comparación exacta y posesión de clave para A **y** B. Si cualquiera falla, conserva el original y corrige el backup; no reemplaces la identidad. Retira luego las copias temporales recuperadas del área de prueba según la política de tu dispositivo; borrar un archivo no garantiza borrado físico en flash o snapshots. No destruyas el original ni los dos backups finales.

## 6. Confirmación del propietario y revisión pública

Solo después de las pruebas, confirma estos hechos sin revelar secretos:

- Tengo acceso al PKCS12 original y a su contraseña.
- Tengo A y B cifrados en soportes separados bajo mi control.
- He recuperado y verificado ambas copias desde sus destinos finales.
- Tengo recuperación de las contraseñas independiente del dispositivo original.
- Esta es la SHA-256 pública y este es el archivo **público** `flexygram-release.cer`.

El asistente podrá verificar el certificado público, registrar su huella exacta y comparar los resultados. No podrá comprobar físicamente tus soportes; la confirmación de custodia es del propietario. No se declara terminada la firma antes de ese paso. Si solo tienes el teléfono y aún no dispones de un segundo soporte independiente, la custodia permanece pendiente.

## 7. Incorporación futura a Actions

La custodia confirmada no autoriza automáticamente subir la clave. Se necesita autorización posterior del propietario para incorporarla a un entorno protegido Beta. Los nombres y procedimiento están en [SIGNING.md](SIGNING.md). No se han creado secretos, entornos o workflows nuevos de compilación en esta misión.

## Referencias oficiales

- JDK 21 keytool (genkeypair, PKCS12, exportcert): https://docs.oracle.com/en/java/javase/21/docs/specs/man/keytool.html
- age (cifrado por contraseña y descifrado interactivo): https://github.com/FiloSottile/age/blob/main/README.md
