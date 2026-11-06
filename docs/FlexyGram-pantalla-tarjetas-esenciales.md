# Pantalla principal: Tarjetas esenciales

El primer ajuste de Ajustes FlexyGram → Pantalla principal permite escoger Predeterminado o Tarjetas esenciales. Es un selector de texto sin vista previa. La selección se conserva y también se puede exportar mediante FlexyStudio.

## Comportamiento

- Cabecera fija con avatar, buscador y menú. El avatar abre el perfil; mantenerlo pulsado abre el selector de cuentas.
- El buscador activa la búsqueda existente. Las superficies reutilizan la fuente de blur/glass de la pantalla principal y respetan sus restricciones; cuando no está disponible usan un fondo opaco del tema.
- Marca, historias, accesos Guardados/Favoritos y pestañas de carpetas debajo de la cabecera. Las conversaciones se dibujan como tarjetas conservando el adaptador y las acciones existentes.
- Favoritos se configura exclusivamente con pulsación larga: abre el editor de carpetas con su selector y buscador existentes. La carpeta solo se guarda al confirmar en el editor, respeta los límites de la cuenta y se abre como otra pestaña de conversaciones.
- Los identificadores de Favoritos se guardan por cuenta y no se exportan: una configuración importada no debe apuntar a una carpeta de otra cuenta.
- Nuevo mensaje está en el menú superior. No se añade un botón de editar a Favoritos.
- Fondos, textos, selección y acentos usan claves del tema, con actualización al cambiar entre claro, oscuro y otros temas.

## Implementación y comprobaciones

`app/flexygram/home` contiene la preferencia, selector, cabecera, accesos y pintor de tarjetas. La integración conserva los índices y tamaños de las filas del adaptador nativo. El pintor reutiliza Paint/RectF durante el scroll; no añade sombras, capturas propias ni un bucle de animación.

`tests/test_home_essentials.py` comprueba preferencias por cuenta, normalización, recursos, navegación al editor existente y reutilización de objetos en 20.000 dibujos. `tools/home_essentials/check_types.py` comprueba los tipos de las cinco clases nuevas contra Android API 37 y AndroidX Core; los servicios internos de la aplicación son dobles explícitos. Esto no sustituye una compilación completa ni una prueba visual.

## Validación pendiente en dispositivo

Probar cambio de estilo y vuelta al predeterminado; búsqueda y cierre; selección múltiple; scroll con/sin historias; pestañas y animaciones; cuenta secundaria; carpetas bloqueadas o eliminadas; cambios de tema con la pantalla abierta; tamaños de letra grandes y RTL. Medir frames durante scroll y transiciones antes de afirmar mejoras de rendimiento. No se ha compilado una APK para este cambio.

## Alcance de las pruebas

La ejecución indiscriminada de pytest desde la raíz también recoge herramientas históricas y pruebas vendorizadas de BoringSSL: su recopilación falla por módulos de googletest/googlemock ausentes y dos aserciones históricas ajenas a esta interfaz. La suite mantenida del cliente se ejecuta explícitamente con `python -m pytest -q tests`. No se modificaron esas dependencias ni se ocultaron sus fallos.

Resultados de esta revisión: suite `tests`: 329 pruebas aprobadas y 33 omitidas; siete pruebas específicas de esta interfaz aprobadas (incluida la comprobación SDK añadida al final). Sintaxis de todos los archivos Java modificados y nuevos validada, y `git diff --check` sin errores. No se midieron FPS ni se ejecutó la aplicación en un dispositivo.
