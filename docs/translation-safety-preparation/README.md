# Preparación segura de traducción — diseño para revisión

FlexyGram 1.0, creado y dirigido por **@Lukhou23**. Créditos originales conservados. 19 de octubre de 2026.

**Estado: propuesta, inventario y herramientas aisladas de prueba. No cambia ningún motor ni política de ejecución de la aplicación. No implementa backend, API Telegram ni traducción local.** Las claves originales aún permanecen en la fuente/dependencia; las herramientas nuevas las detectan, no las eliminan ni las hacen autorizadas.

## Cierre aprobado de P0.3c y continuidad

PR #8 verificado en **`e4c6a07f2856054ae432daeaf2639c7fd55ee31d`**, hacia develop, con 25 archivos exclusivamente bajo docs/. Marcado listo y fusionado con autorización en develop: **`2cc41769339d9689498c5f23b446f4cfdf3ad8c0`**. Esta rama, `security/paso-3-translation-safety-preparation`, nace de esa integración.

Se conservan [auditoría P0.3c](../security-p03c-translation-audit/README.md) y [evidencias reales originales P0.3b](../security-p03b/evidence/validated-03e4e27/README.md): 26/26 y ARM64/JNI/Chaquopy exitoso se refieren a **`03e4e27e3a59b79b05f3b99b6fdee7d48709bc16`**, no al merge documental ni a esta nueva preparación. No se recompiló ni repitió esa suite aquí. La nueva suite aislada tiene **27 pruebas**, identificadas por hashes de sus archivos en isolated-tests.result.json.

## Inventario de ejecución directa e indirecta

[Inventario máquina](../../tests/translation_safety/callsites.json): **59 llamadas léxicas en 24 archivos**, con líneas y SHA-256 de las fuentes; [verificador](../../tests/translation_safety/inventory.py) rechaza cambios sin revisión explícita del snapshot. El análisis elimina comentarios/strings antes de buscar llamadas Kotlin/Java y conserva posiciones. No es una prueba universal de alcanzabilidad: reflexión, generación, plugins o nuevas dependencias requieren revisión separada. No se ejecutaron estos caminos sobre Android.

| Superficie | Entradas y rutas observadas | Borde futuro que debe revisar autorización |
|---|---|---|
| API central | Translator.translate: overloads/callbacks/suspend; translateBase; translateWithContext; translatePoll; translateArticle | Antes de seleccionar adaptador y también antes de ejecutar tareas/reintentos; no confiar en la preferencia del usuario como autorización. |
| Mensajes, historias y encuestas | TranslateController; NekoDelegateFragment; MessageTrans; DialogTrans | Texto, entidades, pregunta/respuestas/solución, resúmenes e historias. Respetar cancelación y no guardar resultados parciales bajo proveedor/scope incorrectos. |
| Contenido enriquecido | MessageTrans.translateRichMessageContent, línea 389 | **Fuerza providerGoogle**, con trabajo paralelo y caché, aunque se haya seleccionado otro motor. No confundir con selección por longitud del texto. |
| Artículos | ArticleTrans → Translator.translateArticle | Proveedor separado o general; remapeo mediante getBulkTranslateProvider. |
| Remapeo por capacidad | getBulkTranslateProvider remapea DeepL a Google; utilizado por contexto, encuestas y artículos | Capacidad no disponible debe producir error local o selección explícita autorizada; no caer silenciosamente a Google. |
| Escritura, compartir y adjuntos | ChatActivityEnterView, EditTextCaption, ShareAlert, DialogsActivity, ChatAttachAlert y TranslatorUtils | Hay reintentos con provider=0 que vuelven a resolver el proveedor predeterminado. Fijar elección/scope para cada operación, revalidar antes de ejecutar. |
| Texto de medios/documentos | PhotoViewer, PhotoPickerActivity, PhotoAlbumPickerActivity, DocumentSelectActivity | Selección de proveedor y reintentos al predeterminado; preservar callbacks sin invocar rutas no autorizadas. |
| Selección/transcripción | TextSelectionHelper y TranscribeButton | Selección LLM/predeterminado también puede alcanzar fallback Google. |
| LLM | LLMTranslator: tres llamadas directas a GoogleAppTranslator.doTranslate (153,163,169) | Fallback por agotamiento de errores de red, excepción general o fin de reintentos. El control solo en Translator.translateBase sería insuficiente. |
| Wrapper Google local | source.GoogleAppTranslator: flag experimental → GoogleTranslator; si no, clave Cloud configurada → GoogleCloudTranslator; si no, endpoint web | El experimental es true por defecto y precede a la clave propia. Las tres rutas necesitan política; quitar una clave no autoriza la web. |
| Primer motor afectado | GoogleTranslator.translate/doTranslate → GET PA con clave A; RuntimeException → GoogleTranslatorNeko | Guardar la entrada directa y la transición al fallback; no capturar cancelación para provocar otra petición. |
| Segundo motor afectado | GoogleTranslatorNeko → app.nekogram.translator.GoogleAppTranslator.getInstance/translate/translateImpl | AAR 1.6.1: clave B e identidad de Google Translate. No se hereda autorización por usar un wrapper Java. |
| Biblioteca binaria | Referencias de constant pool a GoogleAppTranslator en sus clases principal/internas y holder obfuscado d | Holder d inicializa singleton GoogleAppTranslator. Estas referencias no prueban que Microsoft/DeepL ejecuten Google; requieren análisis del árbol de retención antes de retirar clases. |

