# Native Test beta.61 — arranque y compilación optimizada

Base: `f0ce4ae91`, continuación de `codex/flexygram-native-clean-bubbles`.
Versión: `1.0.0-beta.61-native-test` / 1350. Paquete y firma de pruebas conservados.
No se restauran las funciones retiradas del perfil Native Test.

## Cambios activos en la APK

El workflow añade `-PflexyStartupOptimization=true` a los flags existentes
`flexyPerformanceBuild` y `flexyReleaseReduction`. Solo se permite para el paquete
Native Test. La tarea genera una copia de las reglas quitando únicamente
`-dontoptimize`; mantiene `-dontobfuscate`, reflexión, JNI y reglas de plugins.
La variante debug sustituye la lista de reglas, en lugar de añadir una copia
optimizada junto a otra que seguiría desactivando el optimizador.

El experimento anterior de `connectedAlpha` sigue disponible y separado. Las
reglas originales no se modifican. Las clases conservadas expresamente siguen
limitando lo que R8 puede transformar: activar R8 no significa optimizar cada
método de todo Telegram.

La comprobación de emojis y reglas de vistas previas se encola después del primer
dibujo del contenido, manteniendo su cola de trabajo original. Ya no empieza
mientras se construye la primera jerarquía. Se solicita una sola vez por Activity;
la destrucción elimina el callback pendiente. No se aplazan bibliotecas JNI,
autenticación, conexión, lecturas iniciales de SQLite o recuperación de mensajes.

La compilación de rendimiento reporta `reportFullyDrawn` después de dibujar
contenido utilizable: las listas requieren datos iniciales cargados y layout
completado; los chats requieren que termine su primera carga. Se resuelve el tab
visible dentro de ViewPagerActivity y no se reporta con la Activity pausada,
destruida o bloqueada por contraseña. El callback vuelve a comprobar el estado.
No hay polling ni callbacks persistentes de frame. Otras pantallas reportan su
vista visible y medida; esta señal no implica que toda su información de red esté
sincronizada.

## Perfiles: estado explícito

**Todavía no se han capturado perfiles propios en un dispositivo.** No se añaden
listas inventadas de métodos ni reglas para todo el paquete. Esta APK incorpora
R8 y el cambio de arranque anterior; no se atribuye a perfiles nuevos una mejora
que no se haya medido.

Se reutiliza el módulo opcional `performance`, antes dirigido a connectedAlpha.
Con `flexyStartupOptimization=true` usa debug Native Test; sin ese flag conserva
connectedAlpha. El workflow compila el harness con el SDK real, sin ejecutarlo ni
crear un emulador. ProfileInstaller ya estaba integrado y mantiene su uso.

El código fuente explícito de perfiles para AGP es
`TMessagesProj/src/main/generated/baselineProfiles`. Allí solo se importarán
`baseline-prof.txt` y `startup-prof.txt` obtenidos del dispositivo. La generación
existente marca únicamente el recorrido de arranque para Startup Profile; chat,
teclado, scroll y ajustes amplían el Baseline Profile.

El importador Native Test reutiliza la validación de recorridos del laboratorio
existente y añade comprobación de paquete, SHA del APK, commit y cambios de código.
Rechaza capturas incompletas, omitidas, fallidas, perfiles vacíos, comodines globales
y Startup Profiles sin cobertura en el Baseline Profile. Preserva el orden
capturado, importante para el layout DEX. Se conserva la interfaz del importador
anterior para Alpha. Una captura no demuestra por sí sola que ART ya la compiló.

## Laboratorio en Android conectado

Usar un dispositivo de laboratorio Android 13+ y una cuenta sintética ya iniciada,
con un chat sintético visible y mensajes cacheados. No se automatiza login, no se
publican trazas privadas y no se borran los datos de la aplicación. La instalación
del build de pruebas requiere una firma compatible; no desinstalar una app con
datos del usuario para resolver una firma distinta.

Ejemplo de generación, sustituyendo las etiquetas por las del dispositivo:

```sh
./gradlew -PflexyPerformanceTools=true -PflexyPerformanceBuild=true \
  -PflexyReleaseReduction=true -PflexyStartupOptimization=true \
  -Pandroid.testInstrumentationRunnerArguments.class=com.flexygram.performance.ProfileGeneration \
  -Pandroid.testInstrumentationRunnerArguments.flexy.fixtureChat=ContactoDePrueba \
  -Pandroid.testInstrumentationRunnerArguments.flexy.settingsLabel=Ajustes \
  :performance:connectedDebugAndroidTest
```

Si la navegación a Ajustes usa un menú, añadir `flexy.menuDescription` con su
etiqueta localizada. El tab nativo se usa directamente cuando está presente.
Recuperar del resultado de la instrumentación los archivos de perfiles generados
y el XML JUnit de las tres pruebas; el informe del APK está en los artefactos de CI.

```sh
python tools/startup_optimization/profiles.py \
  --baseline /ruta/captura/startup-baseline-prof.txt \
  --baseline /ruta/captura/chat-baseline-prof.txt \
  --baseline /ruta/captura/settings-baseline-prof.txt \
  --startup /ruta/captura/startup-startup-prof.txt \
  --junit-results /ruta/captura/TEST-ProfileGeneration.xml \
  --build-report /ruta/captura/startup-optimization.json
```

Los nombres efectivos los informa AndroidX. Importar sobre el mismo código que
produjo el APK y versionar los resultados. No usar perfiles de Telegram oficial
como si pertenecieran a este binario.

Para comparar, ejecutar `com.flexygram.performance.DeviceBenchmarks` con los mismos
flags y etiquetas, primero con `flexy.compilation=none` y luego con
`flexy.compilation=baseline`, después de construir e instalar el APK que contenga
los perfiles capturados. Los recorridos de arranque frío y caliente realizan 20
repeticiones; los demás cubren apertura, teclado, mensajes y ajustes. Conservar
JSON y trazas. No comparar tras borrar datos o cambiar condiciones térmicas/red.

## Verificación de entrega

`verify_apk.py` exige una configuración R8 efectiva sin `-dontoptimize` y con los
nombres conservados, registra SHA-256 y distingue perfiles propios de perfiles de
bibliotecas. Rechaza una pareja de perfiles incompleta o un perfil propio que no
se empaquete. El informe siempre mantiene `device_aot_verified=false`: comprobar
ART, el layout DEX y el impacto en teléfono requiere la fase de dispositivo.

No se promete un porcentaje de mejora. En esta tarea no se capturó ART, no se
midió FPS ni se ejecutaron recorridos Android. La compilación completa y su
resultado corresponden al workflow de GitHub Actions.

Validación de esta revisión: **544 pruebas pasadas y 41 omitidas**. La revisión
final de pertenencia a la ventana y arranque pasó 13 pruebas dirigidas. El
regresor ejecutó R8 real con optimización activada/desactivada y verificó nombres,
entradas reflectivas/JNI y eliminación de código. Los tres archivos del laboratorio
y el reporter compilaron contra APIs reales de Android y AndroidX, con avisos de
anotaciones ausentes en el classpath aislado. Sintaxis Java, YAML y
`git diff --check` verificados. Ningún resultado es una medición en teléfono.
