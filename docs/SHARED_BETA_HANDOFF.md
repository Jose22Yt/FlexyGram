# Entrega compartida: ajustes, movimiento e interfaces de chat

Rama: `share/flexygram-settings-motion-menus`.

La integración conserva como antecesor `5c398e0f5b375ee46770b6742ce856dca73a2683` y añade los commits locales de rendimiento y UI `940b912725`, `f24e67248b` y `ffab970a8e`. Se hizo un merge sin reescribir la historia publicada.

## Contenido integrado

- Se conservan el menú de mensajes con sus cuatro diseños, la selección de acciones, el interruptor **Reducir animaciones**, las correcciones de navegación y los márgenes de ajustes de la rama compartida.
- **Burbujas de chat**: filas a todo el ancho y tarjetas separadas en Apariencia, Borde y Fusión. La vista previa queda fuera de los grupos.
- **Signature Floating**: opción adicional en la galería horizontal de interfaz superior. Nombre centrado sobre toda la tarjeta, foto hasta el extremo y desvanecida hacia la mitad, estado nativo en una píldora separada 8 dp y revelado al abrir el chat.
- **Interfaz inferior**: vistas previas de 64 dp, tarjetas más compactas y controles debajo para Normal/Compacto/Muy compacto, posición vertical y restablecimiento. Los controles se aplican al estilo Compacta y reutilizan las preferencias y la geometría nativas existentes.
- **Rendimiento**: reutilización acotada de geometría para las secciones y conservación segura de las imágenes publicadas por la vista previa del fondo.
- FlexyStudio conserva el identificador del nuevo estilo superior y las preferencias existentes de tamaño/posición de la entrada.

La píldora Floating usa `FastMotionTiming.duration(220)` con el reloj local del revelado: sigue el interruptor de FlexyStudio, la escala de Android cuando corresponde y la desactivación de animaciones del sistema. No se reescriben texto ni medidas del editor para animarla.

## Validación de esta integración

Comando ejecutado con Python/Pytest y el JDK preparados en el entorno:

```sh
python3 -m pytest tests/ tools/connected_alpha/test_flexystudio.py tools/connected_alpha/test_composer_reference.py -q
```

Resultado: **272 pruebas correctas, 33 omitidas y 9 subcasos correctos**. Incluye los nuevos menús de la rama, preferencias de movimiento, geometría/posición de las vistas previas, agrupación, conservación de fondos y exportación/importación.

También se compilaron las clases reales de renderizado, configuración, galería, tarjetas y controles contra Android API 37 con dobles explícitos de los servicios del proyecto. El contenedor nativo modificado pasó el análisis sintáctico Java. No es una compilación completa de la aplicación ni una prueba de FPS/IME en un dispositivo.

No se generó APK. Los commits de esta entrega usan `[skip actions]` para omitir los workflows de push. Las auditorías históricas que congelan fuentes de versiones antiguas se describen en el informe del editor inferior y no deben confundirse con la suite actual anterior.

Detalles de los cambios:

- [Tarjetas del editor de burbujas](settings3/BUBBLE_EDITOR_CARDS.md)
- [Signature Floating](settings3/FLOATING_CHAT_HEADER.md)
- [Galería y controles inferiores](settings3/COMPOSER_GALLERY_CONTROLS.md)
- [Revisión de rendimiento](performance-current/REVIEW.md)
- [Menú de mensajes de la base compartida](FlexyGram-menu-mensajes.md)
