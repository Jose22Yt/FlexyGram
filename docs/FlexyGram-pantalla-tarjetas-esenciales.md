# Pantalla principal: Diseño esencial

El primer ajuste de Ajustes FlexyGram → Pantalla principal permite escoger Predeterminado o Diseño esencial. Es un selector de texto sin vista previa, conservado entre sesiones y portable mediante FlexyStudio. Debajo se encuentra el interruptor de líneas divisorias, conectado a la configuración existente de divisores y válido en ambos diseños.

## Presentación y navegación

- Cabecera fija: avatar, FlexyGram y una sola píldora con búsqueda y tres puntos. Reutiliza la fuente existente de blur/glass y sus restricciones; dispone de fondo opaco del tema cuando el efecto no está disponible.
- Buscar abre el editor existente y comparte su progreso de transición con la cabecera: no introduce un segundo animador independiente. El avatar abre el perfil; mantenerlo pulsado abre el selector de cuentas.
- Historias y accesos Guardados/Favoritos pueden recogerse con el scroll usando traslación. Las pestañas de carpetas tienen su desplazamiento limitado para permanecer debajo de la cabecera.
- Las conversaciones recuperan sus filas habituales, sin pintor de tarjetas adicional.
- Guardados se muestra solo como acceso superior en este diseño: la lista visible utiliza una proyección cacheada que excluye el diálogo propio. La lista del controlador no se elimina ni se reordena por esta ocultación. La búsqueda, el archivo y el diseño predeterminado conservan sus entradas.
- Favoritos conserva su carpeta existente y sus índices nativos. Su pestaña queda con ancho cero, sin contador/indicador visible ni foco accesible; el acceso superior abre esa misma carpeta. No se elimina ni se renumera ninguna carpeta del servidor.
- La selección de Favoritos compara el índice de la pestaña con el índice de la carpeta, no con su identificador del servidor.
- Mantener pulsado Favoritos abre el editor y buscador existentes. Solo se guarda al confirmar; respeta los límites y la cuenta. El identificador se almacena por cuenta y no se exporta.
- Nuevo mensaje, bloqueo y descargas siguen disponibles desde el menú superior. No hay botón separado para editar Favoritos.

## Cabecera de conversación, iconos y recursos

La cabecera de conversación activa utiliza el despacho normal de eventos de Android en lugar de la máscara de glass anterior. Los controles propios ya comprueban su geometría. Esto evita descartar los toques de llamar/menú antes de llegar a sus listeners. El menú se ancla al control visible. Se conserva el manejador existente de llamada y sus condiciones de disponibilidad.

Los iconos de teléfono, búsqueda, tres puntos, micrófono, clip, pegatina plegada y sonrisa son vectores de trazo uniforme basados en las referencias suministradas. La flecha de volver usa un trazo más fino en el modo correspondiente. Son dibujos propios; no se presentan como recursos oficiales de iOS.

El icono Glossy existente es el único alias habilitado en instalaciones nuevas, el fallback del controlador y la imagen inicial de Android 12+. Se conservan las selecciones explícitas existentes. En API 24/25 se reutiliza el mismo arte existente mediante alias de recursos.

Se corrigieron 51 formatos de recursos (37 cadenas base y `CloudConfigSyncDate` en 14 traducciones) para usar posiciones explícitas y compilar con AAPT2. Una prueba con el Formatter real verifica que no cambia el texto ni la numeración de argumentos, incluidos formatos mixtos. Tres textos de valoración que usan el formateador de spans y porcentajes literales se marcan como `formatted="false"`, sin alterar su contenido.

## Verificación y límites

Las pruebas JVM ejecutan la proyección de diálogos y su invalidación, el filtro de eventos de ActionBar, el cálculo de anchos de carpetas ocultas y el icono recordado. Las comprobaciones contra Android API 37/AndroidX compilan las clases nuevas de Home con dobles explícitos de servicios internos. También se valida sintaxis Java y recursos con AAPT2.

Pendiente de dispositivo: comprobar apertura/cierre/interrupción de búsqueda, scroll con y sin historias, arrastre de fijados, entrada a Favoritos y vuelta a otra pestaña, modo de selección, cuenta secundaria, claro/oscuro, fuentes grandes, RTL y actualización del launcher. Las pruebas host no miden FPS ni acreditan ausencia de jank.

La versión preparada es 1.0.0-beta.14 (1303). La validación oficial de Gradle se ejecutó y se detuvo por falta de las credenciales privadas de Telegram. El diagnóstico también confirma que no están provisionadas la clave de firma oficial y sus contraseñas ni Firebase Beta. No se genera una APK sin esas entradas y no se sustituye la identidad de firma.

Resultados de verificación de esta revisión: suite completa `tests`: **336 aprobadas y 33 omitidas**. Después se añadió y aprobó una prueba JVM adicional del arrastre de fijados con Guardados oculto, tanto en la lista general como en ambas páginas de carpetas. La sintaxis de los Java modificados/nuevos, los tipos de Home contra SDK 37 y los recursos principales con AAPT2 pasaron; `git diff --check` sin errores. Estas comprobaciones no son una compilación completa de la aplicación ni una prueba en dispositivo.
