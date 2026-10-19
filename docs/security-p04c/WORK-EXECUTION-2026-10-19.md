# P0.4c: ejecución real de recuperación y reconstrucción

FlexyGram, responsable @Lukhou23. Continuación de PR17 desde
`723580b5cfee51416aa3f87cdebc3f8c911eb7ed`, siguiendo el comentario
`https://github.com/Jose22Yt/FlexyGram/pull/17#issuecomment-6279426562`.
No autoriza fusión, firma, distribución, Production ni Paso4.

## Resultados de este checkpoint

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

En este checkpoint el build Android experimental está en curso: **no se declara
todavía una nueva APK ni96 ELF inspeccionados**. El recibo de reconstrucción que
indica `apk_built:false` describe esa etapa, no un build Android posterior.
La certificación API24/16KB requiere los dos laboratorios ARM64 y carga real
JNI/Python; no puede sustituirse por estos tests Linux ni por escáneres.
No se ha firmado, instalado, autenticado, distribuido o fusionado nada.

El contrato de laboratorio solo podrá adaptarse tras revisión explícita del nuevo
artefacto y de su firma, con custodia recuperable verificada antes de generar una
clave. Procedimiento y matriz: `ANDROID-INSTRUMENTATION.md` y `ANDROID-LAB-16K.md`.
