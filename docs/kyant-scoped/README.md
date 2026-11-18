# Kyant solo en la barra principal — beta.64

Rama: `codex/flexygram-kyant-scoped-performance`.
Base: `21a7dd3a5` (Native Test beta62 con optimizaciones de arranque y reparación
DNS). Paquete `com.flexygram.messenger.nativebaseline`, mismo esquema de firma.
Nueva versión beta64 / 1353 para actualizar también la prueba Kyant beta63.

Esta integración toma **solo el componente de la barra** de la rama experimental
`codex/flexygram-optimized-kyant` (933befdec). No incorpora su retirada del motor
óptico nativo ni sus cambios en conversaciones, carpetas, búsquedas o perfiles.
`LiquidGlassEffect.java`, su AGSL y las fábricas nativas se conservan.

## Ajuste y exclusión

Navegación y gestos → Barra de navegación inferior → Liquid Glass Kyant.
Una página nueva y un interruptor único; no reaparece el editor de destinos retirado.
Preferencia independiente `flexy_kyant_home_dock` en mainconfig, desactivada por
defecto. No modifica el bit Liquid Glass de Telegram ni enciende otras superficies.
Las preferencias de otros experimentos no se reinterpretan ni migran por fuerza.

La fábrica de fondo **solo de MainTabsActivity** tiene la refracción Telegram
expresamente prohibida. Cuando Kyant dibuja, la barra nativa no dibuja ni su fondo
ni sus selectores: no hay doble lente. Apagado, ahorro de energía, Android <13,
renderizado sin hardware o barra oculta usan el fondo nativo normal sin esa lente.
Las demás superficies conservan el comportamiento de Telegram de la base Native.

## Trabajo reducido

- Host Compose creado bajo demanda. Si el ajuste está apagado no se instancia.
  Encendido, espera una pantalla utilizable dibujada y una oportunidad idle de
  la cola principal, usando StartupIdleWork ya existente. Hasta entonces se usa
  la barra nativa; no se bloquea la apertura esperando el efecto.
- Un RenderNode por icono conserva icono/texto/badge. Las dos capas de Kyant
  reutilizan el mismo registro de View.draw hasta cambiar revisión o tamaño.
  Se libera al apagar, ocultar, cambiar destinos o separar la vista.
- La sincronización nativa reutiliza la lista temporal y el comparador; la lista
  Compose solo se reemplaza si cambia la identidad/orden de las pestañas.
- Invalidaciones de escena se agrupan una vez por frame, sin volver a recorrer
  ancestros cuando ya hay una captura pendiente. No se agregan timers ni tickers.
- Captura de fondo recortada al dock más su margen óptico. La densidad también
  invalida la geometría de captura. Fallar beginRecording/draw ya no deja el
  capturador permanentemente marcado como ocupado.
- Listener de configuración y callbacks se retiran al desprenderse; el trabajo
  de inicialización pendiente se cancela al destruir el fragmento.

El componente de la barra conserva la refracción, el brillo y los gestos de
Kyant. Se desactivan las sombras que rodeaban la barra y el selector. El host
reserva 24 dp de dibujo por encima de la barra cuando monta Kyant, con paso de
toques hacia la lista en esa franja. La captura del fondo conserva su tamaño.
Se conservan la procedencia SHA256 y la licencia Apache2.

## Validación

Tests JVM con clases reales y dobles Android contados para caché de iconos,
captura de escena, persistencia y listeners, más rutas de ajustes y huellas de
procedencia. Pruebas existentes de arranque se conservan. El workflow compila
el puente real con Compose y ejecuta las pruebas existentes de bounds LTR/RTL,
redimensionado y paso de gestos antes de ensamblar la APK con R8.

No hay SDK Android ni dispositivo conectados en este entorno. No se declara
una APK terminada ni FPS/latencia/potencia medidos. La compilación real se
solicita en GitHub y se deja sin seguimiento según la preferencia del usuario.
Prueba manual: ON/OFF y reinicio; entrar/salir de ajustes; chats/carpetas/badges;
tema y tamaño de fuente; RTL; rotación; esconder la barra; teclado y reproductor;
notificaciones y ahorro de energía. Comparar frame time con ON/OFF en el mismo
estado de datos, brillo y temperatura usando Perfetto.

Resultado final de host: **553 passed, 41 skipped** (suite completa), y 15 pruebas
focalizadas aprobadas. Sintaxis Java, XML, YAML y `git diff --check` correctos.
El SDK/harness Compose y el APK quedan para el workflow real, no se reportan
como ejecutados en este entorno. Se recuperaron las fuentes de Media3 y los
archivos de performance omitidos por el checkout local antes de la pasada final.

## Reparación del plugin de metadatos Lottie

El primer workflow beta64 falló en `buildSrc:compileKotlin`: la migración a
Kotlin JVM dejó un import de `org.gradle.kotlin.dsl.register` y lambdas con
receptores implícitos. Se sustituyen por `TaskContainer.register(name, type,
Action)` y acciones explícitas para el filtro de recursos; se conservan nombres
de tareas, entradas y registro de fuentes generadas de AGP.

Validación posterior: `compileKotlin` de buildSrc con Gradle 9.7.1/Kotlin 2.4.10
completado. Ejecución real de LottieMetaTask en un proyecto Gradle aislado produjo
`pack(R.raw.kyant_probe, 48, 120, false)` a partir de JSON con fr48/ip10/op130.
No se requiere SDK para esas dos comprobaciones; la APK completa se relanza en CI.

La segunda pasada superó Lottie/Kotlin, pero Java detectó un `dispatchDraw(Canvas)`
duplicado en el contenedor de MainTabsActivity. Se integra la solicitud idle de
Kyant al final del override nativo ya existente, conservando insets, dibujo y
actualización de fondos. La nueva regresión compila el contenedor anónimo completo
con dobles Android y comprueba una sola ejecución del dibujo antes de la solicitud
opcional. Resultado focalizado: 10 pruebas aprobadas; APK completa pendiente de CI.

## Mejoras de fuente posteriores, sin nueva APK

La inicialización de FileLoader se hace ahora por cuenta solicitada, sin crear
los diez slots desde ImageLoader. Se agrupan comprobaciones multimedia sin
callback y se conservan las barreras de las llamadas con callback. Ver
[IMAGE_STARTUP_LAZY.md](../native-test/IMAGE_STARTUP_LAZY.md). No cambia el material
Kyant ni las superficies de Telegram; no se inicia compilación en esta entrega.
