# P0.3c — Auditoría de servicios de traducción y plan de independencia

FlexyGram 1.0, creado y dirigido por **@Lukhou23**. Se conservan los créditos originales. Fecha: 19 de octubre de 2026. **Solo auditoría/documentación; ningún motor, dependencia, ajuste, interfaz o servicio se modifica.**

## Integración de P0.3b y evidencia preservada

PR #7 comprobado en `03e4e27e3a59b79b05f3b99b6fdee7d48709bc16`, dirigido a develop, un commit/25 archivos y sin cambios inesperados; marcado listo para revisión y fusionado por autorización del responsable, mediante merge commit **`5443f15ac61309bc9bfc9a8f81d0d028e9479923`**. Padres: develop `3f95ed2826c5316e11b0380a0f731b21505033c0` y el SHA aprobado. Su árbol `aab7e88c522c1df18bd3f028b9eb40fd9ec431af` coincide exactamente con el árbol validado.

La rama de esta auditoría, `security/paso-3-p03c-translation-audit`, parte de esa integración. **El commit documental de esta rama no se presenta como el commit compilado.** El código que pasó las 26 pruebas y Gradle ARM64 con JNI/Chaquopy, sin SKIP, sigue identificado exclusivamente como `03e4e27…`.

Se recuperó el archivo original `FlexyGram-P03b-PR7-evidencias-03e4e27.zip`, SHA-256 `c385a24aba868a4485ae6dd70e5d461fdbce7509ebf61eaa0f44a3669abb1e39`, y se verificaron CRC, hashes internos y asociación al SHA. [Logs reales y resultados originales conservados](../security-p03b/evidence/validated-03e4e27/README.md): **26/26**, 0 omisiones; **BUILD SUCCESSFUL 9m55s**, 244 tareas, JNI y Chaquopy incluidos. No se repiten compilaciones ni se reconstruyen logs. La APK interna validada tenía SHA-256 `bd4223a37ca463b33fb98c07b16433746e82468cf9743abbba1a0732f965d7f7`; no se recupera, instala ni distribuye aquí.

## Alcance, método y certeza

Lectura estática de fuentes fijadas en el merge, comparación de blobs con Exteraless original `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`, inspección de POM/manifest y bytecode de la dependencia Maven exacta. Su AAR descargado desde Maven Central tiene SHA-256 `08cdf350bd21b6cc063a8fb0141eed6cdf06c06772c5080ca38114dce07a8f27`, coincidente con el registrado durante la compilación validada; también se verificó el checksum publicado.

No se usaron las claves, no se consultó API Keys/Google Cloud Console, no se enviaron textos a traductores ni solicitudes a Telegram. Solo se recuperaron repositorio, documentación oficial y artefactos públicos de compilación. No se contactó a responsables de servicios ni se utilizaron cuentas personales. Todos los valores de claves quedan fuera del informe y de las evidencias nuevas.

## Inventario técnico y procedencia

