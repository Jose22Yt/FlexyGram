# P0.3d — protección de ejecución de traducción

FlexyGram 1.0, responsable **@Lukhou23**. Créditos y licencias originales conservados. 19 de octubre de 2026.

## Integración y alcance

PR #9 verificado en `7385e7541023f29ba8e669c9bd184721cde44aaa`, dirigido a develop y limitado a 14 archivos bajo tests/translation_safety/ y docs/translation-safety-preparation/. Estaba en borrador: se marcó listo y se fusionó con autorización exclusivamente en develop mediante **`333dd8c9beb35a2e3caa985279858df7b5bc2ee7`**. Esta implementación parte de ese commit, en `security/paso-3-p03d-translation-runtime-policy`.

Este cambio conecta una política **real Java/Android**; no es el modelo Python anterior ni un motor C++ nuevo. No habilita proveedores, backend, Telegram autenticado, Firebase, push, ML Kit ni Internet. No modifica diseño, navegación, animaciones, reproductor ni optimizaciones.

## Protección aplicada

| Punto real | Cambio |
|---|---|
| translate/TranslationServicesPolicy.java | Clase final sin setters, preferencias, claves ni grants mutables. Denegación por defecto de todos los IDs/rutas; Diagnostic no puede habilitarse mediante un ajuste. Códigos fijos de error, sin mensaje/cause/toString del proveedor. Conserva tipos UnsupportedOperationException y SecurityException al sanear. |
| Translator.kt: translateBase y APIs callback | Autoriza antes de seleccionar adaptador y antes/después de ejecutarlo; comprueba cancelación. Captura la selección antes de encolar; errores callback seguros y cancelación repropagada. getBulkTranslateProvider devuelve el proveedor original: DeepL no se convierte en Google. |
| source/GoogleTranslator.kt | Guarda tanto doTranslate como el constructor privado de solicitudes PA antes de formar URL/petición. Error terminal seguro; se retira la transición automática al wrapper Google del AAR. Se conserva el motor y su código heredado para revisión de procedencia. |
| source/GoogleAppTranslator.kt y GoogleCloudTranslator.kt | Guarda doTranslate antes de preferencias, HTML o solicitudes; guarda adicional en la ruta web. Presencia de una clave o flag experimental no concede autorización. Errores HTTP/JSON/red no incorporan body/URL/texto; cancelación no se convierte en fallo/reintento. |
| source/fallback/GoogleTranslatorNeko.java | Deniega antes de getInstance/translate del AAR, incluso invocación directa. No se borra ni parchea el binario. |
| source/LLMTranslator.kt | Deniega antes de leer configuración o preparar texto/contexto y en cada intento, además de doLLMTranslate. Elimina sus tres fallbacks Google; reintenta únicamente el mismo motor y repropaga cancelación. Retira logs de mensajes/prompt/modelo y sufijos de claves; no propaga respuestas privadas como errores. |
| parts/MessageTrans.kt | Deniega antes de usar caché, extraer contexto o preparar trabajos. Guardas adicionales en translateSingleMessage, translateText y rich content. Rich content utiliza el proveedor fijado, también al reintentar; no fuerza Google ni vuelve a provider=0. Limpia marcadores al fallar y no reintenta denegaciones ni convierte cancelación en diálogo de error. |
| Otros adaptadores | Guardas al comienzo de doTranslate de Yandex, Lingo, Microsoft, RealMicrosoft, DeepL, Telegram y TranSmart; también wrapper DeepL del AAR. Clientes HTTP/singletons diferidos hasta después de autorización. Evita que una llamada directa eluda el control central. |

**No existe todavía un resolver de autorización aprobado. Por ello ninguna traducción a través de estos adaptadores está disponible, también fuera de Diagnostic mientras carezca de una integración autorizada.** Esta indisponibilidad es explícita: no se sustituye por otro proveedor, no se oculta una función eliminándola y no se presenta como un cliente listo para beta.

Los ajustes, idiomas y preferencias siguen presentes; seleccionan un proveedor, pero no acreditan derecho a usarlo. Recuperar traducción requiere una integración oficial revisada, autorización verificable, transporte y tratamiento de datos aprobados y nuevas pruebas; no basta con cambiar false a true ni con pegar una clave. No se implementa esa integración aquí.

## Compatibilidad conservada y límites

