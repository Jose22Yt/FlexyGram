# Reproductor: panel compacto con acento del tema

Implementación del estilo 2 aprobado: superficie mate opaca, portada pequeña junto al título y artista, progreso/tiempos y controles en un panel sólido, tres filas de la cola real y accesos a velocidad, letras, cola completa y más. No se añade blur, glass ni un visualizador permanente.

## Pantalla y color

- `PlayerSheet.PlayerLayout`: portada de hasta 96dp, títulos al lado en ventanas amplias, disposición vertical con fuente grande o ventana estrecha. Se conserva el scroll para alturas insuficientes y el modo de letras. La cola vacía no reserva sus filas.
- `PlayerColors.fromSignatureTheme`: usa el acento del proveedor del tema activo y mantiene una caché acotada. El botón principal elige texto oscuro/claro según contraste. La portada no inicia extracción de paletas en la beta.
- `CompactPlayerQueue`: reutiliza tres filas del listado nativo, con una ventana que incluye la canción actual cuando está disponible. La cola sigue el orden de presentación del listado nativo, no predice el siguiente tema aleatorio. Abrir el encabezado muestra la cola completa. Seleccionar una canción utiliza `findMessageInPlaylistAndPlay`; no se crea otro reproductor.
- Los eventos existentes actualizan título, portada, pausa y carga de la cola. No se reconstruye la cola en cada notificación de progreso. Comparar mensajes usa cuenta, diálogo e identificador sin generar claves String por cada elemento.

## Minimizar, compactar y detener

- Minimizar el reproductor completo conserva la reproducción.
- En la tarjeta: portada/títulos abren el reproductor; reproducir/pausar controla el audio; el chevrón compacta a burbuja; **X detiene** mediante el cierre nativo. Para mantener el ancho compacto, siguiente/anterior siguen en la pantalla completa. En ventanas estrechas, mantener pulsada la tarjeta permite compactar cuando el botón no cabe.
- La barra superior utiliza la misma separación entre compactar y cerrar.
- La burbuja se arrastra dentro del fragmento, sin permiso de superposición. Su indicador de pausa queda dentro de sus 56dp iniciales. Tocar la portada/burbuja abre el reproductor completo. Al cerrarlo, se conserva la presentación flotante. El menú de pulsación prolongada permite volver a la tarjeta o detener.
- La referencia al fragmento es débil y se limpia al desprender el propietario. No se añaden observadores a la burbuja.

Para música, la beta utiliza esta pantalla aunque hubiera quedado desactivada la preferencia antigua. El acceso «reproductor clásico» queda oculto. Se conserva la infraestructura nativa necesaria para voz y componentes compartidos; no se cambian MediaController, MusicPlayerService, foco de audio ni notificaciones de reproducción.

## Verificación y límites

- Pruebas JVM: ventana de cola acotada, identificación entre cuentas/diálogos, cierre X separado de compactar y ruta de música hacia la nueva pantalla.
- Comprobación contra Android API37 y AndroidX Core: widgets reales y el `PlayerLayout` real en un host aislado. Los servicios de reproducción, tema, navegación y decodificador son dobles explícitos; no equivale a compilar toda la aplicación.
- Los Java modificados superan el análisis de sintaxis y el diff no contiene errores de espacios.
- El harness gráfico aislado se adaptó a la nueva distribución, pero no se ejecutó. Quedan pendientes la aceptación visual y la escucha en dispositivo: fuente grande, paisaje, RTL, letras, cola larga/aleatoria, descarga, cambio de tema, cambio de cuenta, arrastre de burbuja y X desde reproducción/pausa.

No se ha compilado una APK ni se han publicado estos cambios. Los cambios pendientes de importación individual de FlexyStudio se conservan.

Resultado final: suite `tests/` con **323 aprobadas y 33 omitidas**. Tras la última liberación de referencias y etiquetas de accesibilidad, las seis pruebas específicas del reproductor se repitieron y pasaron. Se actualizó una comprobación antigua del cierre del menú de mensajes para verificar la única actualización de ventana ya implementada, manteniendo sus garantías de cancelación/liberación del toque.
