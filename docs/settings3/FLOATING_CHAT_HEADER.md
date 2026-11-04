# Signature Floating

Estilo opcional `4`, añadido al final de la galería horizontal de **Chat → Interfaz superior**. Los estilos anteriores conservan sus identificadores y la selección actual no se cambia automáticamente. El selector anterior de cabecera también permite elegirlo.

- El nombre se centra horizontalmente en **toda** la tarjeta, incluida la foto, y verticalmente sin sumar la altura del estado. Los nombres largos usan la elipsis nativa.
- La foto nativa ocupa el extremo completo, sin margen ni recorte circular. Su máscara de opacidad acaba cerca de la mitad de la tarjeta. No se crea otro `ImageReceiver` para el chat ni se aplican desenfoques a la imagen. Sin foto se conserva la inicial nativa.
- La conexión/última vez se presenta en una píldora independiente con **8 dp de separación**. Se reutiliza el subtítulo real de Telegram, incluidos sus cambios de conexión y escritura; no se inventan estados ni se modifican las reglas de privacidad.
- Una entrada de **220 ms nominales** desplaza y desvanece únicamente la presentación de la píldora desde detrás de la tarjeta. Su espacio se reserva antes del primer dibujo: no anima medidas ni mueve el historial. Usa un reloj local con la duración de FastMotion: sigue el interruptor **Reducir animaciones** de FlexyStudio y, al desactivarlo, la escala de Android. Respeta las animaciones desactivadas del sistema. No modifica la navegación global.
- La animación termina sin seguir solicitando frames y se reinicia al adjuntar/activar el estilo. No utiliza temporizadores ni conserva vistas en tareas pendientes.
- Los colores siguen el tema. Se conservan los controles nativos de retroceso, perfil, llamadas, menú y contador, con sus áreas táctiles. Las ventanas muy estrechas o fuentes que no caben utilizan la ruta Adaptive ya existente.

La tarjeta de la galería comparte geometría, máscara y superficies con el encabezado real. Su avatar de demostración usa una inicial local; la foto del contacto se muestra en el chat real. La vista previa se escala si el ancho disponible es pequeño para mostrar el diseño completo dentro de la tarjeta.

FlexyStudio acepta y conserva el estilo `4` en las configuraciones portátiles. Se mantiene el formato de archivo existente; el codec prueba su exportación/importación y rechaza identificadores fuera de rango.

## Verificación

- Suite `tests/` y `tools/connected_alpha/test_flexystudio.py`: **262 pruebas correctas, 33 omitidas** por las condiciones de sus suites.
- Pruebas JVM de geometría para densidades, anchos, contadores, llamadas y LTR/RTL; nombre centrado con textos de diferentes longitudes; separación del estado; restauración de preferencias; fin y reinicio del movimiento.
- Compilación de las clases reales de geometría, configuración, renderizado, máscara y vista previa contra Android API 37, con dobles explícitos para los servicios del proyecto. Análisis sintáctico del contenedor nativo modificado y de los selectores.

No es una compilación completa del cliente ni una prueba visual/de FPS en un teléfono. No se genera APK ni se publica la rama.
