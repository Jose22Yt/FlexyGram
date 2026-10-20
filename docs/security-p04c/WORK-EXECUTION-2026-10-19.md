# P0.4c: ejecución real de recuperación y reconstrucción

FlexyGram, responsable @Lukhou23. Continuación de PR17 desde
`723580b5cfee51416aa3f87cdebc3f8c911eb7ed`, siguiendo el comentario
`https://github.com/Jose22Yt/FlexyGram/pull/17#issuecomment-6279426562`.
No autoriza fusión, firma, distribución, Production ni Paso4.

## Resultados de esta ejecución

- CPython3.11.17: gate de entrada **54/54**, normal y `-O`, sin fallos ni omisiones.
- Gate nativo completo **177/177**, normal y `-O`, sin fallos ni omisiones.
- Regresiones históricas **102/102** reejecutadas:26+27+4+12+14+10+9.
- Total único **279**: las207 históricas,16 del adaptador fijado PR21,
  52 de preparación recibidas y4 regresiones nuevas. No se suman ejecuciones `-O`.
- Se recuperaron por descarga de sus orígenes fijados los **25 miembros exactos**
  del antiguo paquete:18 wheels originales ARM64,5 fuentes y2 recibos.
  Tamaño y SHA256 de cada miembro coinciden con el manifiesto histórico.
  **El ZIP original no se recuperó**; no se ejecutó el staging de ese contenedor
  ni se cambió su pin. Se usó la verificación independiente de los inputs fijados.
- Preflight de reconstrucción:18 wheels válidos. Reconstrucción offline A/B real
  con NDK27.2.12479018, CMake3.31.6 y GNUld2.42 desde fuentes fijadas.
  **Los cuatro ELF y tres wheels coinciden byte a byte entre A/B y con los
  hashes históricos**, sin actualizar versiones ni pins para aceptar diferencias.
- ABI final de los cuatro ELF extraídos de los wheels: cuatro contratos válidos,
  sin pérdidas de exportaciones, diferencias de tipos/versiones GNU ni nuevos símbolos.
  `SONAME`/`DT_NEEDED`, PT_LOAD4/16KB y RELRO se conservaron según los controles.
  El informe preliminar de candidatos anteriores al reenlazado no debe confundirse
  con `abi-final-wheels.json`, que inspecciona los binarios realmente empaquetados.
- Se recompiló el runner de instrumentación: **unsigned, no instalable, no ejecutado**.
  Su contrato permanece fijado a la APK y certificado históricos; no se flexibilizó
  para aceptar una APK nueva sin firma. El inventario actual no tiene emulador ARM64
  o imagen arrancada, KVM ni capacidades de aislamiento de red de administrador.

## Correcciones realizadas

1. `reproduce_locked_16k.execute`: las rutas con `..` no coincidían con el
   `-ffile-prefix-map` después de la normalización de CMake, alterando FreeType.
   Primero se mantienen las validaciones de rutas originales/symlinks; solo después
   se pasan rutas canónicas a los builders. La primera ejecución fallida se rechazó
   por hash, como corresponde. La nueva ejecución A/B conserva los hashes aprobados.
   Dos tests cubren normalización y rechazo previo de symlinks.
2. `prepare_experiment --unsigned`: retira exclusivamente la asignación de firma
   del flavor Diagnostic en el checkout desechable. No toca el build activo, no
   crea/carga claves ni introduce firma automática. Dos tests verifican sustitución
   exacta y rechazo de asignaciones ausentes/duplicadas. Un primer intento real
   usando `signingConfig = null` falló por sobrecargas ambiguas de AGP; la corrección
   elimina la asignación y conserva la ausencia de firma en los build types.
3. Inventario de alcance: hashes exactos para los cuatro helpers incorporados por
   ChatGPT y la actualización ya recibida de `rebuild_candidates.py`; no se amplían
   prefijos permitidos ni se relajan validadores. Los fallos iniciales de entorno
   (JAVA_HOME, fuentes externas PR20/21 e inventario desactualizado) se corrigieron
   antes de las ejecuciones aprobadas. Los módulos auxiliares se obtuvieron por
   commit y hash fijos, sin fusionar sus PR ni permitir red dentro de los tests.

## Comandos reproducidos

