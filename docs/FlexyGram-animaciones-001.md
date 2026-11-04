# Velocidad visual ×0,01 de FlexyGram

El factor de presentación es `FastMotionTiming.SCALE = 0.01`. No se escriben
ajustes globales del teléfono ni se solicitan permisos especiales.

## Interruptor de FlexyStudio

`FlexyStudio > Animaciones > Reducir animaciones` permite activar o
desactivar este comportamiento sin reiniciar. Queda activo por defecto para
conservar el comportamiento de la beta actual. La preferencia se guarda en
`flexygram_motion/fast_motion_enabled` y está incluida en la copia del cliente.

Al apagarlo, los animadores recuperan sus duraciones nominales, incluso al
reutilizarlos, y Android vuelve a aplicar su escala sin compensación. Los
resortes AndroidX recuperan su funcionamiento nativo; los relojes manuales y
resortes de burbujas consultan la escala Android. También se desactiva el camino
inmediato de entrada/salida de chats.

La interrupción de navegación con el mismo toque permanece activa en ambos
modos. El interruptor nunca condiciona `finishNavigationForInput` ni la entrega
del evento original. Se conservan las protecciones de gestos activos y modales.

Verificación del interruptor: 259 pruebas generales/Studio aprobadas y 31
omitidas por condiciones de entorno; 33 pruebas Android aisladas aprobadas
(8 del motor, 19 de Studio, 6 de navegación). Los fixtures de Studio se ajustaron
a la beta y su copia completa actuales: versión 1291, límite de
`StudioSchema.MAX_BYTES` y extensión sin distinción de mayúsculas. No se
modificaron esas políticas de importación. No se compiló una APK con este cambio.

Un plugin de compilación transforma las llamadas de presentación del módulo
principal a `Animator`, `ViewPropertyAnimator`, animaciones de vistas y resortes
AndroidX. Usa la API de instrumentación de AGP y su ASM existente; no añade
dependencias a la aplicación. El puente usa únicamente APIs públicas Android.

Para animadores Android se compensa la escala del sistema al comenzar. La
duración nominal se conserva para reutilizaciones y cambios de escala, evitando
aceleraciones acumulativas. Las duraciones positivas tienen un mínimo de 1 ms:
el redondeo y la frecuencia de pantalla impiden garantizar tiempos exactos de
×0,01 para cada animación. Si Android desactiva sus animadores, siguen desactivados.

También se aceleran el reloj de `AnimatedFloat`, la transición manual de
`ActionBarLayout` y la presentación/retorno de burbujas. Los resortes AndroidX
que admiten finalizar se llevan a su destino. Las animaciones heredadas agrupadas
se compactan; no se garantiza conservar sus proporciones temporales internas.

Los relojes `TimeAnimator` y animadores infinitos quedan excluidos. No se
reescriben `postDelayed`, servicios, tiempos de conexión, reproducción ni física
de desplazamiento. Esto reduce espera visual; no demuestra un aumento de FPS.
Las animaciones del lanzador, teclado y otras ventanas del sistema siguen bajo
control de Android, así que no equivale a cambiar las tres opciones ADB globales.

## Verificación del 4 de noviembre de 2026

- Suite `tests/`: **252 aprobadas, 31 omitidas** por sus condiciones de entorno.
- Pruebas aisladas Android de FastMotion: **5 aprobadas**; escalas ×0,01, ×0,5,
  ×1, ×1,5, ×5 y ×6, reutilización, callbacks, cancelaciones, VPA implícito,
  animadores agrupados, relojes excluidos y resorte AndroidX real.
- Regresiones Android de navegación: **4 aprobadas**.
- Compilación Java/Kotlin y validación del plugin `buildSrc`: correctas.
- Plan Gradle `:TMessagesProj:transformDebugClassesWithAsm --dry-run`: correcto;
  comprueba integración/configuración, no ejecuta la transformación de la app.
- Sintaxis Java 21 de los ocho archivos de producción cambiados: correcta.
- `git diff --check`: correcto.

No se ha compilado una APK con este cambio. Falta verificar la aplicación
completa en un dispositivo, incluidas transiciones, desplazamiento y ventanas
del sistema. Las pruebas aisladas no constituyen una medición de arranque o FPS.

## Nueva beta solicitada

La siguiente beta ARM64 incluye también las tarjetas agrupadas de ajustes,
iconos compactos, eliminación de flechas y corrección de fondos de las horas.
Se utiliza el workflow existente `ui-beta-debug.yml`, con sus credenciales de
compilación configuradas en GitHub. El resultado del workflow y su artefacto
deben comprobarse antes de considerar terminada la compilación.
