# Verificador postfirma específico de Beta — pendiente de ejecución

Este cambio añade tools/beta_handoff/post_sign.py y sus regresiones.
Se apila sobre PR28; no modifica cliente, PR23, Diagnostic ni contratos históricos.
Reutiliza gate.run de PR25 y regular/strict_json/members/check_signature/check_alignment
del verificador histórico. Nunca llama a su verify ni approved_identity.

## Evidencia de esta sesión

- PR23 inicial: 78151d9e8083290dca2617279cab3afb53540de6.
- PR23 actualizado durante la sesión: 97dfb08e58159b31d322dd8435080fb039abdeb9.
- PR28 base: de864e5de0ef11d6f8bdff379cd3b1943fc5409d.
- PR29: be75bdb65ddb5ae5a68024a985295eae7f612dd8, integrado por Work2 en
  ef1ce2d22506f4258b48f11c3e644ef5000214ce y
  97dfb08e58159b31d322dd8435080fb039abdeb9. Comparación independiente de los
  ocho blobs: identidad exacta con PR29 (helpers, Activity, doubles, pruebas y
  evidencia). No se afirma ejecución de esas pruebas ni Android.
- gate.py, review_apk.py y verify_post_sign_diagnostic.py permanecen idénticos
  entre el HEAD inicial y el actualizado. Esta rama sigue apilada en PR28,
  sin copiar ni modificar los archivos concurrentes de Work2.
- Sin entorno ejecutable: el intento devolvió
  "No usable execution environment is available".
- **15 métodos de prueba preparados; 0 ejecutados; aprobados/fallidos no determinados.**
  No se ejecutaron Python, apksigner, aapt2, zipalign, Java, Gradle ni Android.
  No se generaron claves, certificados, firmas, APK ni respaldos.
- No hay nuevo defecto del cliente confirmado en esta revisión limitada.
  No se repiten compilación, descargas, Dropbox ni suites históricas.

## Entradas privadas necesarias

Work2 entregará el unsigned ORIGINAL, SHA256, commit completo, versión, directorio
exacto de clases Java del mismo build, informe exitoso del gate PR25 y recibo de
build. No mezclar clases de otro checkout. El recibo JSON tiene:

- schema: 1; package: io.github.jose22yt.flexygram.beta.development.
- source_commit: SHA Git completo; version_code y version_name: cadenas exactas.
- unsigned_apk_sha256: SHA256 del unsigned.
- unsigned_review_sha256: SHA256 de los bytes del informe gate PR25.
- classes: mapa completo ruta relativa POSIX -> SHA256, obtenido con
  post_sign.class_inventory(Path(directorio_de_clases)). Incluye todos los archivos,
  sin enlaces simbólicos, y al menos org/telegram/messenger/BuildConfig.class.

El recibo es una declaración revisada de procedencia; el código no puede deducir
el commit Git ni demostrar procedencia del compilador a partir de bytes de APK.
El operador debe conservar logs, JNI y evidencias originales de build junto al
recibo y revisar esa relación antes de aprobar su hash.

Después de una autorización independiente y explícita, se necesitarán el signed
original, su SHA256, y una copia recuperada privadamente en otra ruta. El
verificador compara sus bytes por SHA256 pero NO observa la transferencia remota.
Usar PR25 archive para conservar/recuperar cada paquete con una sola APK;
no pasarle un archivo con dos APK. Conservar recibos de acceso/revisión privada.

## Autorización separada y sin secretos

El checklist DRAFT de PR28 y una identidad Diagnostic NO son aceptados.
Un responsable autorizado debe revisar custodia recuperable y aprobar el hash
concreto del unsigned y del recibo de build. Registrar esa decisión verificable
en un JSON privado con estos campos requeridos:

