# Inicio de ajustes compacto

La pantalla de categorías de FlexyGram conserva sus diez destinos y los cuatro
grupos. Se retira el título grande duplicado «Ajustes». Las filas del inicio usan
16 sp, un mínimo táctil de 48 dp e iconos de 24 dp; las separaciones y los títulos
de grupo también son más pequeños. Las descripciones siguen disponibles para
accesibilidad y búsqueda, pero dejan de ocupar una segunda línea visible.

El objetivo es mostrar las diez categorías juntas en una pantalla habitual con
el tamaño de letra predeterminado. Las filas pueden crecer y la lista mantiene
el desplazamiento para pantallas pequeñas, títulos largos y letra ampliada.
No se comprime el contenido para forzar una captura ni se recortan categorías.

Se reutilizan seis iconos Solar existentes y se actualizan los cuatro vectores
de inicio, gestos, documento y capas con curvas y esquinas más suaves. El tinte
proviene del tema de Telegram. Los títulos de grupo se registran también en el
sistema de actualización de colores para cambios de tema en la pantalla abierta.
Los editores internos conservan sus filas y sus controles.

Validación: 13 comprobaciones de ajustes e iconos aprobadas y 250 pruebas de la
suite integrada aprobadas, con 31 omisiones opcionales; los diez iconos
compilan y enlazan con AAPT2/API 37. Las tres fuentes Java modificadas pasan el
análisis de sintaxis Java 21 y la celda compila contra las clases reales de Android
API 37 con dependencias Telegram aisladas. Estas comprobaciones no sustituyen
una compilación completa ni la revisión visual en un teléfono. No se compila APK
como parte de este rediseño.
