# Apariencia inicial sin personalización

Las preferencias ausentes usan la presentación original. Se respetan los valores
explícitos guardados; no se ejecuta un restablecimiento global al iniciar.

- Burbujas: «Por defecto» (ID 2) utiliza el renderer nativo, el radio guardado de
  Telegram y su color/tamaño original de hora. Los IDs 0 (adaptativo) y 1
  (anterior) se conservan. El radio inicial nativo es 17; la transparencia inicial
  es 0 y los bordes, la fusión y el blur no se activan solos.
- Al elegir «Por defecto» se omiten los efectos de superficie sin borrar sus
  parámetros. Volver a un material personalizado recupera lo configurado.
- Cabecera: estilo original (ID 1), sin contador ni adaptaciones activadas.
- Entrada de mensajes: original, sin glass ni iconos de referencia. Restablecer
  esa sección también vuelve al estilo original.
- Menú de mensajes: interacción nativa; se conserva la migración del antiguo
  `tap_panel` cuando está guardado. Su restablecimiento vuelve al modo nativo.
- Navegación Signature/flotante, dobles toques y reducción de animaciones:
  desactivados inicialmente. Las correcciones de interacción siguen disponibles.
- Blur y Liquid Glass: apagados en instalaciones nuevas para todas las clases de
  rendimiento, incluso si el servidor incluye esos bits en sus presets. Las
  políticas ya guardadas y su migración se conservan. El blur del visor de fotos
  también queda inicialmente apagado.
- Iconos: recursos originales. Cupertino continúa disponible como elección
  explícita (ID 3), junto a Solar y Remix; su pulso de iconos requiere ese pack.
- Otros estilos visuales opcionales (miniavatares, FAB cuadrado, avatar gooey,
  reproductores MD3 y menú glass) quedan inicialmente apagados. Se mantienen las
  funciones originales de Telegram, como los temas por conversación.

FlexyStudio refleja estos valores en sus catálogos y esquemas. Un preset que
contenga el nuevo ID de superficie 2 requiere la futura versión 1303 o posterior;
los presets anteriores siguen aceptándose. Este trabajo no incrementa la versión
ni genera una APK.

Verificación: pruebas JVM de preferencias vacías, activación, recarga,
restablecimiento y compatibilidad con claves antiguas; pruebas de políticas de
rendimiento con todas las clases de dispositivo. La suite de gráficos/táctil de
Cupertino verifica el pack opcional y la ausencia de sustituciones en los packs
0/1/2. No sustituye una prueba física de instalación limpia.
