# Work2 — integración25 y cliente preparado para la siguiente APK

FlexyGram1.0, creado y dirigido por @Lukhou23. Base PR23
`e50fa88e80358893d08e9901e81e3b0a74a0a54d`.

## Integración revisada

PR25 revisado en `2363f38ccab1618a75fec790c04b78b6067e91bc` se incorpora en
`03bd1ce719c28dc73869f01717f46e9ba013b9e2`: sus14 archivos exactos, sin conflictos.
Incluye gate unificado, control del Application/LAUNCHER del manifiesto,
contenedores/verificación de integridad y compatibilidad PR24. No se duplica
NotificationCenter ni se revierten los commits0575a962/e50fa88e del cliente.
README/evidencias originales de PR25 son históricos; los resultados ejecutados
sobre la integración están bajo evidence-second-beta. No se edita la rama de Work1.

## Cambios del cliente y evidencia de fallos

- La Activity anterior siempre reconstruía Home. Ahora recupera Home/Conversation/Settings
  sintéticos y tema mediante **tres campos primitivos versionados**. Reconstruye la pila
  local sin reproducir intenciones pendientes ni animaciones de una Activity destruida.
  Los arneses comprueban vuelta a Home tras restaurar ambas rutas.
- Antes onDestroy restablecía el tema inicial incluso en cambio de configuración o
  cuando otra ruta había cambiado la referencia global de tema. Ahora conserva el tema
  en recreación y no sobrescribe una referencia de tema distinta de la que posee.
  Esto no es certificación de todos los escenarios multiwindow.
- Excepción RuntimeException/LinkageError inyectada en postInitApplication terminaba en
  cierre. Ahora detiene la construcción de componentes del cliente y muestra un TextView
  de plataforma con **POST_INIT_FAILED**, sin imprimir valores/trazas de la excepción.
  No intenta continuar sobre un cliente parcialmente inicializado. Fallos en
  Application.onCreate/ART anteriores a la Activity o en otras etapas siguen fuera
  de esta frontera: el fallback no demuestra que el arranque Android esté resuelto.
- ProbeState/LocalPythonProbe distinguen JNI_UNAVAILABLE, PYTHON_START_FAILED,
  PYTHON_IMPORT_FAILED y READY. Python continúa bajo demanda fuera de UI y sólo importa
  sys, sin plugins. READY describe Python inicializado/JNI cargado, no prueba todas las
  funciones JNI. Resultado de una Activity destruida se descarta; no se guarda éxito
  de runtime para atribuírselo a otro proceso.

No se restauran cuentas, sesiones Telegram, tokens, archivos ni preferencias ajenas.
Bundle guarda sólo versión/ruta/tema; rechaza tipos/esquemas/rutas desconocidos sin
registrar sus valores. Estado sintético de Activity no habilita Android Backup ni
restauración de sesiones. Diagnostic/Production, permisos, API0/hash vacío, servicios,
JNI, locks, contratos históricos, animaciones y protocolo de eventos sin cambios.

## Ejecución real

**46 métodos distintos PASS normal y -O:**25 cliente (20 anteriores +5 nuevos) y21
handoff. Cero skips/fallos/errores finales; no sumar repeticiones ni las367/85 históricas.
Java/Groovy/CMake reales en host; wrappers Activity/Android/Chaquopy con dobles explícitos,
no ART ni emulador. Tres métodos nuevos reproducen cinco aserciones fallidas antes del
arreglo: rutas/tema y fallo postinit inyectado. Registro rojo conservado.

Escenario CLI PR25→PR24 ejecutado en ambos modos, JSON idéntico y fuentes PR24 fijadas
read-only. Gate integrado rechaza APK deliberadamente ausente (exit1/BLOCKED); eso no
constituye revisión de un binario. [IDs, hashes y logs](evidence-second-beta/results.json).
No hay medición real de latencia, FPS, carga JNI/Python o compatibilidad Android.

## Puerta de compilación y conservación

**No se ejecuta Gradle Android ni se genera otra APK.** La evidencia revisada de PR25
registra HTTP403 antes de transferir54.5MB sintéticos; no hay APK/ZIP original recuperado
ni confirmación posterior de custodia en su discusión. No se repitió la subida ni se
intentó eludir403: almacenamiento y laboratorio físico siguen a cargo de Work1.
No se confunde una comprobación local con recuperación remota. No se toca la APK beta
histórica98de3527… ni se le atribuyen estos cambios.

También faltan en este workspace los insumos privados y SDK/NDK de la compilación
anterior. No se descargan/reconstruyen binarios para acabar con un artefacto sin custodia.
Recetas existentes, versiones JDK21/Gradle9.7.1/SDK37-35/BuildTools36/NDK27.2.12479018/
CMake3.31.6/Python3.11 y18 wheels experimentales fijados permanecen como requisitos.
No se cambian dependencias activas ni se reconstruyen4 ELF/3 wheels.

Una vez Work1 confirme custodia y recuperación íntegra, comandos preparados con rutas
privadas **nuevas** y SDK/submódulos fijados restaurados (no ejecutados aquí):

```sh
python3.11 tools/native_compatibility/prepare_experiment.py \
  --source "$BETA_SOURCE" --checkout "$BETA_BUILD" \
  --wheelhouse "$BETA_WHEELHOUSE" --manifest "$BETA_MANIFEST_COPY" \
  --python "$CHAQUOPY_BUILD_PYTHON" --unsigned
```

BETA_BUILD debe ser checkout hermano desechable del nuevo commit, no descendiente del
source. Usar copia del manifiesto/lock experimental en directorio privado nuevo: la
receta genera requirements-experimental.lock junto al manifiesto y no debe sobrescribir
las evidencias históricas. Insumos exactos verificados primero, claves/firma ausentes.
Desde ese checkout, exportar NATIVE_TARGET=arm64-v8a, JAVA_HOME y ANDROID_SDK_ROOT,
CHAQUOPY_BUILD_PYTHON al Python3.11 fijado, CMAKE al binario3.31.6 y añadir el directorio
de Ninja1.12.1 al PATH; después:

```sh
"$GRADLE_HOME/bin/gradle" --no-daemon --console=plain --max-workers=2 \
  -PflexygramBetaDevelopment=true :TMessagesProj:assembleBetaDevelopmentDebug
python3.11 "$BETA_SOURCE/tools/beta_handoff/gate.py" \
  --apk "$BETA_APK" --sha256 "$BETA_APK_SHA256" --classes "$BETA_CLASSES" \
  --build-tools "$ANDROID_SDK_ROOT/build-tools/36.0.0" \
  --ndk "$ANDROID_SDK_ROOT/ndk/27.2.12479018" --javap "$JAVA_HOME/bin/javap" \
  --output "$BETA_NEW_REVIEW"
```

BETA_APK_SHA256 se calculará del binario nuevo; no utilizar98de3527… como hash esperado.
BETA_CLASSES debe proceder de la misma compilación; ese control externo no sustituye
inspeccionar DEX/runtime. Conservar APK/clases/JNI/logs y comprobar recuperación íntegra
antes de descartar originales. Firma, instalación y distribución no están autorizadas.

Siguiente tarea concreta: Work1 aporta recibo de conservación y condiciones autorizadas
de prueba física; Work2 restaura sólo los insumos necesarios, compila unsigned en ruta
nueva y ejecuta el gate integrado. Luego, con aprobación independiente, primer arranque,
UI local, JNI/Python, exportación y12 casos nativos. Tamaño de página real se medirá;
API24/16KB no quedan certificados por un teléfono no verificado. No Paso4 ni autenticación.
