# Ajustes compactos de FlexyGram

Se mantienen las diez categorías principales. Pantalla principal y Conversaciones
ahora son índices de apartados, con las mismas preferencias y callbacks nativos.
No se migra, reinicia ni duplica ninguna configuración.

## Organización

- Pantalla principal: lista y título, movimiento y desplazamiento, mini píldoras, avatares, carpetas,
  elementos visibles y opciones adicionales de apariencia.
- Conversaciones: interfaz inferior, interfaz superior, burbujas y menú;
  mensajes y respuestas, menús y acciones, multimedia, stickers, bordes y
  reflejos, información de miembros, conversiones y animaciones.
- Los cuatro accesos de diseño tienen dibujos distintos. También se distinguen
  los accesos de sistema y plugins. Se reutilizan recursos existentes; los
  iconos originales de Telegram iOS se tintan con el tema actual.
- Mini píldoras: selector de una fila que muestra el valor actual y abre un
  diálogo de opciones. La demostración se crea solamente al solicitarla y se
  puede ocultar. Las cuatro opciones conservan sus valores persistidos.

Los controles mantienen sus dimensiones legibles y áreas táctiles. Cada apartado
usa un único RecyclerView y crea solamente los adaptadores necesarios. El índice
principal de Pantalla principal pasa de ocho controladores a uno de enlaces;
el de Conversaciones, de doce a dos de enlaces. Estos son conteos estructurales,
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
7. Revisar temas claro/oscuro, RTL y fuente grande: textos legibles, sin cortes,
   contraste adecuado y controles accesibles.

## Alcance de validación

Los tests JVM ejecutan el plan y el despacho de secciones de producción con
controladores contados, verifican que no se crean editores al abrir el índice,
comprueban la cobertura de los controles anteriores y el reciclaje de la vista
previa. También se comprueban los recursos reales de iconos, localización,
regresiones y sintaxis Java. AAPT2 verifica los tres XML de textos nuevos.

No se ha compilado una APK ni ejecutado una prueba física de esta interfaz.
No hay mediciones de fluidez o memoria en un teléfono. La versión de distribución
no se incrementa hasta preparar la próxima beta. Los commits de esta tarea usan
`[skip ci]` para respetar la petición de no iniciar compilaciones.

Resultado final, incluyendo la integración de las mejoras remotas de desplazamiento de beta 54: **427 pruebas aprobadas y 40 omitidas**.
Comprobación de sintaxis Java: seis archivos modificados/nuevos sin errores.
AAPT2: los tres XML de localización nuevos pasan la verificación aislada.