| Elemento | Origen comprobado | Funcionamiento y dependencias |
|---|---|---|
| `tw.nekomimi.nekogram.translate.source.GoogleTranslator` | Fuente de la base Exteraless; blob `91147b27e920c298de8307b19a4ca203e278d6cd`, idéntico al original. El namespace Nekogram no identifica por sí solo al autor/commit upstream original. | Implementa Translator; usa OkHttp/HttpUrl, org.json, coroutines y cliente HttpClient del proyecto. Convierte entidades a HTML con HTMLKeeper; reconstruye TLRPC/TranslateAlert2 y ajusta saltos de línea en chino. |
| `app.nekogram.translator.GoogleAppTranslator` | AAR `app.nekogram.translator:translator:1.6.1`, ya declarado en la base original. POM declara Nekogram como desarrollador, SCM `https://github.com/Nekogram/translator` y licencia GPLv3. | Extiende BaseTranslator; singleton getInstance/translate/translateImpl; parámetros de idioma/modelo, token de solicitud calculado localmente, OkHttp y parseo Gson. Retorna Result.translation/sourceLanguage; wrapper Java usa translation. |
| Dependencias declaradas del AAR | POM recuperado del artefacto 1.6.1, no una versión arbitraria nueva. | Kotlin stdlib 2.2.10 (compile), Gson 2.14.0 y OkHttp 5.4.0 (runtime). Son versiones declaradas; no una afirmación sobre todas las resoluciones finales transitivas. Manifest de biblioteca: minSdk21, sin services/receivers/providers ni permisos propios. |
| Cliente HTTP local | `tw.nekomimi.nekogram.utils.HttpClient` | connectTimeout15s, readTimeout0, writeTimeout10s, callTimeout30s; ejecución asíncrona y cancelación de Call.await. No se cambiaron tiempos ni rendimiento. |
| Cliente HTTP de biblioteca | Helper obfuscado `app.nekogram.translator.b` | Construye su propio OkHttpClient si no se ha proporcionado uno por sus campos estáticos; execute síncrono; tratamiento especial de 429; retorna body/string, parseado después. No se supone que hereda los timeouts/cancelación del cliente local. |
| Otros consumidores del AAR | `RealMicrosoftTranslator`, `fallback/DeepLTranslatorNeko` | También importan clases de esta dependencia. Retirar el AAR completo a ciegas puede romper funciones ajenas al hallazgo Google. |

**Límite de procedencia de la biblioteca:** el sources.jar publicado contiene únicamente META-INF/MANIFEST.MF, sin código. El repositorio SCM declarado no pudo recuperarse públicamente en este entorno. Se auditó bytecode del AAR exacto; no se atribuye una revisión fuente verificable al binario ni se afirma reconstrucción reproducible upstream. La licencia de código declarada no acredita autorización para usar las claves o los servicios.

## Ruta efectiva de ejecución y fallbacks

No confundir la clase local `tw.…GoogleAppTranslator` con la clase de biblioteca `app.…GoogleAppTranslator`.

1. `Translator.translateBase` selecciona `providerGoogle = 1`; `NekoConfig.translationProvider` tiene valor inicial 1. Entradas de traducción de texto, entidades, encuestas, artículos y con contexto pasan por este selector. `getBulkTranslateProvider` además remapea DeepL a Google en ciertas traducciones de conjunto.
2. El wrapper local `source/GoogleAppTranslator.kt` comprueba primero `NaConfig.googleTranslateExp`, **true por defecto**. Si está activo llama a **GoogleTranslator**, el primer hallazgo.
3. GoogleTranslator intenta su petición; ante RuntimeException registra un error con Throwable y llama a `fallback.GoogleTranslatorNeko`, que ejecuta el **GoogleAppTranslator del AAR**, segundo hallazgo. Es un fallback automático, no una autorización independiente del servicio.
4. Si el modo experimental está desactivado, el wrapper comprueba la preferencia `GoogleCloudTransKey`; si está presente usa GoogleCloudTranslator, que apunta al endpoint público Cloud Translation v2. **En el orden actual, una clave propia puede quedar ignorada mientras el modo experimental siga activo.**
5. Sin experimental ni clave configurada usa el endpoint web `translate.google.com/translate_a/single`, con User-Agent de Google Translate. No contiene esas dos claves, pero no se considera por ello un servicio autorizado para una beta ni una alternativa aprobada automáticamente.

Los blobs del wrapper y del fallback Java también coinciden con la base original; no son regresiones introducidas en P0.1–P0.3b. Véase [source-provenance.json](evidence/source-provenance.json).

## Solicitudes, claves e identidad

| Propiedad | Integración local GoogleTranslator | Integración del AAR GoogleAppTranslator |
|---|---|---|
| Endpoint observado | HTTPS `translate-pa.googleapis.com/v1/translate` | Mismo host/path PA |
| Datos enviados | Texto/HTML, idiomas, opciones cliente, clave en query de una petición GET | Texto, idiomas/modelo y parámetros cliente; GET o POST form con método override, según tamaño. Puede incluir texto en URL. |
| Clave | Literal cliente heredado, etiqueta de auditoría **A**, en parámetro key | Otro literal cliente heredado, etiqueta **B**, en header x-goog-api-key |
| Identidad declarada | User-Agent de navegador Chrome; sin X-Android-Package/Cert en la construcción inspeccionada | User-Agent GoogleTranslate y **X-Android-Package de Google Translate**, más una huella X-Android-Cert fija ajena a FlexyGram |
| Estado de autorización | No demostrada | No demostrada; identidad ajena confirmada en bytecode |

