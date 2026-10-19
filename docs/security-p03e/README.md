# P0.3e — viabilidad de sustitución de traducción, fase aislada

FlexyGram 1.0 — responsable **@Lukhou23**. Créditos y licencias originales conservados. 19/10/2026.

## Integración aprobada y alcance

PR #10 comprobado en `97b5972c03ced57e17b54ff6af5a8ea516785a7c`, 45 archivos esperados, hacia develop. Se integró exclusivamente en develop por **`26f5c9fc03924fafcf3246b78b48946d09fba69d`**. Su árbol, las 57 pruebas y las compilaciones/evidencias se conservan en [P0.3d](../security-p03d/README.md). Rama nueva: `security/paso-3-p03e-translation-dependency-prototype`.

Esta fase **solo añade tests/prototipo y documentación**. No sustituye `translator:1.6.1`, no modifica src/, Gradle, manifiestos, SDK ni funciones activas. P0.1–P0.3d siguen intactos; Diagnostic conserva denegación predeterminada, API 0/hash vacío, aislamiento de sesiones/plugins/push y ausencia de INTERNET. No hay backend, proveedor habilitado, APK nueva, instalación, distribución ni ejecución Android en esta fase.

## Fuentes verificadas y lo que falta

| Fuente primaria consultada | Resultado verificable | Límite |
|---|---|---|
| [POM publicado](https://repo.maven.apache.org/maven2/app/nekogram/translator/translator/1.6.1/translator-1.6.1.pom) | Declara SCM `https://github.com/Nekogram/translator`, GPL-3.0, Kotlin stdlib 2.2.10, Gson 2.14.0 y OkHttp 5.4.0. | Metadatos publicados; no son fuentes correspondientes ni acreditan derechos sobre un servicio. |
| [sources.jar publicado](https://repo.maven.apache.org/maven2/app/nekogram/translator/translator/1.6.1/translator-1.6.1-sources.jar) | Descargado otra vez: solo META-INF/ y MANIFEST.MF. Hash/listado en source-availability.json. | No permite reconstruir la biblioteca. |
| Repositorio SCM declarado, GitHub API pública | Respuesta 404 mediante la conexión actual. | No demuestra inexistencia universal: podría ser privado, movido o retirado. No se contactó a mantenedores ni se accedió a repositorios privados. |
| [Nekogram/Nekogram](https://github.com/Nekogram/Nekogram) | Árbol main inspeccionado, SHA `8c07753a82174314873a655bb7206a919bc0a919`, sin truncamiento; contiene wrappers de traducción. | No se estableció correspondencia de esos wrappers con las fuentes del AAR 1.6.1. No se ofrece una reconstrucción a partir de un repositorio parecido. |
| AAR activo conservado | SHA-256 `08cdf350bd21b6cc063a8fb0141eed6cdf06c06772c5080ca38114dce07a8f27`. | Es una referencia binaria, no una fuente verificable. No se modifica ni ejecuta un motor remoto. |

**Resultado:** no se ha localizado una fuente correspondiente verificable de esta versión mediante las comprobaciones anteriores. No es viable certificar hoy una reconstrucción fiel de 1.6.1. La inspección javap/constant pool aporta firmas y observaciones de compatibilidad, no se presenta como código fuente original recuperado.

Alternativas fuente primarias, solo candidatas:

- [DeepL/deepl-java](https://github.com/DeepL/deepl-java/tree/8b7ed8c1d0f0f6f921a463b252f04c2ec47cf791), repositorio oficial al que redirige DeepLcom/deepl-java, snapshot `8b7ed8c1d0f0f6f921a463b252f04c2ec47cf791`, licencia MIT declarada por GitHub.
- [Azure SDK Java, módulo azure-ai-translation-text](https://github.com/Azure/azure-sdk-for-java/tree/9deee9867e66d956dde14cd7b76794dcdb8b4b60/sdk/translation/azure-ai-translation-text), snapshot `9deee9867e66d956dde14cd7b76794dcdb8b4b60`, repositorio MIT.

No son reemplazos API/ABI del AAR. No se añaden ni se compilan aquí, ni se certifica su soporte Android, peso transitivo, paridad de idiomas/calidad, licencias de toda la distribución o configuración de credenciales. La existencia de fuentes oficiales no autoriza a utilizar un servicio. Las referencias oficiales de [Microsoft translate](https://learn.microsoft.com/en-us/azure/ai-services/translator/text-translation/reference/v3/translate) y [DeepL translate](https://developers.deepl.com/api-reference/translate/request-translation) se consultaron únicamente como contratos documentales: formatos, idioma detectado y errores; DeepL documenta formality y tag handling. No se realizaron llamadas a sus API.

## Superficie que debe conservarse

Solo tres consumidores Java/Kotlin de producción importan `app.nekogram.translator`: RealMicrosoftTranslator (proveedor 6), DeepLTranslatorNeko (ruta sin clave del proveedor 7) y GoogleTranslatorNeko. El proveedor Microsoft 5 usa BingTranslatorRaw local, no ese AAR. No confundirlos ni retirar sus funciones.

| Clase/método de biblioteca | Consumo/contrato observado | Requisito futuro |
|---|---|---|
| BaseTranslator.translate(String text, String from, String to) → Result, throws Exception | Convierte códigos de entrada, llama translateImpl y convierte sourceLanguage de salida. | Conservar orden/semántica; no inferir segmentación, reintentos o validación que Base no hace. |
| getTargetLanguages(), supportLanguage(String) | Lista y comprobación contains exacta, sensible a mayúsculas. | Mantener lista declarada y diferenciarla de disponibilidad real del servicio. |
| MicrosoftTranslator.getInstance(), supportLanguage(), translate() | RealMicrosoft comprueba destino, convierte aliases chinos y auto→null; entrega texto/HTML. | No inicializar un singleton heredado ni heredar credenciales/identidad en un sustituto. |
| DeepLTranslator.getInstance(), translate() | Wrapper envía text/from/to y lee result.translation. | Conservar salida y detectar idioma; separar la vía API propia/formalidad del fallback de biblioteca. |
| Result.translation y Result.sourceLanguage, Result.of, equals/hashCode | Campos públicos finales String; factoría estática. | Una futura fachada deberá preservar estos campos para consumidores Java; un record con accessors no es ABI equivalente. |
| Http429Exception extends IOException | Tipo de rate limit del AAR; no cancelación coroutines. | Mapear con diagnóstico seguro y sin cambiar proveedor. |
| DeepLTranslator.setJwt(String) | Existe en ABI; sin llamadas desde los consumidores actuales del cliente. | No copiar, leer ni reutilizar JWT heredados. La compatibilidad con terceros/plugins requeriría análisis separado. |

[evidence/consumed-abi.txt](evidence/consumed-abi.txt) registra firmas y descriptores. [class-reference-closure.json](evidence/class-reference-closure.json) registra aristas de clases del constant pool: cierre Microsoft de 11 clases y DeepL de 10, sin Google en esos dos cierres. **No es prueba completa de alcanzabilidad**: reflexión, descriptores, inicialización y consumidores binarios requieren revisión. No se borran holders/clases ni se parchea el AAR basándose en ese grafo.

## Matriz de compatibilidad y brechas

| Aspecto | Referencia observada | Prototipo/prueba aislada | Estado antes de producción |
|---|---|---|---|
| Métodos y resultados | Base.translate y campos Result públicos; callbacks Translator/TLRPC en el cliente. | BaseTranslator real con subclase de transporte ficticio verifica pipeline/Result; prototipo fuente usa tipos propios. | **No drop-in ABI**; falta fachada y compilación de consumidores reales con sustituto aprobado. |
| Idiomas | 134 literales en constructor Microsoft, 123 en DeepL; snapshot binario, no lista oficial de servicio. | Se comprueban todas las entradas con contains y listas inmutables. | No se ejecutaron proveedores reales ni se certifican todos esos idiomas; catálogo oficial futuro puede diferir. |
| Códigos chinos | zh-CN↔zh-Hans y zh-TW↔zh-Hant, conversión de biblioteca sensible a mayúsculas. Aliases de wrapper zh/zh-HK y variaciones. | Se ejercitan ambos sentidos y aliases con un oráculo de Base y reglas observadas. | Casos declarados pasan; no se infiere equivalencia lingüística. |
| Auto/origen | RealMicrosoft transforma solo `auto` en null; cadena vacía permanece vacía. Wrapper DeepL conserva `auto`. | null/auto/vacío/zh/variantes/pt-BR probados, sin normalizar silenciosamente ambas vías igual. | El mapeo hacia una API oficial será otra capa y debe aprobarse. |
| Texto/HTML, Unicode, saltos | HTMLKeeper/TranslateAlert2/TLRPC envuelven a los motores; no son parte de la ABI AAR. | Transporte eco conserva literalmente HTML ficticio, emoji y saltos, y etiqueta TEXT/HTML. | **No prueba de transformación HTML ni offsets de entidades**; esos componentes quedan intactos. Faltan corpus reales de formato con sustituto. |
| Formalidad DeepL | Rama API propia del cliente usa default/prefer_less/prefer_more; AAR.translate no tiene ese argumento. | Capacidad explícita en fixture DeepL; Microsoft rechaza formalidad antes del transporte. | Extensión del prototipo, **no paridad acreditada con AAR**. SDK/API futura requiere evaluación. |
| Errores/429 | Base propaga Exception; existen Http429Exception y errores privados heredados. | 400/403/429/456/500/504, fallo IO, respuesta nula; código seguro y sin causa privada. | Semántica de error deliberadamente más segura, no identidad de excepciones. Falta puente hacia UnsupportedOperationException/callbacks del cliente. |
| Cancelación | ABI síncrona sin token de cancelación. | Antes/durante/después del fixture, excepción cancelada e interrupción de hilo; descarta resultados tardíos, no fallback. | Contrato nuevo de laboratorio. Falta puente coroutines/HTTP, cierre de recursos y Android real. |
| Reintentos/proveedor | P0.3d mantiene denegación y elimina fallbacks no autorizados. | Una petición por operación/fallo, proveedor final inmutable; ningún cambio de proveedor. | No se habilitan grants ni política de retry remota. |
| Diagnósticos/secretos | Dos claves/identidad ajenas siguen en fuente/AAR activos. | Request/Response/Result redactados; fallos no conservan message/cause del transporte; scanner del JAR propio limpio. | **No equivale a APK limpia**; beta sigue bloqueada. |

## Prototipo y pruebas realmente ejecutadas

`tests/translation_dependency/java/lab/flexygram/translation/PrototypeAdapter.java` es un núcleo fuente independiente del AAR para instancias Microsoft y DeepL. Solo usa JDK y una interfaz FixtureTransport: no tiene URL, HTTP, SDK, acceso a entorno/credenciales ni inicializadores de servicios. Vive fuera de todos los source sets Android. No está conectado a la aplicación.

El arnés ejecuta **BaseTranslator y Result reales** del binario mediante una subclase que sobrescribe exclusivamente el transporte y normalización observada; no ejecuta MicrosoftTranslator, DeepLTranslator, Google ni sus singletons. La estática de Base se inspeccionó: crea Gson; no inicializa HTTP. El uso de un oráculo parcial no demuestra paridad de implementaciones de proveedor desconocidas.

Variables de herramientas locales, sin secretos:

```sh
# TRANSLATOR_CLASSES_JAR: classes.jar extraído sin modificar del AAR cuyo hash está fijado.
# GSON_JAR: Gson 2.14.0 ya disponible; JDK 21 en PATH.
python -m unittest discover -s tests/translation_dependency -v
python tests/translation_dependency/binary_inventory.py RUTA_CLASSES_JAR
python tests/translation_dependency/binary_inventory.py RUTA_CLASSES_JAR --languages
```

**Resultado: 69 pruebas aprobadas, 0 fallos, 0 omisiones: 12 nuevas y las 57 previas repetidas (26 + 27 + 4).** El JAR fuente del prototipo pasó el escáner; no se generó una APK ni se repitió Gradle Android en esta fase. Las compilaciones anteriores conservadas corresponden a P0.3d, no se atribuyen al prototipo.

La suite no descarga dependencias ni accede a servicios. Las listas, ABI, hashes y resultados se encuentran en evidence/. El JAR escaneado contiene **solo** las clases fuente del prototipo, no el arnés/oráculo ni el AAR. No se altera ni suprime una función activa para obtener un scanner limpio. La retirada futura exige escanear la APK real completa y todos sus contenedores.

## Cómo retirar las dos claves sin sacrificar otros motores — propuesta condicionada

1. Congelar AAR/POM/metadata, referencias/ABI y corpus; completar inventario de fuentes y licencias. Si se recupera fuente correspondiente con tag/commit verificable, construir una referencia reproducible antes de cambiarla. No basta un fork de nombre parecido o un sources.jar vacío.
2. **Clave A:** está en GoogleTranslator.kt del cliente, no solo en el AAR. Tras aprobación, sustituir su transporte heredado por una fachada de proveedor no disponible/autorización explícita que conserve contrato e ID; una futura función solo se recuperará con integración autorizada. No esconder, fragmentar o trasladar el literal a BuildConfig.
3. **Clave B/identidad ajena:** retirar la dependencia binaria entera solo cuando un módulo fuente revisado cubra los consumidores Microsoft/DeepL y la fachada Google bloqueada sin conservar el motor/clases/holders ajenos. No hacer cirugía de ZIP/AAR ni confiar en R8 para demostrar procedencia o retirada.
4. Alternativas si no hay fuentes correspondientes: adaptadores propios con API/SDK oficial y fachada de compatibilidad, o mantener cerrado el AAR y bloquear distribución. Evaluar Android, dependencias transitivas, formatos, cuotas, autorización, privacidad y licencias por separado. No se selecciona ni integra una alternativa de producción hoy.
5. Gates antes de proponer reemplazo: API/ABI de consumidores, catálogo/capacidades, fixtures de formato/TLRPC/errores/cancelación, ausencia de fallback y secretos en logs; construcción ARM64/JNI/Chaquopy, protección Diagnostic y escaneo genérico + dos huellas + identidad ajena en APK/DEX/IMY/JAR/resources. Confirmar presencia funcional Microsoft/DeepL desde fuente, no solo borrado de hallazgos. Pruebas Android y medición posteriores requieren autorización.

**Decisión recomendada:** aceptar este estudio/prototipo para continuar revisión, pero **no aprobar todavía la sustitución activa**. Las fuentes correspondientes faltan y las pruebas son parciales/de laboratorio. Se mantienen las funciones y los bloqueos P0.1–P0.3d; la beta sigue bloqueada por las dos claves y la identidad ajena.

## Incidencia de Kotlin

[KOTLIN-INCREMENTAL-REPRO.md](KOTLIN-INCREMENTAL-REPRO.md) conserva contexto, logs originales y protocolo futuro en entorno limpio. No se cambia ninguna configuración ni se ejecuta una nueva compilación Android para investigar esa incidencia en P0.3e.
