# Restauración de materiales de burbuja e iconos

Base revisada: beta 13, `1749b71ce0d93c55cf7dc8704d1d735ff48ff488`.

- Material anterior: transparencia y desenfoque de fondo. Sus bordes personalizados no se dibujan ni aparecen en el editor.
- Material adaptativo del aviso: el relleno conserva el alpha nativo y no utiliza la transparencia ni el blur guardados del material anterior. Mantiene los controles de borde, estilo, grosor y fusión.
- Hora pequeña: disponible en ambos materiales, sin alterar la preferencia al cambiar de estilo.
- Las preferencias de blur, transparencia y borde se conservan al alternar materiales; se aplica únicamente la familia de controles que corresponde al estilo activo. No se cambia el material elegido por el usuario.

Se retiran la sustitución global de recursos por Cupertino, el reemplazo del menú de mensajes y sus observadores de pulsación. Vuelven los recursos y animaciones anteriores, incluido el nombre Default del conjunto base. Los conjuntos Solar/Remix y los paquetes instalados conservan su selección y precedencia. No se reinician preferencias.

Los archivos y la fuente de Cupertino quedan archivados en `tools/cupertino/reference`, fuera del código y assets empaquetados de la app. Las licencias permanecen como referencia. No se retiran créditos.

Verificación sin APK: pruebas JVM de configuración, cambios entre materiales, alpha del relleno y hora/ticks; pruebas de tarjetas y navegación; prueba que comprueba la ausencia de puntos de sustitución Cupertino activos; análisis de sintaxis de los Java modificados. La aceptación visual final requiere una ejecución en dispositivo.

## Limpieza posterior

- Se retira del empaquetado la fuente Cupertino de 257628 bytes y su código sin uso. La referencia, el generador y las pruebas aisladas apuntan a `tools/cupertino/reference`; los avisos de licencia permanecen disponibles.
- Se elimina el puente de blur tintado del material adaptativo, sin consumidores tras separar los dos estilos. El blur anterior conserva su caché y su alpha de animación.
- Al limpiar un propietario de blur se sueltan también su drawable e imagen auxiliares. No se reciclan bitmaps que pudieran seguir referenciados por HWUI.
- Cambiar únicamente el material o los controles de efecto en la vista previa no solicita un nuevo layout de texto. Un cambio de métricas de la hora o una invalidación geométrica sigue solicitándolo.

La reducción de bytes indicada corresponde a la fuente retirada, no al tamaño final de una APK. Las pruebas verifican liberación de referencias y número de solicitudes de layout; no son mediciones de FPS en dispositivo.

Resultado de verificación de la limpieza: `pytest -q tests/` finalizó con 316 pruebas aprobadas y 33 omitidas. Las pruebas específicas adicionales de arranque/iconos finalizaron con 7 aprobadas. Los Java de producción modificados superaron el análisis de sintaxis y el diff no presenta errores de espacios. No se construyó ninguna APK; las pruebas gráficas aisladas de Android actualizadas quedan pendientes de ejecución.
