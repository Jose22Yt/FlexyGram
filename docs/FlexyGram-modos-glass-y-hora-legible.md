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

`BubbleTimeContrast` conserva el color del tema cuando tiene contraste suficiente. Si es
necesario lo ajusta y, cuando una superficie transparente o un gradiente impide garantizar
contraste con un único color, dibuja un respaldo pequeño detrás de la hora. No se captura
la pantalla ni se muestrean píxeles durante el scroll. El cálculo se conserva por celda y
solo se repite al cambiar sus colores de entrada.

La comprobación contempla también fondos intermedios: comprobar únicamente blanco y negro
podía dar un falso resultado favorable para texto gris sobre una burbuja transparente.
El objetivo de contraste es 4,5:1 para la hora completamente visible. Las animaciones siguen
respetando su alfa. Las horas sobre medios conservan el dibujo nativo. Se restaura el Paint
compartido para no afectar a otras celdas o textos.

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

Dos pruebas Robolectric API 35 con gráficos nativos ejecutan el método real de dibujo de la
hora, StaticLayout, Canvas y los Paint de Android. Los anfitriones de Telegram son dobles;
no se inicia la aplicación completa. La compilación Java del anfitrión usa el SDK API 37.
En este entorno se ejecutaron sin red usando Maven y el SDK instrumentado ya en caché.
El ejecutor compartido conserva un mensaje final histórico sobre música; el informe
`BubbleTimeAndroidTest` es la evidencia pertinente, con 2 pruebas aprobadas.

Límites: no se ha medido FPS, tiempo de arranque, consumo de GPU/batería ni comportamiento
completo en un teléfono. El acabado de refracción y las transiciones de todas las superficies
necesitan aceptación en dispositivo. Estas comprobaciones no equivalen a compilar la APK.

Resultado de esta revisión: **247 pruebas generales aprobadas y 31 omitidas**;
**2 pruebas de Canvas Android aprobadas**. El parser Java 21 acepta los 15 archivos
Java de producción modificados o añadidos; esto comprueba sintaxis, no compila la aplicación.
`git diff --check` no presenta errores de espacios ni marcadores de conflicto.
