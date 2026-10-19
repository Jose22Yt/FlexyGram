# Validación de P0.4b

## Identidad de código y evidencias

Código de aplicación/JNI compilado: **`c55915ce0bf9a820d4744a31f8c6aeddb80a1d02`**, sobre merge P0.4a `d9f2b788cf23e830e84ba24e9f6cb2e71e13bd4d`. Los 29 archivos de ese commit tienen [hashes congelados](evidence/code-source-hashes.json). El commit posterior de verificación/documentación ajusta el inspector para reconocer el nombre nativo real `libtmessages.49.so` y prueba nombres ausentes/ambiguos; no cambia Android/Gradle/JNI ni produce otra APK. Sus herramientas tienen [hashes propios](evidence/verification-tool-hashes.json). No se confunden estos commits con el código cuyo artefacto se construyó.

## Resultados

| Comprobación | Resultado real |
|---|---|
| Seguridad P0.1/P0.2/P0.3a/P0.3b | 26 aprobadas |
| Preparación de traducción | 27 aprobadas |
| Política runtime en arneses | 4 aprobadas |
| Fachada de laboratorio/compatibilidad | 14 aprobadas |
| Prototipo aislado | 12 aprobadas |
| Integración diagnóstica y DEX | 10 aprobadas |
| Variantes nuevas | 9 aprobadas |
| Total | **102 aprobadas, 0 fallidas, 0 omitidas** |
| Producción real Gradle | assembleProductionRelease rechazado con FLEXYGRAM_PRODUCTION_INCOMPLETE, salida1 |
| ARM64 completo | **BUILD SUCCESSFUL, 9m47s, 248 tareas: 41 ejecutadas, 207 al día** |
| JNI y Chaquopy | CMake/Ninja ARM64 ejecutados; runtime Chaquopy reconstruido; sin SKIP |
| Manifiesto fusionado y APK binario | Allowlist completa aprobada; solo ACCESS_NETWORK_STATE y permiso propio de receptor no exportado; sin INTERNET |
| BuildConfig Java real compilado | ID diagnóstico, API ID0/hash vacío, aislamiento=true, seis capacidades=false; sin valores de push utilizables |
| JNI enlazado | Scope diagnóstico coincide con Java, símbolo de atestación exportado; init y dos entradas de socket solo RET |
| Correspondencia JNI empaquetado | Hash de sección .text idéntico al binario enlazado inspeccionado |
| APK/ZIP/ABI/firma | CRC correcto; 18 bibliotecas raíz AArch64; firma válida y certificado idéntico a la clave propia de laboratorio |
| Escaneo APK | 14.847 entradas, 7 archivos anidados, 0 candidatos de clave cliente, 0 coincidencias de claves retiradas, 0 identidades/certificados operativos ajenos detectados, 0 configuraciones de servicios embebidas |
| Dependencias | 201 artefactos externos únicos escaneados y JAR de fachada limpios; cuatro grafos Diagnostic sin AAR retirado |
| DEX/guardas | Sin clases duplicadas, seis clases de fachada, sin clases extra del AAR o laboratorio; 17 clases de guardas inspeccionadas |
| Instalación/arranque/tráfico Android | **No ejecutados** |

No fue un clean global: el assemble ejecutó el grafo completo, reutilizando partes sin cambios; JNI se compiló y Chaquopy se reconstruyó en el entorno recuperado. Los intentos previos recuperaron dependencias y compilaron otras tareas del mismo código; no se usa el APK histórico P0.3g ni se afirma que todas las tareas corrieran desde cero en el último comando.

## Artefacto interno, sin distribución

- Paquete: `io.github.jose22yt.flexygram.diagnostic`.
- Etiqueta: FlexyGram Diagnostic. Versión: 13.0.2 (1261). ABI: arm64-v8a.
- Tamaño: **111.957.903 bytes**.
- SHA-256: **`87da6f47b08dbb9d885deb455ec905a7f94189068dd9adc600c2f9943d2ebc81`**.
- No instalado, publicado ni adjuntado. Su hash identifica exclusivamente este resultado interno; no es el APK P0.3g ni otra APK anterior.

La [firma pública](evidence/diagnostic-signature.log) se contrastó con el certificado exportado de la clave de laboratorio propia, fuera de Git. No se entrega clave/contraseñas ni se configura firma productiva. Las afirmaciones de escaneo se limitan a patrones, huellas y formatos inspeccionados; no son una garantía universal de ausencia de secretos.

## Inspección Java/JNI

Ver [política Java compilada](evidence/compiled-java-policy.json), [bytecode Java](evidence/java-policy-bytecode.log), [guardas nativas](evidence/native-linked-guards.json) y [desensamblado ARM64](evidence/native-linked-guards.log). Los tres métodos seleccionados contienen únicamente RET, sin inicialización o socket. La sección .text del APK tiene SHA-256 `f76278c7b470fc64e2d284fc80bdaad71d2087d3a3a0ec2b38a28cef5b1b065f`, idéntico al de la biblioteca enlazada antes de strip (28.385.356 bytes). También se verificó la atestación de flavor/capacidades dentro del JNI empaquetado. Es inspección estática: no se ejecuta JNI en Android ni se deduce comportamiento del framework completo.

