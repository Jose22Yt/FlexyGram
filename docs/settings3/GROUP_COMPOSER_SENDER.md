# Selector de identidad dentro de la entrada compacta

Rama: `share/flexygram-settings-motion-menus`, base publicada `b55bf39c7617253f2e4987010743c0069f17cb71`.

El selector nativo de «Enviar como» activaba `hasFlexySpecialControls`, deshabilitando la presentación compacta en grupos. Ahora su visibilidad no fuerza ese cambio. Los controles especiales restantes conservan sus condiciones de seguridad.

Diseño aprobado: adjuntos fuera a la izquierda, avatar de identidad dentro del extremo izquierdo de la píldora, texto a continuación, emoji a la derecha dentro y micrófono/enviar fuera. No se cambia el selector de cuenta/identidad real, sus permisos, peers, imágenes ni popup. Se reutiliza el mismo SenderSelectView y su mismo padre; no se reconstruye la jerarquía.

`ComposerGeometry.senderSize/senderLeft/senderTextStart` calculan avatar y espacio de texto según el inset y separación existentes. El avatar queda dentro del fondo de la píldora y anclado abajo al escribir varias líneas. El borrador enriquecido comparte la reserva de texto. Al volver al diseño original se restauran los parámetros nativos del avatar. Tamaño/posición vertical siguen sus preferencias actuales.

La aparición en modo compacto usa alpha; la visibilidad y reserva de espacio cambian una vez. No hay un callback nuevo por frame que modifique márgenes ni traslade texto/emoji. Se cancelan los desplazamientos nativos pendientes al entrar al compacto. El modo original conserva su flujo previo. Se mantiene el límite de anchura de 280dp del campo y el fallback para controles no adaptados, como acciones de pago expandidas y WebView.

Verificación: **8 pruebas aprobadas** con JDK 21: `test_group_composer_sender`, `test_composer_layout`, `test_composer_gallery`, `test_composer_action_sizes`, `test_composer_tools`. El nuevo probe ejecuta los métodos reales de elegibilidad y parámetros con dobles Android en 84 combinaciones de densidad/tamaño/separación; comprueba contención, espacio de texto, restauración y controles especiales. La regresión de animación comprueba la rama de integración y ausencia de actualización de layout por frame. La sintaxis de ChatActivityEnterView pasó javac parse; `git diff --check` limpio.

No se generó APK ni se ejecutó la interfaz en dispositivo. Pendiente comprobar tacto y popup del avatar, envío anónimo/personal, selección/edición, IME, texto largo, cambio de tamaño/posición y tema claro/oscuro. Esta entrega es local; aún no publicada.