- schema: 1; status: CUSTODY_VERIFIED_BETA_SIGNING_AUTHORIZED.
- approval_scope: FlexyGram_Beta_personal_offline_only.
- package: io.github.jose22yt.flexygram.beta.development.
- apk_signing_authorized: true; production_use_allowed: false.
- private_key_backed_up: true; custody_recovery_verified: true.
- approval_reference: referencia comprobable de la decisión (mínimo 8 caracteres).
- approved_unsigned_apk_sha256 y build_receipt_sha256: hashes revisados.
- certificate_sha256: huella SHA256 aprobada, minúscula sin separadores, no ceros.

Este esquema no concede autorización por rellenarlo ni autentica al firmante del
JSON. La revisión humana del origen de la decisión sigue siendo obligatoria.
No crear ese registro como si hubiera autorización hoy. Nunca incluir clave,
keystore, contraseñas, tokens ni texto personal; el verificador no los necesita.
La huella identifica el certificado autorizado sin depender de nombres heredados.
Custodia/generación, firma por hash, entrega, instalación y prueba son decisiones
separadas. El resultado nunca concede permiso de instalar o distribuir.

## Ejecución futura en host con Python3.11, pyelftools0.32 y herramientas fijadas

Primero ejecutar las nuevas regresiones, normal y optimizado:

    python3.11 -B -m unittest discover -s tests/beta_post_sign -v
    python3.11 -O -B -m unittest discover -s tests/beta_post_sign -v

Las pruebas usan ZIPs sintéticos y dobles explícitos de herramientas; no generan
certificados ni firmas. Un éxito sintético no es apksigner real ni Android.

Después de disponer de todos los archivos y autorizaciones reales:

    python3.11 tools/beta_handoff/post_sign.py --help

Ejemplo de invocación (rutas privadas del operador, variables sólo de hashes,
commit y versión; sin contraseñas):

    python3.11 tools/beta_handoff/post_sign.py --unsigned-apk /private/beta/unsigned.apk --signed-apk /private/beta/signed.apk --recovered-apk /private/recovered/signed.apk --unsigned-sha256 "$BETA_UNSIGNED_SHA256" --signed-sha256 "$BETA_SIGNED_SHA256" --commit "$BETA_SOURCE_COMMIT" --version-code "$BETA_VERSION_CODE" --version-name "$BETA_VERSION_NAME" --classes /private/beta/classes --unsigned-review /private/beta/unsigned-review.json --build-receipt /private/beta/build-receipt.json --approval /private/beta/signing-approval.json --build-tools /sdk/build-tools/36.0.0 --ndk /sdk/ndk/27.2.12479018 --javap /jdk21/bin/javap --output /private/reports/post-sign-NEW.json

El informe debe ser NUEVO, fuera del repositorio, de entradas y directorios de
herramientas. Se crea exclusivo, modo0600; nunca sobrescribe un PASS previo.
Salida0 significa BETA_SIGNED_STATIC_REVIEW_ONLY_PENDING_ANDROID; salida1 BLOCKED.
Fallos/importaciones/herramientas ausentes bloquean, con tipos de error saneados.
No se registran stdout/stderr de herramientas en el informe.

## Alcance real

Reejecuta el gate unsigned completo (identidad/offline, Java/JNI, ELF API24/4K/16K,
Chaquopy y escáner heredado). Compara rutas y hashes descomprimidos con el signed;
sólo excluye metadatos estrechos de firma JAR nuevos. Conserva un MANIFEST.MF
preexistente. Verifica apksigner real, v2 para minSdk24 y un certificado exacto,
zipalign real del signed, manifiesto binario y ausencia de cambios durante revisión.
No basta con un informe anterior ni se salta el gate con una opción CLI.

La igualdad del payload conserva DEX, recursos, JNI, Python, manifiesto y política
del unsigned revisado; no demuestra ejecución de esas políticas ni carga real.
La alineación ELF se hereda del gate sobre los mismos bytes; ZIP se vuelve a medir.
No certifica arranque, rendimiento, compatibilidad Android17/ART/linker ni aceptación
de instalación en un teléfono. Quedan pendientes las pruebas Android autorizadas,
la ejecución de las regresiones PR29 por Work2 y todas las decisiones de custodia,
firma, entrega e instalación. Production, autenticación y servicios siguen cerrados.
