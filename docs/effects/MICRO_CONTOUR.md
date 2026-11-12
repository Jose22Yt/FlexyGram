# Microcontorno oscuro

Cuarta opción de Efectos de brillo. Adaptación Android de la referencia visual de
un borde de cristal oscuro y discreto; no se presenta como un port idéntico de
UIGlassEffect ni como una reproducción verificada de iOS 27.

## Comportamiento

- Valor persistido nuevo: 3. Se conservan GLARE=0, SOLID=1 y HIDDEN=2.
  El orden público anterior del selector tampoco cambia: Desactivar, Por defecto,
  Contorno sólido. Microcontorno oscuro se añade al final.
- No se migra ni modifica la preferencia de usuarios existentes. La clave y el
  setter originales siguen siendo los mismos. Los valores desconocidos siguen
  usando el efecto por defecto.
- Negro con alfa 36/255, grosor de 0,35 dp con mínimo de un píxel físico.
  Se respeta la transparencia de la superficie. Es un perímetro interior,
  estático; no agrega sombras, desenfoque, animaciones ni capturas adicionales.
- Se reutilizan los trazados y las cachés existentes del renderer blur3, incluyendo
  bitmap, color/NinePatch y RenderNode/Liquid Glass. El estado del modo forma parte
  de la clave de caché. Las curvas interiores se ajustan solamente en el modo nuevo.
- StrokeDrawable y las dos variantes del helper estático usan el mismo color y
  grosor. Los Paint prestados recuperan color, shader, estilo y ancho, incluso
  cuando falla una operación de Canvas.
- El enum de compatibilidad y el límite de importación de EtgBackup admiten el
  nuevo valor; los editores antiguos mantienen los tres valores anteriores.

## Superficies

La aplicación se realiza en el renderer compartido, sin listas de chats ni
condiciones por tipo de conversación:

- Cabecera de conversación y cápsulas de navegación/acciones.
- Entrada de mensajes y controles inferiores que utilizan el fondo nativo.
- Píldoras de carpetas: grupos, contactos, canales, bots y carpetas personalizadas.
- Barra inferior y superficies de navegación de la pantalla principal.
- Otras superficies que ya emplean blur3/StrokeDrawable o su helper de contorno.

No activa blur o glass en superficies que no lo tenían habilitado ni cambia
fondos opacos ajenos al sistema de efectos. Los tres modos anteriores conservan
sus colores, grosores y rutas de dibujo.

## Validación

Los probes JVM comprueban las cuatro correspondencias de preferencias y ambos
enums, retorno a los modos anteriores, ancho sin acumulación, ausencia de
reconstrucciones repetidas, contornos circulares/asimétricos y restauración de
Paint ante excepciones. Se mantienen los checks de compatibilidad de los métodos
históricos y el almacenamiento original.

El harness Android aislado incorpora además una prueba de píxeles negros con
alfa máximo 36 y centro transparente; no se declara ejecutada en esta tarea.
Queda pendiente la validación visual en un teléfono con temas claro/oscuro,
blur y Liquid Glass, todas las superficies indicadas y cambios repetidos de modo.
No se ha compilado una APK ni iniciado GitHub Actions.

Resultado final: **427 pruebas aprobadas y 39 omitidas**. Los XML de las tres
localizaciones pasan AAPT2 y los Java modificados pasan el análisis sintáctico.
No se ha realizado una medición física de tiempo de fotograma o memoria.