Se incluyeron también el despacho `translator.doTranslate` y las llamadas/fábricas por instancia de la dependencia compartida para cubrir los bordes Microsoft/DeepL. El inventario incluye 29 llamadas Translator.translate, 3 translateWithContext, 2 translatePoll, 1 translateArticle, 8 translateBase, 3 getBulkTranslateProvider y 13 llamadas entre wrappers, motores, despacho por instancia y consumidores compartidos. No se publican parámetros de peticiones ni claves. Véase [referencias binarias del AAR](evidence/aar-google-class-references.json).

## Política propuesta y modelo aislado

[policy_model.py](../../tests/translation_safety/policy_model.py) es una especificación ejecutable en Python, situada **fuera de src/ y sin importación desde Gradle/Android**. No descarga nada, no usa SDK, no lee sesiones, no guarda credenciales y no realiza red. Solo llama adaptadores ficticios de las pruebas. No se presenta como protección ya instalada en la aplicación.

Decisiones propuestas para implementación futura:

1. **Diagnostic deniega toda traducción mediante estos adaptadores**, incluso local opcional, antes de inicializar SDK, consultar servicios o preparar tareas. Identidad diagnóstica e aislamiento son constantes de variante; ningún ajuste, restore o flag experimental concede autorización.
2. **Denegación por defecto:** las tres rutas Google heredadas (local, biblioteca y web) quedan inhabilitadas aunque alguien les proporcione un grant. Proveedor desconocido, configuración ausente, identidad ajena, scope distinto/caducado o capacidad no acreditada producen error local fijo.
3. El resolver confiable futuro debe acreditar proveedor, identidad, scope, vigencia, capacidades y derecho a operar el servicio. En el modelo `rights_verified` es un dato sintético inyectado por pruebas; **no es prueba IAM, una firma ni una preferencia que el usuario pueda habilitar**. El endpoint aprobado debe venir de ese resolver; una cadena con nombre FlexyGram no acredita propiedad. El esquema/verificación real aún no se implementa.
4. Una llamada requiere tanto proveedor autorizado como capacidad soportada. Cambio de proveedor solo con selección explícita asociada al scope y nueva comprobación; **ningún catch, reintento, remapeo DeepL→Google o provider=0 concede ese permiso**. Error/403/429/timeout es terminal para la elección actual; no envía el texto a otro servicio silenciosamente.
5. Revalidar al ejecutar cada trabajo y antes de aceptar callback/cache con scope actual. No cachear una decisión allow; cancelar trabajos al cambiar configuración/cuenta/scope, descartar respuestas obsoletas y no mezclar cachés de texto entre cuentas/proveedores. El modelo verifica el instante de ejecución; la devolución asíncrona/ART y las cachés reales necesitan futura prueba de integración.
6. Para backend oficial: endpoint HTTPS aprobado exacto, sin credenciales en URL/query, sin redirecciones a hosts no aprobados, sin pinzar una identidad de Google Translate. **La política de redirects/TLS real no se modela aún**, debe implementarse en el cliente concreto y probarse con servidor ficticio.
7. Telegram requiere además sesión propia autorizada y condiciones de cuenta/capacidad del método. Modelo local requiere modelo instalado/autorizado; ausencia no descarga ni cae en red. Diagnostic permanece denegado para ambos. No se habilita autenticación en esta etapa.
8. Errores de diagnóstico son códigos fijos, sin URL, headers, body, texto, claves ni sufijos de credenciales. El modelo no propaga excepciones de proveedor ni incluye payload en repr. Futuras implementaciones deben repropagar CancellationException y conservar cancelación/tiempos sin afirmar mejoras de rendimiento.

