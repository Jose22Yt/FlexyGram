# Diseños limpios, ticks iOS y hora pequeña sobre Native Test

Base instalada y verificada: `04ebd253b41abe23ca1ff388291eb181debfcfaa`
(`1.0.0-beta.59-native-test`, app separada).
Rama de esta continuación: `codex/flexygram-native-clean-bubbles`.

## Alcance

Ajustes de FlexyGram → conversaciones → burbujas: tres opciones de selección
única, Telegram (predeterminada), FlexyGram e iOS 27. La última recupera la
geometría de Telegram para iPhone ya presente en el proyecto, cuya procedencia
se documenta en `tools/ios_bubbles/provenance.json`; no introduce otro renderizador.
El selector usa tres filas radio nativas y un interruptor de hora pequeña,
sin vista previa animada ni capturas del wallpaper. Se mantienen los demás cambios de Native Test y la instalación
separada; no se restaura el sistema completo de personalización.

## Trabajo de dibujo y configuración

- Solo se leen `shape` y `small_timestamp` de `flexygram_bubbles`, una vez al cargar el perfil, o al
  pedir `reload()` expresamente. Los getters usados al dibujar leen el snapshot.
  Repetir la selección actual no guarda otra vez ni refresca la lista.
- Las preferencias de materiales, bordes, transparencia y blur no se consultan.
  Sus setters regresan antes de leer preferencias o modificar el snapshot en
  este perfil. No se borran preferencias del perfil completo.
- La forma se dibuja con el Paint nativo y el caché de geometría por celda de
  MessageDrawable. Selección, alfa, máscaras y degradados conservan la ruta nativa.
  El identificador de forma ya forma parte de la clave del caché.
- El perfil limpio no crea los Paint extra de materiales, SignatureBorderPath
  ni BubbleFusion. No entra en la ruta de superficies ni en el proveedor de
  wallpaper/glass. Las formas personalizadas tampoco generan un bitmap ni una
  pasada de sombra adicional. Telegram conserva su ruta original NinePatch.
- Al volver al chat, un cambio real de forma invalida las celdas visibles una
  sola vez, sin recargar mensajes ni reconstruir la conversación. Al cambiar la hora
  pequeña, se notifica al adaptador una vez para volver a medir los StaticLayout
  de las celdas visibles a 9 dp o al tamaño nativo. El Paint compartido de otros
  metadatos conserva su tamaño. El primer
  arranque y las reaperturas sin cambios no añaden esta invalidación.

No se reactiva FastMotion, FlexyFiles, Studio, dock personalizado, reproductor
FlexyGram, efectos de borrado o panel de interacción personalizado.

## Comprobaciones

- Suite de repositorio: 528 aprobadas, 41 omitidas; se conservan las omisiones de
  entorno de la base. La prueba de refresco añadida después de la colección de
  esa suite se ejecutó en la comprobación focalizada siguiente.
- Comprobación final focalizada: 29 aprobadas; configuración real Java con
  preferencias que fallan al acceder a efectos, selector y refresco por cambio.
- Robolectric API35 / gráficos nativos Skia, compilación del harness contra API37:
  6 pruebas aprobadas. Diferencia de siluetas, restauración de píxeles Telegram,
  reutilización del Path por generationId, selección/alfa/shader nativos,
  grupos/medios/entrada/salida, bloqueo de efectos y ausencia de auxiliares.
  Los hosts de Telegram son dobles explícitos; MessageDrawable, BubbleConfig,
  BubbleStyle, IosBubbleShape y los gráficos Android son reales.

Estas pruebas comprueban corrección y reutilización del trabajo; no constituyen
mediciones de FPS ni de tiempo de arranque en un teléfono. No se compiló una
nueva APK. Esta rama no está incluida en los disparadores de compilación por
push del workflow de APK. La APK anterior y el respaldo beta.58 siguen intactos.

## Restauración de ticks y tiempo

Se recuperan los vectores iOS de 11×9 dp y sus posiciones de FlexyGram anterior,
incluidos texto, medios, stickers, selección y la lista de chats. La prueba
compara exactamente `drawStatusDrawable` y el bloque de recursos de Theme con
el respaldo `9b305e3ee7ee16097576d60af07f6ed9f105de9c`. Los recursos no se
recrean en cada frame; permanecen en el ciclo de carga del tema. No se modifica
la lógica de estados enviado/leído ni sus transiciones.

“Hora pequeña” vuelve como interruptor persistente, apagado por defecto. Se usa
el tamaño existente de 9 dp y la implementación previa de medida/dibujo, sin
panel, borde, blur ni sombreado añadido. Las dos preferencias se cargan juntas,
y los getters usados durante el scroll no acceden a disco. Los otros efectos
siguen bloqueados.

Validación adicional: 9 pruebas gráficas iOS/estilos, 4 pruebas Android de hora
con la configuración real Native Test, y comparaciones con el código respaldado.
No se construye una APK; el ejecutable gráfico es solo un harness JVM aislado.

Comprobación final de esta restauración: suite general con **531 aprobadas y
41 omitidas**, sin nuevas omisiones. Sintaxis Java y `git diff --check` correctos.
La comparación exacta con el respaldo y los 13 casos gráficos anteriores pasaron.

## beta.60: limpieza de ajustes y compilación

La versión `1.0.0-beta.60-native-test` (1349) conserva el paquete separado
`com.flexygram.messenger.nativebaseline`. Se retiran del plan de navegación
las secciones de bordes/reflejos, animaciones personalizadas y dock configurable;
los enlaces antiguos vuelven a una pantalla válida. También se ocultan las
filas antiguas de interacción personalizada, contorno glass y navegación
personalizada en los editores secundarios, para que no reaparezcan en búsqueda.
La restauración del estado de una sección retirada vuelve a su vista general.
Los controles nativos de exteraLess, burbujas limpias y hora pequeña se conservan.
La copia beta.58 sigue separada e intacta.

## beta.61: arranque y optimizador

La continuación integra R8 optimizador conservando nombres/JNI/plugins, trabajo
auxiliar tras el primer dibujo y adaptación del laboratorio de perfiles a Native
Test. Estado real de perfiles, comandos y límites en [STARTUP_BETA61.md](STARTUP_BETA61.md).
