# Beta 38: iconos predeterminados

Origen: `FlexyGram_Iconos_Extraidos_Exactos_v2.zip`, proporcionado por el propietario. Sus notas de instalación son documentación del archivo, no instrucciones adicionales del usuario. Se usan los 109 símbolos principales y diez símbolos complementarios de la hoja B (incluido Plugins), sin redibujar ni modificar los PNG. Los duplicados de las otras hojas, láminas de presentación y variantes duplicadas no se empaquetan. La base rasterizada proviene de las variantes blancas del ZIP (`drawable-night-*`) para admitir tanto filtros `MULTIPLY` como `SRC_IN`. Se empaquetan como recursos normales y el tinte del tema determina su color final claro/oscuro, conservando la misma silueta alfa. `tools/exact_icons/assets.json` registra archivo de origen y SHA-256 por recurso.

Los 119 símbolos tienen mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi: 595 PNG, 1.300.230 bytes sin comprimir. Android selecciona y reutiliza la imagen adecuada. Cada vista recibe un Drawable independiente para sus límites, transparencia y tinte. No hay decodificación ni búsquedas de nombres durante `draw`, ni efectos de blur, callbacks periódicos o capas añadidas por estos iconos.

`tools/exact_icons/generate.py` genera 477 asociaciones por nombres explícitos. Se preservan las dimensiones lógicas de los controles originales. No se sustituye un estado distinto por un símbolo aproximado: teclado, fin de llamada, desfijar, anterior/siguiente, repetir una y herramientas de recorte/rotación conservan su recurso cuando el archivo no proporciona equivalente. Los iconos pintados directamente por componentes y las animaciones Lottie ajenas al composer siguen sus rutas existentes. La selección Solar/Remix/Cupertino y las sustituciones importadas mantienen su prioridad; el nuevo conjunto corresponde a Predeterminado.

El cargador cubre actividades y contexto de aplicación, además de los controles de conversación que antes evitaban la sustitución. El botón del composer usa sticker para abrir emojis/stickers tanto compacto como normal. El teclado sigue significando volver a escribir. No se cambian gestos, destinatarios ni funciones del panel.

| Categoría | Símbolo del archivo |
| --- | --- |
| Conversaciones | Mensaje con tres puntos |
| Pantalla principal | Paleta |
| Navegación y gestos | Controles |
| AyuMoments | Megáfono |
| Plugins | Rompecabezas de hoja B |
| FlexyFiles | Carpeta |
| Archivos y descargas | Descargar |
| Sistema y comportamiento | Panel de cuatro módulos |
| FlexyStudio | Capas |
| Acerca de FlexyGram | Globo |

Los iconos de ajustes pasan de 24 a 36 dp. Las filas principales conservan una altura mínima de 56 dp, márgenes para el texto, RTL y expansión por fuente grande. La envoltura aplica el primer plano del tema al símbolo y no utiliza `saveLayer` ni fondos individuales. Se conserva la caché de enlace de filas y sus fondos/ripples reutilizados.

Resultado de la suite completa: **368 correctas, 39 omitidas, 0 fallos**. Las omisiones corresponden a SDK/AndroidX, corpus externo y herramientas no disponibles. Las pruebas específicas del cargador y de ajustes sí se ejecutaron.

Validación: integridad de los 595 PNG; regeneración determinista; referencias de recursos; prueba JVM del cargador real con IDs no finales, reutilización de píxeles, tinte por vista, densidad explícita y desactivación ante packs opcionales; regresiones de ajustes y composer. No se compila APK por indicación del propietario. El entorno no incluye SDK API 37/Build Tools 36; queda pendiente validar el render en dispositivo con temas claro/oscuro, RTL y fuente grande, y medir jank/FPS durante scroll. No se afirma una cifra de fluidez sin esas mediciones.
