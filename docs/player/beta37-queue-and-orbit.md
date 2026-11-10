# Reproductor — beta 37, build 1326

Base: `27495e5663de12f34e9a6b5d862fc55c4929e78b`.
Rama: `codex/flexygram-beta-glass`. Fecha: 10 de noviembre de 2026.

## Funciones integradas

- **Reproducir a continuación** y **añadir al final** en el menú de un mensaje de
  música y en las filas de la cola. La canción actual conserva su posición de
  reproducción. Si no hay reproducción activa, la primera canción inicia una sesión.
- **Quitar de la cola** mediante el menú de una pista pendiente. No elimina su
  archivo, mensaje ni pertenencia a una lista guardada. La canción actual está
  protegida para evitar interrupciones accidentales.
- **Reordenar** desde el asa de cada pista pendiente. Los cambios se aplican una
  sola vez al soltar, no durante cada movimiento del dedo. El menú ofrece también
  subir/bajar para usuarios que no utilizan arrastre.
- **Buscar en la cola** desde la cápsula del reproductor ampliado, que abre la
  lista con el teclado, o desde el propio campo de búsqueda de la lista. Filtra por
  título, artista y nombre de archivo sin distinguir mayúsculas o acentos. No es
  una búsqueda de música en Internet.

La cola editable es temporal. Al editar, toma una instantánea de las canciones ya
cargadas y se separa de los cargadores de perfiles/chats/búsquedas. Se evita así
que una respuesta tardía reordene la selección manual. No se cambia ninguna lista
guardada en el servidor. Se conservan los ajustes nativos de repetición, dirección
y aleatorio; añadir «a continuación» tiene prioridad en el orden efectivo actual.
Activar de nuevo aleatorio explícitamente sigue usando su comportamiento nativo.

Se permiten canciones de distintos chats de la misma cuenta. Se rechazan mezclas
con otra cuenta, contenido efímero/programado y operaciones incompatibles con una
reproducción de voz. Los identificadores incluyen cuenta, diálogo e ID de mensaje:
dos chats con el mismo ID numérico no son la misma pista. Añadir una pista ya
presente la mueve, sin duplicarla. El límite de crecimiento de una cola manual es
5.000 pistas; se puede quitar/reordenar contenido de listas heredadas mayores.

Durante una búsqueda se desactiva el arrastre para no confundir el subconjunto
filtrado con el orden completo. Quitar/añadir al final/reproducir después siguen
disponibles. Si cambia la lista durante un arrastre, se rechaza el resultado
obsoleto y se muestra la cola actual. Tocar un asa sin cambiar el orden no convierte
la lista en una cola manual ni separa su fuente original.

## Diseño aprobado

- Se mantiene una única portada circular real y el gesto de búsqueda de posición
  sobre su contorno, incluida la accesibilidad por incrementos.
- Arco de progreso con el acento del tema, una transición clara en su extremo y
  un halo pequeño. No hay ondas en el reproductor ampliado. La portada no rota.
- La cabecera mantiene la fuente de reproducción y sus controles. Se reduce un
  poco la portada y se incorpora la cápsula «Buscar en la cola» antes de ella.
- Título/artista centrados con el favorito a la derecha; se conserva la fila de
  velocidad, letras, temporizador y cola.
- En las tarjetas minimizadas se habilita el contorno ondulado del botón de
  reproducción, condicionado a reproducción visible y ahorro de energía. Al
  pausar deja de avanzar la fase y vuelve a su forma estática.

## Trabajo de rendimiento

El arco luminoso usa dos shaders reutilizados por tamaño/densidad/color: uno de
barrido y otro radial. Mover el progreso solo cambia sus matrices y dibuja el arco;
no crea bitmaps, filtros blur, servicios, animadores ni un temporizador adicional.
El progreso circular oculto durante el colapso no vuelve a invalidar la portada.

La búsqueda mantiene un índice normalizado por actualización de cola y agrupa
cambios del campo durante 120 ms. No vuelve a crear el índice al recibir progreso
de audio. El arrastre mueve filas locales y solo confirma una transacción al soltar;
esa transacción comprueba que la instantánea original sigue vigente.

No se copiaron DEX, APKs auxiliares, hooks ni servicios del plugin de referencia.
No se añadieron permisos, proveedores externos ni controles de otras aplicaciones.
La reproducción, descarga, foco de audio y notificación siguen siendo nativos.

## Verificación y límites

- Suite completa: **364 aprobadas, 39 omitidas, 0 fallos**.
- Cuatro pruebas nuevas ejecutan el modelo de cola, los métodos reales extraídos
  de MediaController, el renderer luminoso y los contratos de interfaz/recursos.
- Se recorren las cuatro combinaciones de dirección/aleatorio, identidad entre
  cuentas/chats, límites, pista actual, transacción obsoleta, arrastre sin cambios,
  búsqueda Unicode y fin de la cola sin repetición accidental.
- Prueba de 10.000 dibujos: solo dos gradientes con geometría y tema constantes;
  se reconstruyen al cambiar color/densidad. Se comprueban valores no finitos y
  opacidad cero. Estos conteos no son FPS ni tiempos de GPU de un teléfono.
- Se actualizaron las fixtures de `tools/connected_alpha/music_visual` y se
  generaron/comprobaron sintácticamente sus 56 archivos Java.
- El renderizado Android no se ejecutó: faltan los originales SDK API 37 y Build
  Tools 36. Las 39 omisiones incluyen corpus externos de plugins y artefactos
  SDK/R8 ausentes; no se contabilizan como aprobadas.
- No se ejecutó Gradle/assemble, no se generó ni firmó APK. El commit usa
  `[skip ci]` para mantener pendiente la compilación.

La siguiente beta debe comprobar en dispositivo: teclado/búsqueda, arrastre con
cambios simultáneos de pista, selección de canciones de varios chats, claro/oscuro,
temas con otros acentos, tamaños de texto grandes, pausa/reanudación, colapso a
tarjeta y retorno. Medir tiempos de frame/jank antes y después con el mismo contenido
y dispositivo. Una prueba sintética satisfactoria no garantiza ausencia de lag ni
un acabado idéntico en todas las versiones de Android.
