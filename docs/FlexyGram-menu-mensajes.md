# Menú de mensajes de FlexyGram

Ruta: **Conversaciones → Menú de mensajes**. Se conserva el modo clásico de
Telegram y la lista compacta anterior. La galería añade las tres propuestas:

- **Acciones rápidas**: cuadrícula de tres columnas y acceso «Más» centrado.
- **Tarjetas agrupadas**: responder/copiar, acciones del mensaje y eliminar/más.
- **Barra y menú**: responder/copiar/reenviar arriba y lista con iconos al final.

Las miniaturas se dibujan con `BubbleActionPanelView`, el mismo componente que
se usa en el chat, a escala reducida. Tocar una activa el diseño y el modo
FlexyGram. La galería se desplaza horizontalmente y muestra la selección actual.
Los iconos son trazados originales redondeados; no requieren fuentes o assets
externos. Las rutas y los pinceles se preparan al crear el icono, no por frame.

**Acciones visibles** permite elegir responder, copiar, sticker, reenviar,
editar, fijar, eliminar, seleccionar, guardar, compartir y copiar enlace. La
selección es global, pero se cruza con las acciones que permite cada mensaje.
«Más» permanece disponible incluso si se ocultan todas las acciones principales,
y abre la lista nativa completa. Cancelar el diálogo no guarda cambios;
Restablecer recupera las seis acciones de la referencia.

ChatActivity conserva la propiedad de la selección y de los permisos. Cada
acción vuelve a comprobar la identidad de la burbuja y las opciones nativas
actuales antes de ejecutarse. Sticker tampoco puede omitir la restricción de
contenido protegido o efímero. Guardar y compartir usan las acciones originales.

El orden del popup es **reacciones → espacio de la burbuja → opciones**. El
espacio inferior de las reacciones es positivo en el modo compacto. La matemática
de colocación conserva la burbuja completa entre ambas superficies, usando el
área segura que excluye cabecera, traducción, fijados y teclado. Las ventanas
cortas mantienen el desplazamiento nativo de las opciones.

Los ajustes se guardan en `flexy_bubble_interaction/menu_layout` y
`menu_actions`; ambos están incluidos en la copia completa de FlexyStudio.
Se conservan el movimiento amortiguado existente, la cancelación de callbacks
al retirar la vista y la preferencia independiente de reducir animaciones.

## Verificación

- 257 pruebas generales aprobadas; 31 omitidas por condiciones de entorno.
- 5 pruebas Android aisladas del menú aprobadas: diseños claro/oscuro, RTL,
  miniaturas, permisos, preferencias, diálogo atómico y colocación segura.
- 16 pruebas Android aisladas de ajustes aprobadas.
- 31 comprobaciones de copia/restauración de Studio aprobadas.
- Sintaxis Java 21 y `git diff --check` correctos.

Los PNG `menu-*-native.png` de la prueba Android proceden del componente real,
no de generación de imágenes. El arnés aísla los controladores de Telegram y
no sustituye la verificación del chat completo en un dispositivo. No se compiló
una APK con este cambio.
