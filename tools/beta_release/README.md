# Continuación de la entrega oficial Beta

Base: PR140 `72f7e7f1e8600a85ab2539e04197b2fc9a6742a1`. Conserva toda la integración de Work1 y corrige AppName/AppNameBeta a **FlexyGram Beta** en los ocho overlays existentes. La etiqueta real del manifiesto, NagramX, también se resuelve a FlexyGram Beta en el overlay Beta. Paquete, versionCode1290, certificado, iconos, Java de aplicación, JNI y validación Gradle permanecen intactos.

## Bloqueo actual

No están disponibles en las entradas de entorno el PKCS12 oficial, sus contraseñas ni credenciales Telegram. Tampoco hay archivo Firebase Beta en el checkout. El certificado público no permite firmar. No se genera ni sustituye la identidad.

El propietario debe provisionar los originales en un entorno seguro autorizado, fuera del checkout, conforme a `docs/SIGNING.md`. No enviar clave ni contraseñas por chat. Si se usa Actions, verificar las protecciones reales de `flexygram-beta` antes de cargar secretos; el nombre no garantiza protección. Esta continuación no crea entornos ni carga secretos.

## Construcción y aceptación pendientes

1. Provisionar clave original, contraseñas, alias `flexygram-release`, credenciales Telegram y Firebase de `com.flexygram.messenger`.
2. Para la ruta por variables de entorno: `python3 tools/beta_release/preflight.py`. Solo diagnostica presencia y nombres de entradas faltantes; no abre el PKCS12, valida contraseñas ni prueba correspondencia criptográfica. La ruta local.properties original sigue soportada por Gradle.
3. Preparar JDK21, SDK37/build-tools36, NDK27.2.12479018, CMake3.31.6, Python3.11 y módulos completos JNI/Chaquopy. Ejecutar `NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleBeta --no-daemon --console=plain`. Se conserva el validador original de pin/alias/PKCS12 y correspondencia privada/pública, sin bypass.
4. Verificar el APK real: `python3 tools/beta_release/verify_beta_apk.py /ruta/privada/FlexyGram_Beta.apk --build-tools /ruta/sdk/build-tools/36.0.0`. Exige el pin oficial sin override, firmas v2/v3, alineaciónZIP16KB, paquete/versión/nombre, launcher/providers/backup, payload Telegram y96 ELF AArch64 compatibles con16KB, incluidos Chaquopy anidados. El verificador Alpha original sigue intacto.
5. Cifrar y entregar por la vía privada autorizada; no publicar APK sin protección.
6. Validar instalación/login/red/push/multimedia, efectos/borrado, scroll/multitap/temas, consumo sostenido y una actualización con misma firma y mayor versionCode en Poco. Un informe de APK no acredita aceptación física.

No hay APK nueva ni correspondencia privada/pública verificada. Los tests del verificador usan respuestas de herramientas simuladas y ZIP sintético; no son evidencia de un APK construido o firmado.

## Verificación realizada

Suite completa anterior al último ajuste de NagramX: 381 métodos host PASS y 144 generales PASS /31 omisiones opcionales. Después del ajuste: 14 tests específicos/compatibilidad, identidad y compilación AAPT2 de recursos Beta PASS. Certificado público y ocho rechazos PASS. La validación CI del PR repetirá la suite completa sobre la fuente final. Ningún resultado equivale a una APK firmada o instalada. Detalle: verification.json.

## Propuesta AntiTerm e71c4d (30 de octubre de 2026)

Sobre PR141 se propone únicamente la sustitución pública autorizada por el propietario: certificado `e71c4d1e14dd940892009c61164df522c133029df6d1258561f6a1a4d1f3c015`, pines y herramientas de verificación. No cambia el código Android ni sus funciones, paquete, versión, JNI o validadores Gradle. El informe histórico verification.json acredita la base anterior, no la posesión de esta nueva identidad. Ver docs/SIGNING_CUSTODY_REVIEW.md para evidencias y pendientes actuales.

La auditoría #5 no autoriza esta fuente nueva. El lanzador en main sigue fijado al PR141 original y debe permanecer así hasta una actualización revisada separada. La posesión privada, Firebase, siete secretos protegidos, build real y aceptación en Poco siguen pendientes.
