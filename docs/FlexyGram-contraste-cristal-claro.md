# Legibilidad del cristal claro sobre imágenes oscuras

La capa clara de la cabecera dejaba pasar demasiado el fondo oscuro, mientras
los subtítulos y el mensaje fijado conservaban colores grises o azules de poco
contraste. Desenfocar la imagen no elimina esa variación de luminosidad.

- Se introduce `GlassContrastPolicy`, independiente de Android, para proteger la
  legibilidad sobre los extremos negro y blanco de cualquier fondo. En modo
  claro la capa translúcida tiene un mínimo de alfa 184/255; un tinte personalizado
  demasiado oscuro se aclara sólo lo necesario. La imagen continúa visible.
- La cabecera y los paneles superiores usan esa misma capa de referencia. El
  material Universal aplica el límite de legibilidad en modo claro y sus ajustes
  lo explican. El valor solicitado de opacidad se conserva, sin modificarlo.
- El proveedor del tema de conversación ajusta títulos, subtítulos, textos e
  iconos del panel fijado y el control de traducción para contrastar con esa capa.
  Los colores que ya contrastan no se alteran. La corrección usa la paleta del
  tema y la opacidad, con caché de colores; no lee píxeles ni sigue el scroll.
- La rama oscura del material se conserva. Los controles de blur y el interruptor
  maestro siguen condicionando el efecto.

Validación local: 210 pruebas aprobadas y 31 omitidas. La prueba nueva ejecuta el
código Java de producción con 180 combinaciones de tintes, opacidades y colores
(incluidos gris y azul), y comprueba sus resultados con un cálculo WCAG
independiente sobre nueve fondos oscuros, claros y saturados: contraste mínimo
4,5:1 para el texto calculado y conservación de la transparencia. Esto valida
el modelo de color, no una captura Android posterior al cambio. La comprobación
visual final requiere el APK y un teléfono.