**Contratos que se preservarán:** Translator y sus callbacks/overloads, HTMLKeeper, TLRPC.TL_textWithEntities, TranslateAlert2, selección de idioma y capacidades de mensajes/encuestas/artículos/medios. La política no traduce ni transforma contenido. Los motores y preferencias actuales permanecen byte a byte iguales en esta preparación; eso conserva P0.1–P0.3b, no acredita autorización para operar todos los servicios de terceros en beta.

## Retirar claves: estrategia reproducible sin romper Microsoft/DeepL

No se acepta esconder, cifrar, trasladar a BuildConfig o fragmentar los literales. Un resultado limpio del escáner tampoco justificaría hacerlo: debe demostrarse su retirada del código y dependencia, con artefacto e inventario reproducibles.

Situación comprobada: `RealMicrosoftTranslator` usa MicrosoftTranslator del AAR; `DeepLTranslatorNeko` usa DeepLTranslator del mismo AAR. El motor DeepL local también conserva una ruta de clave propia/formalidad y una ruta de biblioteca. El AAR tiene sources.jar sin fuentes, código parcialmente obfuscado y el SCM declarado no se pudo recuperar públicamente en P0.3c. **No se propone borrar GoogleAppTranslator.class, su holder o el AAR a mano.**

Estrategia previa a cualquier reemplazo, pendiente de aprobación:

1. Congelar AAR 1.6.1, POM, dependencias transitivas y hashes; generar SBOM y API/ABI pública de BaseTranslator/Result/Google/Microsoft/DeepL y holders. Correlacionar con fuentes mediante commit/tag y una construcción de referencia; licencia/créditos y autorización de servicio se verifican por separado.
2. Obtener fuente correspondiente del publicador por un canal autorizado, o escoger una fuente verificable y auditada para un módulo controlado en este mismo proyecto. No se contacta a terceros ni se crea otro repositorio aquí. Si no se consigue fuente fiable, **bloquear esa vía**, sin declarar el binario opaco saneado.
3. Construir un módulo fuente reproducible con adaptadores separados por proveedor; conservar las firmas y semántica que consumen Microsoft/DeepL, incluida detección de idiomas, códigos zh, errores, formateo y opciones/formalidad soportadas. Implementar la sustitución Google mediante adaptador seguro revisado. Evitar incluir el código/literales/identidad Google retirados y actualizar referencias/holders desde fuente.
4. Comparar la API consumida y ejecutar fixtures de Microsoft/DeepL con transporte falso antes/después, incluyendo idioma no soportado, auto, 429, cancelación, formato y formalidad. No inferir que el resto del AAR queda libre de configuraciones de terceros: requiere revisión antes de beta. No realizar llamadas con sus credenciales heredadas.
5. Si es necesario sustituir también esos consumidores por adaptadores oficiales nuevos, presentar primero su matriz de paridad y requisitos de configuración/autorización propios. Es un cambio funcional adicional y **no está autorizado en esta preparación**. No sacrificar funciones para hacer pasar el scanner.
6. Fijar versiones y checksums de fuentes/herramientas/dependencias, registrar parche mínimo, generar AAR desde fuente y comparar ABI/SBOM/resultados. Desactivar primero las rutas retiradas mediante policy y después excluir sus clases/literales desde esa construcción revisada. R8 puede ayudar a quitar código muerto, pero **no sustituye la prueba de retirada ni la procedencia**.
7. Construcción Android ARM64 completa posterior, JNI/Chaquopy, suite anterior y fixtures de paridad, manifiestos y APK, escaneo genérico + huellas conocidas + marcadores ajenos. Verificar que no quedan las dos claves ni esa identidad y que Microsoft/DeepL siguen presentes y se comportan conforme al contrato. Guardar SHA y herramientas exactos. Ninguno de estos pasos de sustitución/compilación se ejecuta aquí.

La opción de mantener hoy la dependencia intacta es deliberada y segura únicamente bajo el aislamiento vigente de Diagnostic; **no desbloquea una beta autenticable**.

## Comparación de soluciones definitivas

