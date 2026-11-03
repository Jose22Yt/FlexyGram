# Vista previa de mensajes grandes en el menú contextual

Se corrige la ruta compacta de selección de mensajes individuales, utilizada por
el toque de burbuja y el menú de acciones/reacciones.

- La escala de ajuste deja de tener el mínimo fijo de 0,72. El mensaje o foto
  completos se reducen temporalmente para caber entre reacciones y acciones.
  El contenido y tamaño de la burbuja original no se modifican.
- La colocación utiliza el mismo espacio que el recorte: después de la cabecera,
  fijados y traducción, y antes del compositor y los insets inferiores.
- La altura del hueco se vuelve a medir de forma acotada y con invalidación de
  layout. En ventanas cortas se reserva espacio a la vista previa y se limita la
  altura de las acciones, que conservan su ScrollView nativo.
- La selección compacta no desplaza primero el RecyclerView para reposicionar
  el mensaje original. Se transforma solamente su dibujo temporal.
- El ajuste geométrico usa una fase limitada a 0–1, independiente del rebote
  decorativo. Las vistas reducidas no crecen fuera de su hueco ni se invierten.
- La celda seleccionada dibuja todos los bloques de texto y emojis durante el
  dibujo temporal, restaurando su estado después. Ya no se sobrescribe la caché
  de bloques visibles de la fila normal.
- Si cambia la altura del panel superior o el tamaño de ventana, se descarta el
  menú abierto para evitar conservar límites antiguos. Se reinicia el offset
  del viewport al configurarlo.

Validación local: 213 pruebas aprobadas y 31 omitidas; sintaxis Java y diff
correctos. Se ejecuta la geometría de producción con fuentes parcialmente fuera
  de pantalla, mensajes de hasta 12 000 px, distintas alturas de paneles, teclado
  y ventanas, además de extremos del rebote. PlacementProbe comprueba 3381
  aserciones. Las pruebas no sustituyen una ejecución visual en Android.

El vídeo adjunto no pudo transferirse: supera el límite de 32 MiB de la
herramienta. Las correcciones se basan en la descripción del propietario y los
fallos encontrados en el código; queda pendiente confirmar visualmente el APK.
