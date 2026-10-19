# P0.3g — sustitución diagnóstica experimental

FlexyGram 1.0, responsable @Lukhou23. Rama experimental `security/paso-3-p03g-translation-staging`. No constituye una traducción operativa, cliente autenticable o beta distribuible.

## Integración aprobada

PR #12 verificado con HEAD exacto **2e2037225555a51a291545e1c64e513c830fed80**, base develop y 27 archivos únicamente bajo `docs/security-p03f/` y `tests/translation_dependency/`. Se integró exclusivamente en develop como **8ed92d59f8e2c379851e13d3c45f24d8a36f92df**. La rama experimental deriva de ese commit. Main y PR #2 no se modifican. Las evidencias históricas P0.3d–f permanecen byte a byte intactas.

## Cambios funcionales exactos

| Archivo/componente | Cambio limitado a Diagnostic | Contrato y protección |
|---|---|---|
| `settings.gradle` | Incluye `:translation-compat-diagnostic`, situado en `TMessagesProj_Modules/translation-compat-diagnostic` | No incluye el laboratorio de tests |
| `TMessagesProj/build.gradle` | Sustituye la declaración translator:1.6.1 por el proyecto fuente; excluye expresamente ese grupo/módulo en todas sus configuraciones | El proyecto ya fija application ID Diagnostic e ISOLATED_DIAGNOSTIC=true en todas sus variantes; no se crea otra identidad ni habilitación |
| Nueva tarea `verifyDiagnosticTranslationClasspath` | Antes de preBuild comprueba los componentes de debugCompileClasspath y debugRuntimeClasspath y produce un inventario de artefactos externos | Rechaza la dependencia heredada; no acepta un reporte obsoleto como prueba |
| `BaseTranslator.java` | Firma pública/protegida, pipeline de conversiones, array secuencial, campo Gson y helper MD5 de compatibilidad | Sin transporte, credenciales, validación de autorización o fallback nuevo |
| `Result.java` | Campos public final String, factory, equals/hash XOR compatibles | toString redactado deliberadamente |
| `MicrosoftTranslator.java`, `DeepLTranslator.java`, `LanguageCodes.java` | Constructores sin argumentos/getInstance y catálogos ordenados 134/123; conversiones chinas exactas | Implementación de traducción denegatoria, sin transporte ni constructor de inyección. setJwt rechaza cualquier valor sin guardarlo |
| `Http429Exception.java` | Clase IOException y constructor conservados | Diagnóstico fijo; no se simula una respuesta remota |
| `GoogleTranslatorNeko.java` | Mantiene el método público translate y requireRoute; después deniega incondicionalmente | No importa ni inicializa GoogleAppTranslator; no usa clases de la biblioteca retirada, ni aunque un doble de política permitiese la ruta |
| `GoogleTranslator.kt` | Retira el builder/petición/respuesta PA y su clave incrustada; elimina cliente HTTP/imports que ya no usa | Mantiene objeto Translator, doTranslate, contrato privado translate con denegación local, catálogo, helpers, preferencias e interfaz. No sustituye por Google web ni otro proveedor |

No se retiene ni reconstruye la clave retirada mediante cifrado, ofuscación o concatenación. No se parchea el AAR ni se borra del historial/caché de referencia: simplemente deja de estar resuelto y empaquetado por esta compilación. El AAR original sigue disponible solo como referencia de laboratorio para comprobar ABI; no debe confundirse ese oráculo con una dependencia del APK.

El nuevo módulo contiene **seis clases fuente** y ninguna implementación HTTP/SDK, endpoint, JWT, clave cliente o identidad de aplicación ajena. El namespace `app.nekogram.translator` es necesario para conservar enlace ABI; no es una nueva identidad de aplicación ni apropiación de autoría. Se conservan GPL-3.0, créditos Exteraless/Nekogram y responsabilidad de @Lukhou23.

El módulo aislado P0.3f, con FixtureTransport y sus constructores ficticios, sigue exclusivamente bajo tests. No está enlazado a Android. Su copia diagnóstica revisada no contiene FixtureEngine, FacadeFailure ni FixtureTransport.

## Componentes conservados

Sin cambios en Translator.kt, HTMLKeeper.java, TLRPC.java, TranslationServicesPolicy.java, RealMicrosoftTranslator.kt, DeepLTranslator.kt y MicrosoftTranslator.kt. Tampoco en preferencias, navegación, animaciones, renderizado, reproductor, actualizador, manifiesto fuente ni políticas P0.1/P0.2/respaldo/push.