Se mantienen las firmas públicas de Translator y sus callbacks, HTMLKeeper, TLRPC, tipos de entidades y opciones existentes. Microsoft/RealMicrosoft, DeepL y sus wrappers continúan presentes; **la declaración y el AAR compartido app.nekogram.translator:translator:1.6.1 se conservan**. Se añaden guardas y se difiere la inicialización, no se reemplazan algoritmos ni formateadores. La comprobación de hashes contra la base preserva build.gradle, HTMLKeeper y TLRPC. Esto acredita conservación e integración de código, no paridad lingüística ni disponibilidad de servicios remotos.

El aislamiento anterior (identidad, API 0/hash vacío, MTProto, sesiones, respaldo, plugins, manifest/push) permanece sin cambios de producción. Los errores saneados no conservan causas privadas. Otros adaptadores denegados (por ejemplo Lingo y TelegramAPI) y clientes de red LLM aún conservan trazas o errores heredados que deberán revisarse antes de cualquier habilitación; este cambio no los declara saneados ni autorizados. No se garantiza el saneamiento universal de bibliotecas, plugins arbitrarios o caminos nuevos: la autorización predeterminada sigue cerrada y Diagnostic conserva la prohibición de red.

## Pruebas reproducibles

Requisitos de laboratorio: JDK 21, Python 3.11, Gradle 9.7.1/lib con Groovy/Kotlin 2.4.0/coroutines, Gson 2.14.0 disponible. Variables KOTLIN_LIB, GRADLE_USER_HOME y GSON_JAR solo señalan herramientas locales, no credenciales.

```sh
python -m unittest discover -s tests/security -v
python -m unittest discover -s tests/translation_safety -v
python -m unittest discover -s tests/translation_runtime -v
python tests/translation_safety/inventory.py
```

- Suite previa: 26 pruebas de P0.1/P0.2/respaldo/push, sin debilitar sus controles.
- Preparación: 27 pruebas; se conserva el modelo aislado y el scanner. El inventario se actualiza explícitamente de **59 llamadas/24 archivos a 55/22**: desaparecen las tres llamadas LLM→Google y la llamada PA→Google del AAR. Las dos fuentes dejan de figurar como consumidores léxicos de ese patrón; sus entradas directas están cubiertas por las nuevas pruebas. No se eliminan motores para reducir el conteo.
- Se reemplaza la aserción histórica de tres fallbacks/Google forzado/línea fija por ausencia de fallbacks y proveedor explícito de rich content. preserved_sources.json conserva hashes previos y nuevos en p03d_reviewed_changes para las modificaciones autorizadas; las demás fuentes siguen comprobándose byte a byte. No se regenera automáticamente en tests.
- Nueva suite: compila y ejecuta la política Java real, DiagnosticPolicy real y ambos wrappers Java completos con dobles de biblioteca que cuentan inicializaciones/llamadas. Prueba Diagnostic true y false, IDs desconocidos y todas las rutas, 20 intentos por wrapper y errores con canarios privados.
- Extrae cuerpos completos reales de translateBase, getBulkTranslateProvider, LLM.doTranslate, PA.doTranslate, translatePoll (incluida encuesta vacía), MessageTrans.translateText/rich/error handler. Los compila con Kotlin, ajustando únicamente las cabeceras del envoltorio de prueba (visibilidad/override) y proporcionando dobles Android/HTML/TLRPC/transporte. Con política real: cero operaciones de proveedor. Con **doble de política exclusivo del arnés**: comprueba preservación de proveedor/entidades, fallos terminales, 3 intentos del mismo LLM, agotamiento/429, cancelación y rich/retry sin Google. Este doble nunca se incorpora a src/ ni al APK.

Las pruebas no ejecutan ART, emulador, aplicación, cuentas, sesiones, revocaciones ni peticiones Telegram/Google. El transporte del arnés es local y ficticio. No equivalen a una prueba real de traducción o compatibilidad en el Poco.

Resultados finales, compilación, manifiesto y escaneos: véase **[evidence](evidence/)** y el resumen de validación. Los informes anteriores son históricos y conservan su identidad; no se atribuye su APK ni sus resultados a esta rama.

## Resultado final de validación

