# Ajustes compactos de FlexyGram

Se mantienen las diez categorías principales. Las seis categorías con grupos
extensos —Pantalla principal, Conversaciones, Navegación, AyuMoments, Plugins y
Sistema— son índices compactos de apartados, con las mismas preferencias y
callbacks nativos. Archivos, FlexyFiles, FlexyStudio y Acerca de se mantienen
directos porque ya contienen pocos controles o información estática.
No se migra, reinicia ni duplica ninguna configuración.

## Organización

- Pantalla principal: lista y título, movimiento y desplazamiento, mini píldoras, avatares, carpetas,
  elementos visibles y opciones adicionales de apariencia.
- Conversaciones: interfaz inferior, interfaz superior, burbujas y menú;
  mensajes y respuestas, menús y acciones, multimedia, stickers, bordes y
  reflejos, información de miembros, conversiones y animaciones.
- Sistema: comportamiento general, red y transferencias, notificaciones y batería,
  mapas, contactos, archivo, fuentes, superficies y efectos, icono de aplicación,
  privacidad y diagnóstico, y opciones adicionales. Packs de iconos, emoji, nube
  y código de acceso siguen siendo accesos directos a sus gestores existentes.
- Navegación: barra inferior, comportamiento, gestos, opciones adicionales y
  editor de navegación.
- AyuMoments: modo fantasma, privacidad de historias, guardado e historial,
  filtros y transferencia de base de datos, y desactivación/limpieza. Las
  confirmaciones y los callbacks de acciones delicadas permanecen intactos.
- Plugins: accesos a plugins, IA, traductor y PillStack; preferencias de traducción
  en un apartado propio. Los gestores se crean únicamente al abrirlos.
- Archivos mantiene sus dos controles de carpeta y ruta; FlexyFiles conserva
  activación y ayuda; FlexyStudio conserva exportar, importar y compartir, ahora
  con tres dibujos distintos. Acerca de conserva su diálogo de información.
- Los cuatro accesos de diseño tienen dibujos distintos. También se distinguen
  los accesos de sistema y plugins. Se reutilizan recursos existentes; los
  iconos originales de Telegram iOS se tintan con el tema actual.
- Mini píldoras: selector de una fila que muestra el valor actual y abre un
  diálogo de opciones. La demostración se crea solamente al solicitarla y se
  puede ocultar. Las cuatro opciones conservan sus valores persistidos.

Los controles mantienen sus dimensiones legibles y áreas táctiles. Cada apartado
usa un único RecyclerView y crea solamente los adaptadores necesarios. El índice
principal de Pantalla principal pasa de ocho controladores a uno de enlaces;
el de Conversaciones, de doce a dos de enlaces. Sistema, Navegación, AyuMoments
y Plugins también construyen solamente enlaces en sus índices, sin crear allí
los editores ni cargar sus preferencias. Estos son conteos estructurales,
no mediciones de tiempo de fotograma ni promesas de rendimiento en dispositivos.
No se agregan bucles, desenfoque, tareas periódicas ni trabajo al iniciar la app.

Se guardan categoría, apartado y posición de desplazamiento. La búsqueda y los
enlaces antiguos resuelven el apartado específico. El reciclaje de la vista
previa vuelve a conectar la vista al controlador al mostrarla de nuevo.

## Comprobación manual pendiente

1. Abrir Pantalla principal: comprobar los siete accesos y que no se cargan
   demostraciones en el índice. Entrar en cada apartado y volver.
2. Abrir Conversaciones: comprobar los cuatro iconos de diseño y los ocho
   apartados. Cambiar una preferencia y confirmar que se conserva al volver.
3. En mini píldoras, probar los cuatro modos; mostrar, ocultar y volver a mostrar
   la demostración; cambiar de modo con la demostración visible.
4. Buscar esquinas de avatares, contador de carpetas, mini píldoras, HDR,
   stickers, bordes y conversiones. Verificar que se abre y destaca el control.
5. Probar enlaces compartidos antiguos para esos mismos controles.
6. Probar rotación/recreación, volver atrás y restauración del desplazamiento.
7. Recorrer las diez categorías, incluidas Sistema, Navegación, AyuMoments y
   Plugins. Cambiar controles de red/notificaciones/mapas y verificar su persistencia.
8. En AyuMoments, probar las opciones condicionales de guardado de medios,
   exportar/importar y las confirmaciones de mantenimiento; comprobar que no se
   mezclan los controles de limpieza con los de privacidad.
9. Revisar temas claro/oscuro, RTL y fuente grande: textos legibles, sin cortes,
   contraste adecuado y controles accesibles.

## Alcance de validación

Los tests JVM ejecutan el plan y el despacho de secciones de producción con
controladores contados, verifican que no se crean editores al abrir el índice,
comprueban la cobertura de los controles anteriores y el reciclaje de la vista
previa. Las pruebas de partición verifican que cada clave general pertenece a
una sola sección, conservan los hijos de grupos expandibles y contrastan las
claves reales de AyuMoments con NaConfig. La búsqueda y las rutas antiguas se
ejecutan también con el registro Java de producción. También se comprueban los recursos reales de iconos, localización,
regresiones y sintaxis Java. AAPT2 verifica los tres XML de textos nuevos.

No se ha compilado una APK ni ejecutado una prueba física de esta interfaz.
No hay mediciones de fluidez o memoria en un teléfono. La versión de distribución
no se incrementa hasta preparar la próxima beta. Los commits de esta tarea usan
`[skip ci]` para respetar la petición de no iniciar compilaciones.

Validación final de esta ampliación: **431 pruebas aprobadas y 40 omitidas**.
Los siete archivos Java modificados pasan el análisis sintáctico; los tres XML
de localización pasan AAPT2 de forma aislada. No se han compilado APK ni
ejecutado pruebas físicas durante esta tarea.