- Microsoft proveedor 6 sigue llamando a MicrosoftTranslator.getInstance/supportLanguage/translate y leyendo Result.translation.
- DeepL conserva su wrapper Java y consumidor Kotlin. La rama local de API propia permanece intacta y denegada; no se activa ni se elimina.
- Microsoft proveedor 5 usa su implementación local existente, también denegada.
- Los motores Google PA y biblioteca quedan temporalmente sin implementación remota. Sus entradas y preferencias permanecen, con error explícito seguro.
- Todos los demás proveedores, incluido Google web, continúan denegados por TranslationServicesPolicy antes de preparar trabajo o inicializar transportes. Una preferencia no concede autorización.

No se afirma que Microsoft o DeepL traduzcan. Las firmas y puntos de integración existen, pero sus implementaciones diagnósticas no realizan trabajo remoto. Su recuperación requerirá transporte autorizado con fuentes verificables, revisión de política, privacidad, cancelación y formato; no bastará con activar una preferencia o retirar una guarda.

## Pruebas y adaptación explícita de controles

Las **83 pruebas previas** se ejecutaron primero sobre el develop integrado antes de modificar producción; pasaron. Después se ejecutaron de nuevo sobre P0.3g con controles de preservación actualizados para los cambios expresamente autorizados: **83 aprobadas**. Se añaden **10 pruebas**, todas aprobadas: total actual **93, sin fallos ni omisiones**. Logs bajo `evidence/`.

No sería correcto conservar una aserción que exige el AAR activo y llamar regresión a su retirada autorizada, ni eliminar dicha comprobación sin sustituto. Por eso:

- `reviewed_changes.json` registra el commit base y hashes antes/después de exactamente 11 archivos de integración (incluido el módulo nuevo). `review_scope.py` verifica ese límite congelado; las pruebas nunca lo regeneran. Cualquier desviación de producción o evidencia histórica fuera del alcance falla.
- `preserved_sources.json` conserva la historia P0.3d y añade los tres hashes modificados en P0.3g con antes/después explícitos. Los demás controles de identidad permanecen.
- El inventario léxico pasa de **55 llamadas/22 archivos a 53/21** por retirar las dos llamadas al AAR dentro de GoogleTranslatorNeko. El wrapper público continúa presente y está probado con política real y doble permisivo; no se elimina para reducir el contador.
- El control del builder PA pasa de exigir una guarda anterior al builder a exigir guarda anterior a la denegación y ausencia del builder/cliente. No se rebaja a una búsqueda de clave solamente.
- Las pruebas de laboratorio P0.3e/f siguen comprobando su propio prototipo y ABI contra el artefacto original. Los controles de aislamiento ahora admiten exclusivamente la sustitución diagnóstica con hashes congelados, y comprueban que el laboratorio no se incluye en Android.

### Nuevas comprobaciones ejecutadas

1. Descriptores y modificadores públicos/protegidos de las cinco clases ABI frente al AAR registrado.
2. Reflexión sobre constructores: Microsoft/DeepL tienen solo constructor público sin argumentos; cero interfaces/constructores de transporte ficticio en producción. Instancias normales/singletons y setJwt deniegan sin texto privado.
3. Catálogos completos, orden y conversiones null/vacío/auto/chino/mayúsculas.
4. Wrappers Java completos compilados contra las clases fuente, sin ninguna clase Google heredada. Denegación con política real y también con doble permisivo local.
5. Archivos Kotlin completos RealMicrosoftTranslator y GoogleTranslator, sin extraer sus métodos, compilados con consumidores Java contra la fachada diagnóstica real; ejecución JVM bajo política real que deniega. Android/HTMLKeeper/TLRPC son dobles en esta prueba local, no en la compilación completa.
6. Preservación byte a byte de contratos de entidades, consumidores Microsoft/DeepL y políticas de aislamiento; límites exactos del diff preparado para commit.
7. Dependencia heredada ausente, exclusión obligatoria y fuentes compiladas sin materiales retirados detectados.
8. Todas las fuentes del módulo contra bootclasspath Android API24 y D8 min-api24; seis clases sin duplicados.
9–10. Pruebas sintéticas del inventario DEX: distingue definiciones de clase de simples menciones en el pool de strings y rechaza un formato inválido. La inspección del APK usa class_defs, no cuenta cadenas como si fueran clases.