El tipo de cuenta y namespace de datos compilados contienen solo el ID diagnóstico; las autoridades de providers son propias. El grafo Diagnostic incluye la fachada exclusivamente por diagnosticImplementation. Producción está deshabilitada, por lo que no existe un runtimeClasspath productivo resuelto que se pueda presentar como validado: no se crean stubs productivos para aparentar su compilación. Las declaraciones de dependencia productiva no incluyen la fachada ni el AAR retirado.

## Reproducción

Usar [versiones del entorno](evidence/environment.json), submódulos fijados, Android SDK37.0/API24 y BuildTools36.0.0, NDK27.2.12479018 y CMake3.31.6. Extraer con una herramienta que preserve permisos/enlaces originales; no convertir los symlinks del NDK en archivos de texto. Seleccionar host Python3.11.17 mediante CHAQUOPY_BUILD_PYTHON; no sustituirlo por3.12. Configurar exclusivamente la clave diagnóstica fuera del repo y las variables FLEXYGRAM_DIAGNOSTIC_KEYSTORE/STORE_PASSWORD/KEY_PASSWORD, sin imprimir sus valores. Producción no requiere ni debe recibir claves para demostrar el rechazo.

```bash
python -m unittest discover -s tests/security -v
python -m unittest discover -s tests/translation_safety -v
python -m unittest discover -s tests/translation_runtime -v
python -m unittest discover -s tests/translation_dependency -p test_facade.py -v
python -m unittest discover -s tests/translation_dependency -p test_prototype.py -v
python -m unittest discover -s tests/translation_staging -v
python -m unittest discover -s tests/build_variants -v
NATIVE_TARGET=arm64-v8a ./gradlew --no-daemon -Pkotlin.incremental=false :TMessagesProj:assembleDiagnosticDebug
./gradlew --no-daemon :TMessagesProj:assembleProductionRelease
```

La última orden debe fallar con el código de bloqueo, nunca crear una APK productiva. Las pruebas necesitan GSON_JAR2.14.0, KOTLIN_LIB de Gradle9.7.1 y TRANSLATOR_CLASSES_JAR como referencia ABI exclusivamente offline, fuera de dependencias Android. El entorno se recuperó por descargas oficiales y proxy local de la sesión; esas rutas/ajustes no se incorporan al proyecto. El build usó Gradle9.7.1 recuperado de la distribución exacta del Wrapper; no se modificó el Wrapper.

`tests/build_variants/check_diagnostic.py` acepta APK/aapt2/clases Java+Kotlin (classpath unido por `:` en Linux), grafo/manifiesto del mismo build, llvm-readelf y salida JSON. El inspector falla si falta o hay ambigüedad en la biblioteca de aplicación versionada, o si no coincide el scope Java/JNI. A continuación comprobar firma, comparar .text y conservar los hashes del código y artefacto. No instalar la APK para ejecutar estas inspecciones.

## Evidencias conservadas

- [Resumen íntegro](evidence/validation-summary.json), [pruebas](evidence/test-summary.json), [manifiesto fusionado](evidence/merged-manifest.xml) y [su auditoría](evidence/merged-manifest-audit.json).
- Siete logs `*-tests.log` de todas las suites; [rechazo Gradle productivo](evidence/production-build-rejection.log).
- `gradle-arm64-final.log`: log final completo con rutas locales de herramientas/workspace redactadas, incluyendo compilación nativa/Chaquopy y avisos heredados; el encabezado conserva el SHA del original.
- `artifact-scan.json`: resultados del APK, DEX, políticas y hashes/resultados de los 201 artefactos externos, con campos minimizados.
- `dependency-graph.json`: componentes de los cuatro grafos resueltos, sin rutas locales. El informe Gradle con rutas se regenera al reproducir.
- Las evidencias publicadas son texto/JSON legible; **ninguna contiene APK, firma privada o credenciales**. El informe comprimido completo se omitió tras el rechazo de revisión automática por identidad de contenido insuficiente; se inspeccionó localmente y se publicaron únicamente sus campos necesarios. [SHA-256 de evidencias](evidence/hashes.json).

Incidencias resueltas durante recuperación: proxy/JDK y SDK ausentes; resValues deshabilitado por defecto en AGP, habilitado en esta arquitectura; permisos de herramientas SDK y symlinks del NDK, restaurados desde los archivos oficiales; host Python correcto. Solo resValues requirió cambio de proyecto. Los avisos heredados de recursos, deprecaciones y C++ se conservan; no se alteraron recursos o bibliotecas para ocultarlos.

## Pendientes y recomendación

No se acredita instalación, arranque, ausencia de tráfico real por UID, callbacks Android, restauración framework/OEM o funcionamiento de las funciones. Persisten ANDROID_PLATFORM27 frente a minSdk24 y las cuatro bibliotecas Python históricamente incompatibles con16KB; ni este build ni zipalign son una certificación de16KB. Las dependencias pip no fijadas también impiden prometer reproducción binaria idéntica entre resoluciones; se conserva el inventario del artefacto realmente inspeccionado.

P0.4b está preparado para revisión de código y evidencias; conservar este PR en borrador y sin fusionar hasta aprobación. No hay variante autenticable operativa, beta distribuible, cuenta o servicio real habilitado. El siguiente trabajo no se inicia en esta entrega.
