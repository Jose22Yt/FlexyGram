# P0.4b — Separación Gradle y aislamiento Java/JNI

FlexyGram 1.0, creado y dirigido por **@Lukhou23**. Etapa limitada a arquitectura de variantes. No implementa autenticación ni constituye Paso 4.

## Integración autorizada

PR #14 se verificó en `4948fea8b11eca0d64eebbd0b12ea92faa3aa2aa`, base develop y exactamente seis archivos documentales. Se marcó listo y fusionó únicamente en develop mediante **`d9f2b788cf23e830e84ba24e9f6cb2e71e13bd4d`**. La rama `security/paso-3-p04b-build-variants` parte de esa integración. Las evidencias históricas de P0.3g, sus 93 pruebas y compilación asociadas al head `86226a55…`, permanecen intactas; no se reutilizan como resultado de este código.

## Separación implementada

| Aspecto | Diagnostic | Producción arquitectónica |
|---|---|---|
| Flavor / applicationId | diagnostic / io.github.jose22yt.flexygram.diagnostic | production / io.github.jose22yt.flexygram.app |
| Combinaciones | diagnosticDebug y diagnosticStaging | Ninguna variante habilitada; sin APK ni distribución |
| Identidad | Derivada de política fija, no APP_PACKAGE global | ID provisional aprobado, no reserva comercial ni publicación |
| Manifiesto | Manifiesto endurecido movido byte por byte a src/diagnostic | Placeholder sin launcher, INTERNET ni servicios; aplicación deshabilitada |
| Base común | Backup/restore deshabilitados; namespace Java/JNI original | Misma base de protección de datos, sin importar manifiesto diagnóstico |
| BuildConfig | ISOLATED_DIAGNOSTIC=true; seis capacidades=false; API ID0/hash vacío | Modelo isolated=false, todas las capacidades=false; AGP no genera sus clases |
| JNI | Header generado por CMake con flavor/scope, sin fallback de header ausente | CMake rechaza production, desconocido o vacío; no hay JNI productivo |
| Traducción | Solo diagnosticImplementation de :translation-compat-diagnostic | Sin implementación productiva; no hereda fachada ni AAR retirado |
| Firma | Config diagnosticLab asignada únicamente al flavor diagnostic | Sin firma, sin clave productiva, sin fallback al debug/laboratorio |
| Cuentas/datos | accountType recurso generado desde applicationId; sandbox y providers propios | accountType y namespace de almacenamiento derivados de .app, sin crear datos ni migraciones |

`gradle/variant-policy.json` es una política de código revisable, no un archivo privado editable que habilite servicios. El resolver exige exactamente ambas identidades y capacidades deshabilitadas. No basta cambiar true por false: el registro productivo requiere implementaciones futuras y está bloqueado en Gradle, AGP y CMake. Ningún secreto ni propiedad de entorno habilita production.

La política Java sigue leyendo BuildConfig por flavor y conserva DiagnosticPolicy sin cambios. BuildVariantPolicy expone capacidades inmutables y el namespace del sandbox a partir de APPLICATION_ID. CMake recibe flavor y SHA-256 de la política más nombre de flavor; genera el header en su directorio de build, separado por variante. La biblioteca JNI incorpora una atestación pública no secreta del scope/capacidades para contrastar el binario compilado. Las guardas nativas de solicitudes y sockets permanecen intactas. No se anuncia soporte para un JNI productivo que todavía no existe.

Los providers mantienen `${applicationId}`. AccountManager ya usa BuildConfig.APPLICATION_ID y los XML auth/sync ahora usan el recurso de tipo de cuenta generado. No se modifican FileLoader, ApplicationLoader, SharedConfig, UserConfig o bases de datos ni se importan carpetas externas. La separación de sandboxes y la inactividad de servicios de migración se preservan; la validación Android real y la auditoría de rutas externas de una futura producción siguen pendientes. `flexygram_storage_namespace` es un contrato explícito generado, no una afirmación de que todas las rutas externas heredadas ya fueron migradas.

## Credenciales y firma