Los canarios, errores y transportes de prueba son ficticios y locales. Ninguna prueba solicita Telegram/Microsoft/DeepL, manipula sesiones, revoca tokens ni configura cuentas reales.

## Compilación y verificación del artefacto

Los resultados definitivos, códigos de salida, hashes y comprobaciones del APK se registran en los JSON y logs de `evidence/`. Solo la ejecución final exitosa y el APK cuyo hash figure allí pueden considerarse evidencia de integración; las pruebas JVM no sustituyen esa compilación.

Comando ejecutado con el entorno aislado ya aprovisionado:

```sh
NATIVE_TARGET=arm64-v8a ./gradlew --offline --no-daemon -Pkotlin.incremental=false \
  :TMessagesProj:clean :translation-compat-diagnostic:clean :TMessagesProj:assembleDebug
```

Entorno: JDK JetBrains 21.0.10 declarado para Gradle, Wrapper9.7.1, AGP9.3.1, SDK37, BuildTools36.0.0, NDK27.2.12479018, CMake3.31.6, Python3.11 y Chaquopy17.0.0; tests javac con Temurin21.0.12.1+1. Se usa CMAKE/CHAQUOPY_BUILD_PYTHON explícitos como en la compilación previa. Firma Debug de laboratorio local existente, fuera de Git; no se solicitan ni publican secretos. Dependencias disponibles en caché; Gradle se ejecuta offline. La referencia AAR permanece en el entorno de tests, no en los grafos activos.

`kotlin.incremental=false` es solo argumento local de la ejecución, no un cambio de gradle.properties. No se reproduce ni se declara resuelta la incidencia incremental histórica; su protocolo P0.3e permanece intacto.

Primer intento: falló en la nueva tarea verificadora, que consultaba resolvedConfiguration.resolvedArtifacts y provocaba selección ambigua de variantes de proyectos Media3 con AGP9.3.1. Se corrigió únicamente esa tarea: inspecciona resolutionResult para componentes y ArtifactView filtrada a componentes externos para inventariar AAR/JAR. No cambia versiones, Media3, funciones de la app o reglas de matching. El fallo y su log se conservan.

Inspección reproducible, sin instalar ni ejecutar:

```sh
python3.11 tests/translation_staging/check_integration.py APK_INTERNA \
 --aapt2 RUTA_BUILD_TOOLS/aapt2 \
 --classes CLASES_JAVA:CLASES_KOTLIN \
 --graph TMessagesProj/build/reports/translation-diagnostic-classpath.json \
 --manifest TMessagesProj/build/intermediates/merged_manifests/debug/processDebugManifest/AndroidManifest.xml \
 --output docs/security-p03g/evidence/android-integration.json
```

El control inspecciona manifiesto binario y fusionado, mutaciones negativas, CRC/ELF ARM64, guardas compiladas, BuildConfig API0/hash vacío/aislamiento, definiciones DEX sin duplicados, seis clases propias y ausencia de clases de laboratorio o extras del AAR. Escanea recursivamente APK/DEX/JAR/recursos/IMY y todos los AAR/JAR externos resueltos en ambos grafos, además del JAR fuente nuevo. Reporta hashes, contadores e IDs; nunca los valores coincidentes.

## Resultado final comprobado

