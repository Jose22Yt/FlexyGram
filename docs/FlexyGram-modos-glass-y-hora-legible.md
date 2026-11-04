# Modos de vidrio y legibilidad de la hora

Cambios sobre `codex/flexygram-beta-glass`, base `c475a9f8b`.
No se compila ni publica una APK con este trabajo.

## Comportamiento

Se conservan los interruptores originales en Ahorro de energía → Efectos en chats.
No se añade otro interruptor ni se recupera la pantalla Universal Glass retirada.

| Difuminado | Liquid Glass | Resultado |
| --- | --- | --- |
| Apagado | Encendido | Liquid Glass nativo, incluida su fuente de blur; no depende de Difuminado. |
| Encendido | Apagado | Blur con contorno de FlexyGram sobre la fuente nativa reducida; sin refracción. |
| Encendido | Encendido | Prevalece Liquid Glass nativo; no se superponen dos motores. |
| Apagado | Apagado | Las superficies de conversación y navegación usan su presentación de respaldo. |

Los límites de versión, los interruptores existentes de tema y el ahorro automático de batería se mantienen.
Las preferencias existentes de contorno siguen respetándose. El modo de FlexyGram reutiliza
la captura y el contorno nativos, con un tinte protegido para fondos extremos. No recupera el
motor Universal Glass eliminado, sus capturas adicionales ni sus ajustes por superficie.
La captura de blur continúa compartiéndose entre las superficies de cada pantalla.

Se corrige el refresco de chat: antes usaba Difuminado para decidir si activar la refracción
y podía ignorar el cambio entre modos porque el estado efectivo del blur no cambiaba.
La pantalla principal también actualiza el supresor, las superficies ya creadas y las claves
de caché al cambiar de modo. Los listeners se retiran al destruir la pantalla.
Los tintes automáticos siguen los valores nativos de cada modo; los tintes explícitos se respetan.

## Hora de las burbujas

`BubbleTimeContrast` conserva el color del tema cuando tiene contraste suficiente y lo
ajusta cuando es necesario. Se elimina por completo la tarjeta rectangular introducida
en la primera revisión. Si una superficie transparente o un gradiente impide resolver
el contraste con un único color, se protege únicamente el borde de los caracteres con
un halo fino de 1 dp, sin dibujar un fondo para la hora.

El objetivo de 4,5:1 se comprueba sobre el color cuando se puede conseguir con una tinta
uniforme. En los casos ambiguos se usa la separación entre tinta y halo, sin prometer
esa relación para cada píxel del fondo variable. No se captura la pantalla ni se muestrean
píxeles durante el scroll; los colores se conservan por celda hasta que cambia la entrada.
La tinta y el halo respetan el alfa de las animaciones. Se restauran el color y la sombra
originales del Paint compartido, incluso si ya existía una sombra personalizada. Las horas
sobre medios conservan su dibujo nativo.

## Trabajo de renderizado reducido

- La opacidad de un RenderNode cambia como propiedad de composición, sin regrabar su contenido.
- Repetir el mismo alfa no hace trabajo adicional. Pasar de invisible a visible conserva la
  notificación de posiciones nativa.
- El supresor de blur solo se reconstruye al cambiar entre modo con refracción y modo sin ella.
- Las fábricas actualizan las superficies existentes mediante referencias débiles y depuran
  las referencias muertas; no retienen las vistas o pantallas retiradas.
- Se corrige un `save()` sin pareja en la grabación del relleno del drawable nativo.

## Verificación reproducible

Pruebas generales:

```sh
python -m pytest tests/ -q -p no:cacheprovider
```

Regresiones específicas: `tests/test_glass_modes_time_contrast.py`. Ejecutan los métodos reales
extraídos de SharedConfig, ChatActivity, la fábrica y el drawable, con anfitriones de prueba
explícitos. Cubren interruptores independientes, cambios sin reabrir el chat, conservación
de caché, referencias débiles, alfa, tintes automáticos y contraste con fondos extremos,
intermedios y de color.

Canvas Android aislado:

```sh
python tools/bubble_time/android/run.py \
  --sdk-root /ruta/android-sdk --maven mvn \
  --output-dir /tmp/flexy-time-android-probe
```

Tres pruebas Robolectric API 35 con gráficos nativos ejecutan el método real de dibujo de la
hora, StaticLayout, Canvas y los Paint de Android. Los anfitriones de Telegram son dobles;
no se inicia la aplicación completa. La compilación Java del anfitrión usa el SDK API 37.
En este entorno se ejecutaron sin red usando Maven y el SDK instrumentado ya en caché.
El ejecutor compartido conserva un mensaje final histórico sobre música; el informe
`BubbleTimeAndroidTest` es la evidencia pertinente, con 3 pruebas aprobadas.

Límites: no se ha medido FPS, tiempo de arranque, consumo de GPU/batería ni comportamiento
completo en un teléfono. El acabado de refracción y las transiciones de todas las superficies
necesitan aceptación en dispositivo. Estas comprobaciones no equivalen a compilar la APK.

Resultado de la revisión inicial, antes de retirar el recuadro: **247 pruebas generales aprobadas y 31 omitidas**;
**2 pruebas de Canvas Android aprobadas**. El parser Java 21 acepta los 15 archivos
Java de producción modificados o añadidos; esto comprueba sintaxis, no compila la aplicación.
`git diff --check` no presenta errores de espacios ni marcadores de conflicto.

Corrección del recuadro: las regresiones de color y modos se vuelven a ejecutar, junto
con tres pruebas de Canvas Android. La nueva prueba comprueba que las esquinas y los
espacios del texto no se rellenan como una tarjeta, y que se restaura una sombra previa.
No se compila una APK ni se activa GitHub Actions para esta corrección.