```sh
python3.11 -B tools/native_compatibility/run_p04c_host_gate.py
python3.11 -B -O tools/native_compatibility/run_p04c_host_gate.py
python3.11 -B tests/native_compatibility/run_gate.py --output /private/native-all.json
python3.11 -B -O tests/native_compatibility/run_gate.py --output /private/native-all-optimized.json
python3.11 -m unittest discover -s tests/security -v
python3.11 -m unittest discover -s tests/translation_safety -v
python3.11 -m unittest discover -s tests/translation_runtime -v
python3.11 -m unittest discover -s tests/translation_dependency -p test_prototype.py -v
python3.11 -m unittest discover -s tests/translation_dependency -p test_facade.py -v
python3.11 -m unittest discover -s tests/translation_staging -v
python3.11 -m unittest discover -s tests/build_variants -v
python3.11 tools/native_compatibility/reproduce_locked_16k.py --sources "$SOURCES" --wheelhouse "$ORIGINAL_WHEELS" --ndk "$NDK" --cmake "$CMAKE" --output "$NEW_OUTPUT" --verify-inputs-only
python3.11 tools/native_compatibility/reproduce_locked_16k.py --sources "$SOURCES" --wheelhouse "$ORIGINAL_WHEELS" --ndk "$NDK" --cmake "$CMAKE" --output "$OTHER_NEW_OUTPUT"
python3.11 tools/native_compatibility/prepare_experiment.py --source "$SOURCE_CHECKOUT" --checkout "$INDEPENDENT_CHECKOUT" --wheelhouse "$OTHER_NEW_OUTPUT/a/wheels" --manifest "$OTHER_NEW_OUTPUT/a/wheels-manifest.json" --python "$ABSOLUTE_PYTHON311" --unsigned
NATIVE_TARGET=arm64-v8a ./gradlew -Pkotlin.incremental=false :TMessagesProj:assembleDiagnosticDebug
```

Los comandos requieren JAVA_HOME/JBR21, SDK37/BuildTools36, los16 submódulos fijados,
pyelftools del lock, GSON, compilador Kotlin, oracle de firmas y los paths externos
PR20/21 fijados por `pr21_adapter.py`. Los hashes de herramientas y recibos están
en `evidence-work-20261019/`. Las rutas `/private` son ejemplos, no descargas públicas.

## Conservación y límites

Se respaldaron privadamente inputs y outputs reproducidos, sin APK, keystore ni
credenciales. El ZIP nuevo de inputs tiene SHA256
`069f02369676c96db4507f14b70abb95c29f75c9f28d3c80712b716a485b420b`;
no es el ZIP histórico173252… ni debe pasarse como tal al stager original.
El respaldo de outputs tiene SHA256
`1231c834ba67cb33f4ef4105de1748acd478b2061886b60c845e64d3cd40ba54`.

## Build Android completo y APK nueva sin firma

El checkpoint de herramientas `85e20675cbc142e64ad92e726dba5c15cd8efae3`
se publicó durante la compilación. La aplicación se compiló en el worktree
independiente de723580b5, cuyos archivos Android activos son idénticos a85e20675.
El único overlay Gradle es el documentado en `overlay.json`: wheelhouse experimental,
verificación offline de esos wheels y retirada de la asignación de firma Diagnostic.
No se cambió Gradle activo, locks originales, manifiestos, políticas o código del cliente.