- **Gradle exit0 / BUILD SUCCESSFUL en 8m39s**, 252 tareas: 39 ejecutadas, 14 desde caché y 199 actualizadas. Se limpiaron el módulo Android y el nuevo módulo fuente; las dependencias/subproyectos no modificados reutilizaron caché. CMake ARM64 y el runtime Chaquopy se construyeron; no se excluyeron JNI ni tareas Python. CheckDebugDuplicateClasses aprobado.
- **93 pruebas aprobadas**, 0 fallos, 0 omisiones, más **10 mutaciones negativas del manifiesto real rechazadas**. Hashes de las fuentes verificadas de nuevo después de compilar; 16 submódulos permanecen en sus commits fijados.
- APK **interna exclusivamente**: SHA256 **6302ecb37ca15716b5ce56fe1039845841454092b35181ffcd35cb82832cd066**, **111957647 bytes**, paquete `io.github.jose22yt.flexygram.diagnostic`, nombre `FlexyGram Diagnostic`, versión `13.0.2`/`1261`, ARM64 y firma Debug v2 válida. No se adjunta, instala, distribuye ni publica como Release.
- Manifiestos fusionado y binario: allowlist aprobada; **INTERNET ausente**, solo ACCESS_NETWORK_STATE y el permiso propio de receiver. BuildConfig compilado: **API ID0, API Hash vacío e ISOLATED_DIAGNOSTIC=true**. Se mantienen las políticas previas, sin habilitar autenticación, Firebase/push, plugins o proveedores.
- APK: escaneo **completo**, **14847 entradas**, **7 archivos anidados**; **0 candidatos de clave cliente, 0 coincidencias de las dos claves retiradas, 0 marcadores de paquete ajeno, 0 marcadores de certificado ajeno, 0 google-services.json**. DEX, recursos, JAR/IMY internos y demás entradas se revisan recursivamente.
- **201 AAR/JAR externos únicos** resueltos entre compile/runtime y el JAR de la fachada: todos los escaneos completos y aprobados. Ningún grafo activo contiene translator:1.6.1; el artefacto original de referencia no está en esos classpaths.
- **73595 definiciones DEX**, **0 duplicadas**; exactamente una definición de cada una de las seis clases de la fachada, cero clases extra del AAR en su namespace y cero clases del transporte de laboratorio. Guardas verificadas en **17 clases compiladas**. Se validan **18 bibliotecas instalables ELF AArch64** y CRC del ZIP.
- Avisos no bloqueantes observados: obsolescencias Locale/Java, reglas tools del manifiesto sin otra declaración que reemplazar/eliminar, compatibilidad mínima/políticas CMake, extensiones/deprecaciones/atributos o campos sin uso en C++. Gradle avisa sobre APIs obsoletas para Gradle10. No se cambian archivos nativos ni herramientas para silenciarlos.

Esto demuestra viabilidad de **compilar Diagnostic con sustitución fuente cerrada**, no traducción real ni soporte Android en ejecución. La retirada de las dos claves/marcadores está respaldada por el escaneo de esta APK concreta y su grafo activo; no por ocultación/R8. La autorización de distribución continúa en **false**.

## Riesgos y límites pendientes

- **No habilitar ni distribuir.** Incluso un escaneo estático limpio no autoriza servicios ni certifica seguridad universal. Diagnostic mantiene INTERNET ausente, API0/hash vacío, autenticación/MTProto/plugins/desarrollo/respaldo/Firebase/push deshabilitados por las políticas previas; no se instalan APK ni se prueban cuentas.
- **No hay validación ART/emulador/Poco.** Compilar y analizar estáticamente no demuestra arranque, comportamiento, latencia, consumo o traducción real. No hay optimizaciones ni cambios visuales en esta fase.
- **minSdk24 no equivale a soporte integral API24.** La fachada sí se compila contra API24. La configuración nativa original conserva ANDROID_PLATFORM=android-27, mientras el manifiesto declara mínimo24. Es una limitación heredada que necesita revisión/ejecución posterior; no se altera arbitrariamente aquí. Tampoco se certifica Android17/API37 por usar compileSdk37; targetSdk original sigue36.
- **Cancelación/formato operativos pendientes.** RealMicrosoft conserva el catch(Exception) heredado que puede convertir CancellationException en IllegalStateException cuando exista una integración autorizada. Actualmente la guarda impide llegar. No hay sockets/trabajos remotos que cancelar en la fachada cerrada. Igualdad de firmas y catálogos no demuestra errores HTTP, semántica de idiomas ni paridad de HTMLKeeper/offsets con un proveedor.
- **Alcance de escaneo.** Detecta formatos y huellas registrados, ZIP/JAR/IMY anidados, UTF16 y clases DEX. No es una prueba universal de ausencia de secretos, tráfico o malware; no cubre valores reconstruidos arbitrariamente. Este cambio no conserva reconstrucciones de las dos claves.
- **Recuperación de funciones.** Google PA/biblioteca y Microsoft/DeepL de la fachada permanecen explícitamente indisponibles; los ajustes no se borran. Un futuro transporte autorizado deberá preservar contratos y pasar revisión independiente antes de cambiar la política. No se implementa backend ni se avanza a P0.4/Paso4.

Recomendación: revisar únicamente la viabilidad diagnóstica y sus evidencias. Esta rama no se fusiona automáticamente ni autoriza una versión funcional de traducción.
