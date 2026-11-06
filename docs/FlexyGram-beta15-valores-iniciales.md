# Beta 15: valores iniciales y acceso a Ajustes

Esta revisión reemplaza la política de desactivar ampliamente la personalización
introducida en la beta 14. Solo cambia los valores usados cuando no existe una
preferencia guardada; no restablece decisiones explícitas de los usuarios.

## Activado inicialmente

- Barra inferior principal, presentación flotante y sus dobles toques habituales.
- Menú animado Signature al tocar mensajes, con desenfoque de selección de toda
  la conversación, aunque el blur de superficies esté apagado.
- Reducción de animaciones y preferencias generales de apariencia que se habían
  apagado en la beta 14 (miniavatares, acentos de carpetas, avatar gooey, etc.).
- El nuevo reproductor continúa siendo la única interfaz de música de la beta.

## Apariencia original de conversación

Las burbujas continúan en «Por defecto», con hora nativa y sin borde, blur,
transparencia ni fusión personalizados. La cabecera y la entrada de mensajes
continúan en sus estilos originales. El blur de superficies, Liquid Glass y el
menú glass permanecen apagados inicialmente. El desenfoque al seleccionar un
mensaje tiene una política independiente, sin activar esos interruptores.

## Ajustes siempre accesibles

Los dos menús superiores de conversaciones (el de DialogsActivity y el del host
MainTabsActivity) incluyen Ajustes independientemente de la barra inferior, sus
pestañas o el orden personalizado del menú. Esto también cubre una selección
vacía de pestañas: el menú se construye al abrirlo y no necesita forzar ni
reescribir preferencias antiguas para recuperar el acceso.

## Comprobaciones

Se ejecuta el constructor real del menú con barra visible/oculta, destinos
vacíos y destinos sin Ajustes, verificando que el toque abre la acción correcta.
Las pruebas de preferencias verifican instalación nueva, decisiones explícitas,
recarga, compatibilidad con `tap_panel`, y separación del blur de selección de los
interruptores de superficies. Se mantienen las regresiones de capturas que
protegen la opacidad de la interfaz inferior. No sustituyen la validación física.
