# Velocidad visual ×0,01 de FlexyGram

El factor de presentación es `FastMotionTiming.SCALE = 0.01`. No se escriben
ajustes globales del teléfono ni se solicitan permisos especiales.

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