Las etiquetas A/B no son valores ni referencias a claves nuevas. Las evidencias previas identifican ambas en classes20.dex/GoogleTranslator.translate y classes35.dex/GoogleAppTranslator.translateImpl del APK validado.

**Hechos:** son claves cliente embebidas, extraíbles y distintas; no son API Hash de Telegram, claves de sesión ni archivos de service account. El AAR declara una identidad de otra aplicación en la solicitud. El código usa un endpoint PA, diferente del endpoint público documentado Cloud Translation v2. No se encontró aquí una configuración FlexyGram aprobada que autorice esas rutas.

**Inferencia limitada:** los headers de identidad ajena son compatibles con un servicio que espera restricciones de aplicación, pero no prueban cuáles están vigentes ni quién controla el proyecto. El primer cliente, que no añade esos headers, tampoco demuestra que su clave carezca de restricciones. No se infiere propietario, proyecto, cuota, facturación, vigencia o permiso de redistribución a partir de un literal/namespace.

**Pendiente imposible de resolver con esta inspección:** clasificación administrativa exacta, APIs habilitadas y restricciones de paquete/certificado/proyecto solo se pueden acreditar por el titular autorizado mediante consola/registro de configuración y documentación del servicio. No se solicita acceso a proyectos ajenos ni se prueban sus claves. Aun si una clave estuviera difundida públicamente o técnicamente aceptara solicitudes, eso no demostraría autorización para FlexyGram.

Google documenta restricciones por aplicación y API, y para Android la combinación paquete + SHA-1 del certificado [S1]. Sus guías recomiendan evitar claves en URL/código cliente y mantener las credenciales en el servidor [S2]. No se promete que sustituir los headers por el paquete FlexyGram haga compatible o autorizada una clave heredada.

## Riesgos confirmados y potenciales

| Hallazgo | Evidencia / límite | Prioridad propuesta antes de beta |
|---|---|---|
| Dependencia de dos claves no acreditadas | Confirmada en fuente/bytecode y escaneo anterior. No prueba actividad real en Diagnostic. | Bloquear su utilización y retirar sus valores de futuros artefactos autenticables mediante cambio revisado. |
| Identidad Google Translate en biblioteca | Confirmada en headers/UA del bytecode exacto. Restricciones servidor desconocidas. | No conservar como mecanismo de autorización de FlexyGram; sustituir la integración. |
| Selector experimental precede a clave propia | Orden y valor inicial confirmados. | Diseñar selección basada en autorización/capacidad; una configuración propia no debe caer en ruta heredada. |
| Fallback automático no autorizado | Catch RuntimeException → biblioteca; ruta web sin clave como otro camino del wrapper. | Fail-closed por proveedor, también en entradas directas, artículos/encuestas y remapeos DeepL→Google. |
| Texto/clave en URL y errores con datos sin filtrar | GET local confirmado; el fallback y parseo pueden generar excepciones con body/error. FileLog.e(label, Throwable) puede registrarlas cuando el logging esté habilitado. | Diagnósticos estructurados sin URL/query/headers/body/texto; sanitizar mensajes de error. No se afirma que se haya registrado una clave o conversación real. |
| Procedencia fuente del AAR incompleta | Sources jar vacío; bytecode parcialmente obfuscado, SCM no recuperado. | Obtener fuente verificable/licencia y reproducibilidad antes de mantener un fork. No eliminar otros proveedores indiscriminadamente. |

Ninguno de estos hallazgos establece que las claves Google causaran el incidente de sesiones Telegram. No se efectuaron pruebas de cuenta ni llamadas reales.