- **57 pruebas aprobadas, 0 fallidas, 0 omitidas:** 26 de seguridad anterior + 27 de preparación actualizada + 4 nuevas pruebas con escenarios Java/Kotlin ejecutables. Se repitieron las tres suites sobre la fuente definitiva. Además, 10 mutaciones inseguras del manifiesto real fueron rechazadas.
- **Gradle completo ARM64/JNI/Chaquopy: BUILD SUCCESSFUL, exit 0, 11m 3s.** Tras añadir la guarda de encuesta vacía se recompiló y empaquetó la fuente definitiva: **BUILD SUCCESSFUL, exit 0, 1m 41s**, 244 tareas (9 ejecutadas/235 actualizadas), sin excluir JNI ni Chaquopy. Los binarios nativos sin cambios se reutilizan tras haberse compilado en la primera ejecución exitosa.
- La repetición final usa `-Pkotlin.incremental=false` solo en la línea de comandos. La incremental anterior falló con declaraciones duplicadas de extensiones existentes de Locale; se confirmó una sola definición en la fuente y la compilación no incremental pasó. No se parchearon esas funciones ni se modificó gradle.properties. Se conserva el fallo, sin atribuirlo de manera concluyente a una versión concreta de AGP/Kotlin.
- Un intento anterior falló en buildChaquopyRuntimeArm64V8a porque el script no encontraba CMake en su ruta predeterminada. Se estableció CMAKE al SDK 3.31.6 instalado; no se modificó el script ni el submódulo. El bootstrap también requirió preaprovisionar el Wrapper exacto y el JDK JetBrains declarado debido a descargas Java fallidas. Entorno y logs disponibles en evidence/.
- Verificación de clases Android reales: guardas en **17 clases**, incluidas las continuaciones de translatePoll y translateWithContext. Política incluida en DEX; BuildConfig compilado con API ID 0, hash vacío y aislamiento true. Esto es inspección estática del artefacto, no ejecución de Android.
- APK interna: **SHA-256 `61df6a92ea6a4e439405574d01bf130826ba98e3322065f3fbcc92c2eac644ff`**, 115605531 bytes; identidad FlexyGram Diagnostic y paquete propio, firma Debug v2 válida de laboratorio, 18 bibliotecas instalables AArch64 y CRC correcto. No instalada ni distribuida. No se dispone de la clave efímera de las compilaciones anteriores: se generó otra local fuera de Git; no es firma definitiva ni se afirma continuidad de actualización con APK previas.
- Manifiestos fusionado y binario: **sin INTERNET**, allowlist diagnóstica de permisos/componentes conservada. El escaneo del APK terminó completo, con **2 claves conocidas distintas**, 1 marcador de paquete ajeno y 1 de certificado ajeno, y 0 google-services.json embebidos. **passed=false/exit 1 es el bloqueo esperado de distribución**, no un resultado limpio ni un fallo de pruebas que se haya ocultado.
- AAR verificado sin cambios: SHA-256 `08cdf350bd21b6cc063a8fb0141eed6cdf06c06772c5080ca38114dce07a8f27`. No se eliminaron clases de Google ni dependencias de Microsoft/DeepL.

Comprobación reproducible del APK, sin instalarlo:

```sh
python tests/translation_runtime/check_artifact.py ARCHIVO.apk --aapt2 RUTA_AAPT2 --classes RUTAS_CLASSES
# Código 1 esperado mientras estén las claves heredadas.
```

Los hashes de fuentes se verificaron tras la compilación. Los logs normalizan rutas locales y omiten la línea de configuración del proxy; no contienen contraseñas de firma ni claves privadas. Compilación y pruebas no equivalen a validación ART, Logcat, tráfico por UID o comportamiento en el Poco.

## Bloqueo para distribución

Las **dos claves cliente heredadas** permanecen en el código/dependencia, junto con marcadores de identidad ajenos de la biblioteca. El escaneo debe seguir señalándolas; un resultado passed=false es esperado y no se oculta. Guardar una huella no verifica propiedad, restricciones o vigencia; no se realizan pruebas online de claves.

**No aprobar una beta distribuible mientras sigan presentes**, aunque los caminos estén denegados y el manifiesto carezca de INTERNET. La futura retirada requiere procedencia/fuentes verificables y una construcción revisada del módulo compartido que mantenga Microsoft/DeepL, o una sustitución autorizada con pruebas de paridad. No borrar clases/holders ni editar arbitrariamente el AAR. No se decide ni implementa ese reemplazo en P0.3d.

Pendientes: pruebas Android reales offline de arranque, callbacks/cancelación/Logcat y tráfico por UID; revisión del scope/pinning de reintentos de todos los consumidores y de cachés por cuenta/proveedor antes de habilitar traducción; procedencia y retirada de claves/identidad; autorización, privacidad y contratos de cada futura integración. Continúan pendientes los requisitos previos de autenticación y compatibilidad ELF/páginas de 16 KB. No se instala ni distribuye APK; P0.4 y Paso 4 no se inician.