| Comprobación ejecutada | Resultado |
|---|---|
| `:TMessagesProj:assembleDiagnosticDebug`, ARM64 | **BUILD SUCCESSFUL**,11m13s;248 tareas:209 ejecutadas,35 de caché,4 actualizadas |
| JNI y Chaquopy | Compilación completa, sin SKIP; CMake3.31.6/NDK27.2.12479018 |
| Paquetes Python |18 instalados desde wheels locales verificados;3 reconstruidos,15 originales |
| Identidad |`io.github.jose22yt.flexygram.diagnostic`, versión13.0.2/código1261,min24,compile37 |
| APK |`flexygram-v13.0.2(1261)-diagnostic-debug-unsigned.apk`,113080783 bytes |
| SHA256 |`ddb7b017838a2a13991ac09154bbf252a11d62326e9a588349ca03c115e01699` |
| Firma |**Ausente**, no certificado; apksigner rechaza por falta de firma; tampoco hay bloque APK ni entradas JAR de firma |
| CRC y zipalign |Válidos; `zipalign -c -P 16 -v 4` aprobado |
| ELF |97 inspeccionados:96 AArch64 objetivo,1 payload no objetivo de debugpy conservado y visible |
| PT_LOAD |96/96 cumplen4KB y16KB |
| API24 estática |Cero DT_NEEDED faltantes, símbolos fuertes sin resolver o conflictos de versión; sin bloqueadores de cierre/RELRO |
| Cuatro ELF reconstruidos |Bytes empaquetados coinciden con los cuatro hashes de la reconstrucción A/B |
| Guardas JNI |Tres métodos reales compilados como una instrucción ARM64 `RET`; `.text` del APK idéntica al JNI enlazado inspeccionado |
| Compilador JNI |1833 comandos únicos; únicamente `aarch64-none-linux-android24` |
| Aislamiento |API ID0/hash vacío; seis capacidades falsas y marcador Java/JNI concordante; sin INTERNET |
| Superficie |Solo launcher exportado habilitado; componentes/authorities revisados por el gate y mutaciones negativas |
| Traducción |73595 clases DEX, cero duplicadas; seis clases de fachada presentes una vez; sin AAR retirado ni dobles de laboratorio |
| Escaneo |APK, JAR fuente y201 artefactos externos: gate de claves/identidad retiradas aprobado |
| Dependencias |Los cuatro grafos Diagnostic Debug/Staging conservan los mismos identificadores de componentes que la evidencia histórica |
| Production |Prueba negativa real de Gradle: `FLEXYGRAM_PRODUCTION_INCOMPLETE`, sin APK de Production |

`apk-native-acceptance.json` devuelve **STATIC_CLEAN_PENDING_ANDROID**, no una
certificación. `apk-diagnostic-check.json` conserva el escaneo completo. El permiso
ACCESS_NETWORK_STATE y el permiso privado de receptor siguen presentes; INTERNET
está ausente. No se afirma ausencia universal de secretos o de cualquier tráfico
delegado solo por pasar este escáner.

La APK nueva no es la APK firmada histórica17c32…; ni su tamaño ni su SHA coinciden.
No se dispone de aquella para comparar todos sus bytes. No se afirma reproducibilidad
A/B del APK entero: la comparación reproducible fue de cuatro ELF/tres wheels.
El recibo de reconstrucción que indica `apk_built:false` describe esa etapa previa;
el build Android posterior consta en `unsigned-apk-receipt.json` y el log real.
Las copias públicas de logs solo normalizan tabs y espacios al final de línea;
`log-normalization.json` conserva los SHA256 originales y `evidence-sha256.json`
las huellas de los archivos publicados. Los originales permanecen en el entorno privado.

Advertencias conservadas: compatibilidad futura Gradle10, source/target8 en JDK21,
anotaciones opcionales, constructores Locale obsoletos, formatos/localizaciones sin
default y advertencias C/C++ heredadas. No se silenciaron ni se modificaron recursos
para conseguir el build. SDK Manager reinstaló SDK37r02 en un directorio alternativo
por la extracción manual previa; ambos android.jar tienen el mismo SHA256
`bf1b4387cc7ca94fc6ef684f040d9d16fbf16248e181819f020736ea2053f177`.
No se sustituyó la versión del SDK. `-Pkotlin.incremental=false` evita el camino incremental
ya investigado; este éxito no demuestra que aquella incidencia haya desaparecido.

## Android y siguiente puerta

Se recompiló el runner **sin firma**. No se arrancó ningún Android ni se instaló
ninguna APK. El inventario actual contiene ADB37.0.1, pero no emulator/QEMU ARM64,
imagen arrancada, KVM,TUN,CAP_NET_ADMIN o CAP_SYS_ADMIN. Esto describe este host;
no demuestra que ARM64 con TCG sea imposible en otro entorno preparado.
El contrato de laboratorio rechaza correctamente la APK nueva por digest/tamaño;
no se cambian sus pins ni se contabiliza ese rechazo esperado como Android aprobado.

La certificación API24/16KB requiere los dos laboratorios ARM64 y carga real
JNI/Python; no puede sustituirse por estos tests Linux ni por escáneres.
No se ha firmado, instalado, autenticado, distribuido o fusionado nada.

El contrato de laboratorio solo podrá adaptarse tras revisión explícita del nuevo
artefacto y de su firma, con custodia recuperable verificada antes de generar una
clave. Procedimiento y matriz: `ANDROID-INSTRUMENTATION.md` y `ANDROID-LAB-16K.md`.