## Alternativas para conservar traducción sin credenciales ajenas

| Alternativa | Conservación de funciones | Costes y límites / autorización |
|---|---|---|
| **Servicio FlexyGram con proveedor oficial — recomendada** | Mantener interfaz Translator, selección de idioma, textos/entidades, HTMLKeeper y flujos actuales; adaptar entrada/salida a API pública v2/v3 con proyecto propio. | Backend propio añade operación, cuotas y coste; revisar cobertura lingüística, HTML, privacidad y consentimiento. Credenciales de servidor fuera del APK; IAM mínimo, cuota/rate limit y control de abuso. No es proxy abierto. |
| Clave propia por usuario o por variante en API pública v2 | Aprovecha la ruta GoogleCloudTranslator existente tras revisar orden, políticas y errores; no exige clave ajena ni cambio de interfaz inicial. | Una clave en APK/prefs no es secreta por estar fuera de Git; restricciones y alcance deben acreditarse. BYOK no equivale a configuración propia validada ni a solución lista. No portable mediante backup. |
| ML Kit en dispositivo, opcional posterior | Traducción local después de descargar modelos; evita enviar el texto a traductor remoto. | Descargas iniciales y espacio, cobertura/calidad diferentes, límites en idiomas no ingleses y atribución [S5,S6]. No mantiene automáticamente equivalencia con el motor actual; no añadir SDK/modelos ni descarga a Diagnostic. |
| TelegramAPITranslator existente, en futura variante autorizada | No necesita esas claves Google y ya devuelve TLRPC/entidades en la arquitectura. | Requiere autenticación Telegram propia y está prohibido activarlo en Diagnostic. No se promete cobertura, cuota ni paridad: la API documenta restricciones/errores y condiciones de entidades [S7]. No habilitarlo como fallback silencioso. |

No se recomienda sustituir los dos literales por otras claves encontradas en Internet, usar las identidades del AAR, convertir el endpoint PA en proxy con credenciales ajenas, ni adoptar una ruta web solo porque no pide clave.

## Propuesta concreta para implementación posterior, sujeta a revisión

1. **Elegir contrato de servicio y aprobación:** proyecto/proveedor bajo control de @Lukhou23, identidad de futura variante autenticable, responsable de coste/cuota, autorización y política de datos. Recomendación: backend FlexyGram + API oficial; v2 admite API keys, v3 usa autenticación admitida y no API keys [S3,S4]. Preferir identidad de workload/credenciales servidor gestionadas, nunca service account privada dentro del APK.
2. **Añadir una política de traducción propia sin tocar la UI:** denegar siempre en Diagnostic, denegar sin proveedor/configuración autorizados, endpoint fijo permitido, separación de credenciales y preferencias. Mantener P0.1–P0.3b; no usar sesión Telegram como credencial del backend sin un protocolo independiente revisado. Ausencia/expiración devuelve error local seguro, sin consulta al proveedor heredado.
3. **Conservar contratos funcionales:** reemplazar únicamente adaptadores Google y sus fallbacks, mantener Translator/HTMLKeeper/TLRPC y comprobar preservación de formato. Priorizar configuración autorizada sobre flags experimentales. Aplicar policy también a rutas directas, remapeos de proveedor y colas/reintentos. No asumir paridad de traducción o cobertura hasta verificarla.
4. **Sanear sin destruir otros motores:** desactivar y retirar ambos literales y la identidad ajena de artefactos futuros. Para el AAR, preferir fuente verificable y fork mínimo reproducible, o reemplazar sus adaptadores afectados manteniendo Microsoft/DeepL y créditos; no parchear binarios opacos ni excluir la dependencia completa a ciegas. Si no se obtiene fuente suficiente, documentar migración de esos consumidores antes de retirar el AAR. Mantener el escáner genérico informando dos hallazgos hasta su eliminación efectiva.
5. **Privacidad, almacenamiento y fallos:** texto en body HTTPS del contrato propio, sin contenido en logs; redactar errores/respuestas/URLs. No registrar tokens servidor, no exportar/importar claves mediante respaldos, no copiar datos Exteraless. La política allowlist P0.3a no permite GoogleCloudTransKey; no ampliar a credenciales para facilitar migración. Elegir almacenamiento seguro/rotación para futura configuración; una preferencia exportable solo selecciona opciones no secretas.
6. **Pruebas antes de habilitar:** fixtures sintéticos + MockWebServer de laboratorio, cero servicios externos. Verificar Diagnostic sin llamadas incluso mediante invocación directa; falta de configuración/errores/403/429/timeout/cancelación sin fallback heredado; precedencia y scope/rotación, backups sin credenciales, UTF-8/emojis/HTML/entidades/nuevas líneas/idiomas/artículos/encuestas y otros motores conservados; logs sin canarios ni body/URLs. Escaneo APK debe confirmar ausencia de ambas claves/identidad ajena; regresiones de 26 pruebas y compilación JNI/Chaquopy completa cuando se implemente. No se declara esto ejecutado en P0.3c.
7. **Validar servicio propio solo tras aprobación separada:** primero entorno de desarrollo autorizado y texto ficticio, sin cuentas personales; aceptar cuotas y políticas de datos. No desbloquear beta hasta completar laboratorio Android, restauración y 16 KB.