| Alternativa | Funciones y adaptación | Privacidad | Costes y requisitos | Evaluación |
|---|---|---|---|---|
| **Backend propio + API oficial** | Mayor control sobre idiomas, texto/HTML, errores y estabilidad del contrato; adaptador mantiene Translator/HTMLKeeper/TLRPC. Validar paridad de formato, fragmentación y lenguajes; no asumir resultado lingüístico idéntico. | Texto sale del teléfono y lo procesan FlexyGram/proveedor; minimizar contenido/metadatos, sin logs de body, sin caché entre cuentas, retención explícita y consentimiento. FAQ Cloud describe procesamiento/retención propios; no extrapolarla a endpoints PA heredados. | Proyecto y facturación propios, credenciales servidor fuera del APK, IAM mínimo/workload identity, cuota/rate limit y protección contra abuso. Coste por contenido/modelo y destinos, más backend/red/operación; estimación futura = volumen facturable × tarifa vigente + infraestructura. Sin presupuesto/volumen definidos no hay coste mensual fiable. | **Recomendada para mayor paridad y control**, condicionada a revisión del contrato, presupuesto y privacidad. No se implementa/despliega ahora. |
| **API oficial Telegram donde esté permitida** | Integración ya existente y contrato TLRPC cercano; método solo para usuarios, sujeto a idioma/longitud/cuota/disponibilidad. Entidades estilizadas tienen condiciones de cuenta/Premium documentadas; no garantizar reemplazo universal de artículos/texto externo. | Se remite texto a Telegram mediante sesión autorizada; no es traducción local ni preserva automáticamente secreto extremo a extremo. No enviar texto de chats secretos o contenido sensible sin una decisión explícita de privacidad. | No requiere un backend Cloud propio para ese flujo; exige futura autenticación propia, requisitos del servidor y límites vigentes. No prometer gratuidad universal ni saltarse condiciones de cuenta. | Opción complementaria para funciones permitidas; no fallback silencioso. Diagnostic sigue bloqueado. |
| **Local opcional** | Después de disponer de modelos traduce sin enviar texto; ML Kit tiene cobertura/calidad diferentes (50+ idiomas, puentes por inglés), modelos descargables y condiciones de atribución. No prometer paridad con la lista heredada. | Reduce exposición del texto al servidor; descarga inicial/modelos/telemetría del SDK y almacenamiento se revisan por separado. Texto y resultados tampoco deben registrarse localmente. | Espacio, descarga y batería/CPU, mantenimiento/licencia de modelos; puede necesitar preparación de modelos en laboratorio. No instalar SDK, descargar modelos o alterar rendimiento ahora. | Complemento optativo sujeto a evaluación técnica; útil para privacidad/offline, sin convertir ausencia de modelo en envío remoto. |