Diagnostic no resuelve Telegram API ni configuración push privada: los valores utilizables no pueden entrar por LOCAL_PROPERTIES, variables de credenciales o servicios de otros proyectos. Se conserva sin cambios el resolver de pares propios `gradle/telegram-api.gradle`, probado con fixtures. `config/flexygram-production.properties.example` contiene campos vacíos y solo describe el esquema futuro; no se carga. Los archivos reales deberán estar fuera del repositorio y requerir autorización del propietario. No se han obtenido ni usado credenciales reales.

Se retiró la declaración inactiva de release.keystore y su lectura de contraseñas heredadas; todos los buildTypes tienen signingConfig nulo y únicamente el flavor diagnostic selecciona diagnosticLab. El laboratorio recuperado crea una clave diagnóstica independiente fuera de Git; no se publica su archivo ni sus contraseñas y no se crea clave productiva. Release diagnóstico también está deshabilitado para evitar combinaciones innecesarias. Esta clave temporal no define la futura firma estable de distribución.

## Bloqueo productivo comprobable

`gradle/production-readiness.gradle` produce una excepción con código `FLEXYGRAM_PRODUCTION_INCOMPLETE`. Una solicitud explícita de tareas production se rechaza en evaluación; además beforeVariants deshabilita esas variantes y las tareas assemble/bundle explícitas dependen del rechazo. Las abreviaciones que resuelven una de esas tareas tampoco pueden producir un artefacto. No existe parámetro de bypass.

Faltan: implementación de autenticación/transporte propia revisada, adaptadores/políticas productivos de traducción, manifiesto/launcher/recursos operativos aprobados, configuración Telegram propia autorizada y firma independiente. Cambiar solo el flavor, el ID, ISOLATED_DIAGNOSTIC o un par privado no completa esa arquitectura. Los SDK compartidos declarados no equivalen a servicios autorizados. Firebase/UnifiedPush, plugins y traducción siguen inactivos en Diagnostic.

## Pruebas y trazabilidad

Se mantienen las 93 pruebas de P0.3g, con adaptaciones de rutas/DSL por el movimiento de manifiesto y dependencia por flavor, más nueve pruebas de variantes. No se eliminó ningún caso ni se omitió ninguno. Los snapshots históricos permanecen inmutables: la extensión `tests/build_variants/reviewed_changes.json` fija antes/después de cambios explícitos sobre el merge P0.4a; las pruebas nunca regeneran hashes. Se comprueba por separado que el manifiesto Diagnostic conserva cada byte del aprobado y que las fuentes comunes de datos, seguridad y traducción no cambian.

Las pruebas nuevas ejecutan el resolver Groovy real y mutaciones negativas, el rechazo de producción con configuración sintética, Java real con BuildConfig sintético de ambas identidades, generación CMake, compilación nativa de atestación/guardas en host y rechazo sin header/flavor o con producción. Los arneses JVM/C++ no son Android ART ni prueban red real.

Para reproducir se necesitan los JDK/toolchains fijados, Gson2.14.0, KOTLIN_LIB de Gradle9.7.1, Android API24 y D8 BuildTools36.0.0; el antiguo translator classes.jar se usa solo como referencia ABI offline en tests y nunca como dependencia Android. Consultar los comandos/resultados de [VALIDATION.md](VALIDATION.md). `check_diagnostic.py` exige APK, clases, manifiesto y grafo nuevos del mismo build; compara BuildConfig, APK/DEX, bibliotecas ARM64, atestación JNI, recursos de identidad y escáneres históricos. No acepta un APK anterior como prueba.

## Límites

No instalación, dispositivo personal, cuenta, autenticación, llamadas Telegram/push/traducción, distribución de APK, Actions ni cambios de UI/animaciones/reproductor/actualizador. Compatibilidad API24 frente a ANDROID_PLATFORM27, cuatro bibliotecas Python16KB, restauración framework/OEM y ejecución Android permanecen bloqueos para beta. No se modifica plataforma nativa, NDK, Python o SDK declarados para ocultarlos. Mantener [el procedimiento de laboratorio](../security-p03a/VALIDACION-ANDROID-PENDIENTE.md) y [el plan P0.4a](../security-p04a/ANDROID-COMPATIBILITY.md).

Revisión requerida antes de fusionar este PR; no iniciar P0.4c ni Paso4.