**Recomendación:** aprobar primero la política y el contrato oficial con backend propio, luego autorizar un cambio mínimo de adaptadores. Conservar los puntos de entrada funcionales y exigir paridad mediante fixtures. No habilitar traducción heredada ni autenticación por completar esta auditoría.

## Estado y límites al detenerse

Solo se añaden documentos y evidencias. No se recompiló el commit documental, no se alteran motores, navegación, animaciones, rendimiento, actualizador, dependencias, manifiesto o guardas. Diagnostic sigue sin INTERNET, sin autenticación, sin push/FCM. Main permanece protegida en `db1bea24b7b705de33f8ff8c8e174011c153cac7`; PR #2 abierto. Sin habilitar Actions, instalar/distribuir APK o publicar Releases. No se inicia P0.4 ni Paso 4.

**Bloqueos que siguen abiertos:** instalación y primer arranque Android offline, cierres/Logcat, permisos/componentes y tráfico por UID en ejecución, no restaurar cuentas/sesiones ni credenciales (incluidos framework/OEM), carga JNI/Python y páginas reales de 4/16 KB. Zipalign y compilación no resuelven incompatibilidades ELF ni sustituyen esas pruebas. Se conserva [la validación pendiente de laboratorio](../security-p03a/VALIDACION-ANDROID-PENDIENTE.md). También quedan autorización del servicio de traducción, fuente de dependencia y correcciones de esta propuesta, configuración propia Firebase/push y rotación/cachés reales para la futura beta.

## Fuentes primarias consultadas

- [S1: restricciones de API keys, paquete y certificado Android](https://docs.cloud.google.com/api-keys/docs/add-restrictions-api-keys).
- [S2: buenas prácticas para API keys: repositorios, URL y servidor](https://docs.cloud.google.com/docs/authentication/api-keys-best-practices).
- [S3: autenticación Cloud Translation Basic/Advanced](https://docs.cloud.google.com/translate/docs/authentication).
- [S4: API pública Cloud Translation v2](https://docs.cloud.google.com/translate/docs/reference/rest/v2/translate).
- [S5: ML Kit Translation y sus límites](https://developers.google.com/ml-kit/language/translation).
- [S6: ML Kit Android, modelos y ciclo de vida](https://developers.google.com/ml-kit/language/translation/android).
- [S7: Telegram messages.translateText](https://core.telegram.org/method/messages.translateText) — documentación únicamente; no se ejecutó el método.
- [POM publicado 1.6.1](https://repo.maven.apache.org/maven2/app/nekogram/translator/translator/1.6.1/translator-1.6.1.pom) y [AAR](https://repo.maven.apache.org/maven2/app/nekogram/translator/translator/1.6.1/translator-1.6.1.aar) — descarga de dependencia, no operación del traductor. No se redistribuyen claves ni binario en esta auditoría.