Fuentes primarias consultadas 19/10/2026: [Cloud auth v2/v3](https://docs.cloud.google.com/translate/docs/authentication), [privacidad Cloud](https://docs.cloud.google.com/translate/data-usage), [precios oficiales](https://cloud.google.com/products/translate/pricing), [Telegram translateText](https://core.telegram.org/method/messages.translateText), [ML Kit y límites](https://developers.google.com/ml-kit/language/translation), [condiciones de uso/atribución ML Kit](https://developers.google.com/ml-kit/language/translation/translation-terms). No se probaron servicios ni credenciales.

## Archivos afectados: preparación actual y propuesta futura

| Ahora, sin conexión con producción | Propósito |
|---|---|
| tests/translation_safety/policy_model.py | Modelo de decisiones y ejecución con adaptador falso. |
| tests/translation_safety/artifact_gate.py + retired_fingerprints.json | Scanner read-only de ZIP/IMY/JAR/DEX/resources UTF-8/UTF-16LE, claves conocidas/genéricas, paquete/certificado ajenos y configuración embebida. Huellas solo para detección, nunca para formar solicitudes. |
| tests/translation_safety/inventory.py + callsites.json | Inventario explícito y control de cambios de rutas. |
| tests/translation_safety/preserved_sources.json | Hashes de motores, HTMLKeeper y fuentes de aislamiento/logs/backup/push que deben seguir intactas en esta preparación. |
| tests/translation_safety/test_preparation.py | 27 pruebas sintéticas aisladas; no valida implementación Android aún inexistente. |
| docs/translation-safety-preparation/ | Este diseño, evidencias y límites. |

**Archivos de producción que solo se proponen para revisión posterior:** Translator.kt; GoogleAppTranslator.kt/GoogleTranslator.kt/GoogleCloudTranslator.kt y fallback/GoogleTranslatorNeko.java; las tres salidas de LLMTranslator.kt; MessageTrans.kt (rich content forzado y selección/reintentos); configuración/resolver y nueva TranslationServicesPolicy; wiring en adaptadores/colas/cachés; build.gradle y módulo fuente compartido únicamente si se aprueba la estrategia de dependencia. Los puntos UI identificados son consumidores para pruebas, **no una propuesta de cambiar diseño/interfaz**. HTMLKeeper/TLRPC y Microsoft/DeepL se usan como contratos; no se propone reemplazarlos indiscriminadamente.

## Regresiones y aceptación antes de producción

| Riesgo | Prueba necesaria tras implementar, antes de habilitar |
|---|---|
| Se pierde traducción que antes funcionaba por fallback | Cada entrada del inventario prueba capacidad/denegación y error local; probar selección explícita de proveedor autorizado. Sin red a legado incluso en LLM y remapeos. |
| Formato o offsets alterados | HTMLKeeper real, TLRPC real, emojis/UTF-16, entidades anidadas/enlaces, saltos en chino, texto vacío/largo y HTML malformado; fixtures semánticos antes/después. El modelo actual solo preserva un payload sintético, no demuestra esa paridad. |
| Microsoft/DeepL dejan de cargar o pierden opciones | Comparación de API/SBOM, dependencias y fixtures de idiomas/formalidad/fallbacks permitidos sobre módulo reconstruido. Mantener referencias y clases necesarias. |
| Se ejecuta una tarea con grant viejo o se mezclan cuentas | Revocación/rotación al encolar, ejecutar y recibir callback; cache keys por cuenta/proveedor/modelo/idiomas/scope; cancelación y descarte de resultados viejos. |
| Se filtra contenido por excepción/caché/restore | Canarios en body/header/URL/stacktrace/errores/sufijos; backup import/export y restores de framework/OEM sin claves ni sesiones. No ampliar allowlist P0.3a para credenciales. |
| Scanner pasa por cobertura insuficiente | Positivos conocidos, UTF-16LE, anidados, corrupción/límites; revisar fuente/SBOM/bytecode y scanner genérico. Ocultar/ensamblar claves en runtime está prohibido como solución, aunque el patrón no las detecte. |
| Se debilita Diagnostic | Suite P0.1/P0.2/P0.3a/P0.3b, BuildConfig y manifiesto binario final sin INTERNET/auth/push; instalación offline en laboratorio y tráfico por UID. |

## Resultados realmente ejecutados ahora

- **27 pruebas aisladas aprobadas, 0 fallos, 0 omisiones**, 3,523 s: denegación Diagnostic/directa, grants/configuración/scope/vigencia/identidad, selección explícita, capacidades, endpoints, sesión Telegram, modelo local ausente, cancelación, ejecución diferida, errores sin payload y scanner adversarial. [Log](evidence/isolated-tests.log), [identidad de archivos probados y límites](evidence/isolated-tests.result.json).
- [Inventario](../../tests/translation_safety/callsites.json): 59 llamadas / 24 archivos. Snapshot de preservación de 21 fuentes seleccionadas; diff final debe contener únicamente tests/translation_safety y docs/translation-safety-preparation.
- [Escaneo de la fuente existente](evidence/existing-source-scan.json): clave A conocida detectada; resultado **no pasa**, como corresponde.
- [Escaneo del AAR existente](evidence/existing-aar-scan.json): clave B, paquete y certificado ajenos detectados; **no pasa**. SHA del AAR coincide con el de P0.3b. Esto no es un APK nuevo ni un nuevo escaneo del APK perdido.
- El scanner exige --apk para la estructura raíz de un APK; sus pruebas usan contenedores sintéticos en memoria, no APK instalables. Corrupción/profundidad/expansión incompleta no se informan como limpieza. Detección de candidatos no demuestra ejecución ni ausencia universal de secretos.

Comandos sin servicios externos:

```sh
python -m unittest discover -s tests/translation_safety -v
python tests/translation_safety/inventory.py
# Futuro APK de laboratorio, solo cuando se autorice construirlo:
python tests/translation_safety/artifact_gate.py ARCHIVO.apk --apk
```

Un resultado passed=false/exit1 al revisar el artefacto heredado es **hallazgo esperado**, no un fallo a ocultar. Los fingerprints no contienen los valores de las claves. No se ejecutan los traductores para probar su vigencia.

## Límites y decisión solicitada para la próxima etapa

Revisar primero política/capacidades y estrategia de dependencia. Recomendación: adaptador oficial/backend para mayor paridad, Telegram como opción explícita para flujos permitidos y local como complemento; ninguna habilitación hasta revisar privacidad, costes, procedencia y regresiones. No elegir una alternativa por éxito aparente con claves ajenas.

Diagnostic conserva su aislamiento actual; la política nueva **todavía no está conectada** y las claves heredadas **todavía no se retiraron**. No se habilita beta. Siguen pendientes Android real offline, instalación/arranque/Logcat, tráfico por UID, cuentas/sesiones, restauración framework/OEM y compatibilidad ELF/ejecución con páginas de 16 KB. No se afirma que el Poco tenga 16 KB. No se compila, instala ni distribuye APK aquí; no backend ni cuentas/credenciales reales. Main intacta, PR #2 abierto, Actions sin habilitar. No P0.4 ni Paso 4. Detenerse para revisión.
