# Informe de custodia de firma — 29 de octubre de 2026

Base revisada: PR #131, `feat/official-identity-beta-preparation`, commit inicial `432aad76c5bcc8305e4ff917827c522a0dd93f8e`.

| Punto | Estado real |
| --- | --- |
| Clave oficial generada | No |
| Keystore accesible en esta sesión | No se ha creado ni recibido uno |
| Entrega al propietario | No realizada |
| Dos copias cifradas y recuperación real | Pendientes de ejecución y confirmación del propietario |
| Certificado público / SHA-256 Beta | Pendientes, sin valores ficticios |
| Custodia propuesta | Generación local por @Lukhou23, original protegido y backups age en dos soportes separados |
| Alias / formato / algoritmo | flexygram-release / PKCS12 / RSA-3072, SHA256withRSA |
| Firma Alpha | Sin cambios |
| Paquete | com.flexygram.messenger, sin cambios |
| Secretos de Actions | Nombres y procedimiento preparados; ninguno creado, leído ni cargado |
| APK/AAB | Ninguna compilación, empaquetado, firma o publicación |

La condición de no generar una clave definitiva en una sesión temporal se aplica porque no existe confirmación de entrega, acceso y recuperación en soportes del propietario. La alternativa implementada es [el procedimiento de generación y custodia local](SIGNING_OWNER_CUSTODY.md).

Revisión de configuración: se exige un almacén PKCS12 real con una sola identidad y alias fijo; certificado vigente, autofirmado y CN correcto; RSA de 3072 bits y firma SHA256withRSA; huella pública fijada y rechazo del certificado Alpha conocido/debug. Se agrega prueba en memoria de correspondencia entre clave privada y certificado; no firma APK. Se conservan paquete, configuración y archivos de Alpha. El nombre del certificado no demuestra autoría o propiedad: el control de la clave corresponde al propietario.

Comprobaciones locales: el verificador Java compila con el compilador JDK 17 disponible (compatible a nivel de código con el JDK 21 previsto para el proyecto). Cinco casos inválidos o sin terminal interactiva se rechazan sin imprimir datos de entrada. Se revisan XML/documentación, hashes de identidad y diffs. No se genera ningún par de claves de prueba ni definitivo para aparentar una validación positiva. No se ha ejecutado Gradle ni Android. El PKCS12 real, su contraseña, posesión, certificado, vigencia efectiva, huella y restauración deberán verificarse cuando existan en el dispositivo del propietario.

Pruebas reproducibles sin Android: `python3 tools/signing/check_verifier.py` y `python3 tools/identity/check_identity.py`. La ejecución del comprobador Java sobre un PKCS12 real se hace únicamente por el propietario, con contraseña interactiva. El asistente podrá revisar después exclusivamente el certificado público DER y su SHA-256.

Cierre pendiente: el propietario genera la clave una sola vez, exporta `.cer`, verifica original y las restauraciones A/B, confirma custodia y comparte solo el certificado público. Entonces se contrasta y registra la huella. La incorporación a GitHub Actions requiere autorización posterior y protecciones verificadas. La compilación y verificación de una APK Beta continúan pendientes de autorización expresa.

## Automatización local adicional

Se inspeccionó la disponibilidad de transferencia de archivos autenticados. Eso no acredita que exista un destinatario de cifrado verificado ni una recuperación efectiva bajo control del propietario; no se generó una clave en esta sesión. Se implementa la alternativa local autorizada mediante `tools/signing/owner_wizard.py`, con documentación para Android/Termux y paquete de herramientas pequeño, sin material privado.

El asistente local verifica precondiciones, exige contraseña de gestor de 32 caracteres o más, usa contraseñas solo en el entorno de procesos hijos, conserva el almacén en carpeta privada fuera de Git y rechaza CI/entorno del asistente. Reanuda sin regenerar; si una huella ya fijada pierde su almacén, exige recuperación. Los backups existentes no se sobrescriben. Exige dos descifrados y comparación exacta, prueba de clave privada y confirmación explícita del propietario sobre independencia de soportes y recuperación de contraseñas. El software no puede probar esa independencia física.

Pruebas nuevas: 16 casos de ciclo de vida/recuperación con herramientas simuladas y bytes expresamente ficticios, sin crear pares de claves. El verificador Java pasa 6 rechazos de entradas inválidas/no interactivas. No se acredita un éxito PKCS12 real ni se prueba Android físicamente. El paquete contiene únicamente fuentes, guía, pruebas, licencia y sumas de integridad. Los comandos de generación/cifrado/recuperación se ejecutarán después por el propietario en su dispositivo.

Estado de cierre sin cambios: clave y huella Beta aún no existen aquí; entrega privada y confirmación de backups pendientes. Ninguna APK/AAB ni nuevo pipeline ejecutado; no se cargan secretos.
