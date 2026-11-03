# Inicio nativo con el icono seleccionado

## Comportamiento

En Android 12 o superior, FlexyGram persiste el tema de la pantalla de inicio mediante `SplashScreen.setSplashScreenTheme()`. El cambio de icono actualiza este tema, sin una segunda Activity, un overlay de carga, una espera mínima, una descarga o un bloqueo hasta que termine la sincronización. Android retira la pantalla de inicio cuando dispone del contenido; el callback de salida la elimina inmediatamente.

Se incluyen temas estables para los 29 iconos del selector. Los 12 diseños nuevos de FlexyGram usan vectores derivados de sus recursos existentes, con recorte circular explícito y margen seguro de Android. Los iconos heredados reutilizan sus recursos adaptables/redondos existentes; su máscara puede depender del sistema. No se duplicaron bitmaps ni se añadieron bibliotecas.

El arranque inicial usa Neon, el icono predeterminado. Al actualizar desde una versión que todavía no persistía el tema, el icono recordado queda sincronizado para los siguientes arranques. Al seleccionar un icono desde la nueva versión se actualiza automáticamente. Android puede omitir la pantalla de inicio al volver a una aplicación que ya está abierta.

La personalización nativa persistente requiere Android 12. En Android 7–11 se mantiene la ventana inicial compatible, sin añadir una pantalla artificial ni prometer un icono dinámico antes de que arranque el proceso. Los colores de inicio siguen los recursos de día/noche del sistema.

## Trabajo de arranque

- La reconciliación de todos los aliases del launcher pasa del hilo principal a la cola de trabajo. La reconciliación y el cambio explícito de icono se serializan para evitar que la reparación sobrescriba una elección concurrente. La selección resuelta se conserva en memoria para actualizar el splash sin volver a recorrer PackageManager.
- La actualización del tema nativo se agrupa después de un frame y omite escrituras cuando el tema no cambia.
- El arranque desde la interfaz pospone los servicios auxiliares de cuentas hasta después del primer callback de frame y su recorrido de vistas, manteniendo su ejecución en el hilo principal. Las entradas de notificaciones/servicios conservan la inicialización inmediata, sin depender de una Activity.
- La cuenta seleccionada sigue solicitando los diálogos locales antes de los servicios auxiliares y de otras cuentas. No se modificaron SQLite, las sesiones, la autenticación ni la sincronización nativa.

## Validación

- Suite Python/JVM: **220 aprobadas, 31 omitidas**.
- Pruebas nuevas ejecutan la clase real de splash con dobles de Android: coalescencia, última selección, escrituras redundantes, Activity finalizada, retirada inmediata y protección de versiones anteriores. También ejecutan el bloque real de despacho de servicios para los caminos UI y servicio.
- `StartupSplash` y `LauncherIconController` compilaron contra Android SDK 37 con dependencias de aplicación mínimas.
- AAPT2 compiló y enlazó los temas y vectores nuevos con fixtures de los recursos heredados. Esto verifica los recursos, no constituye una APK completa.
- Sintaxis Java y `git diff --check` correctos.

Los vídeos proporcionados muestran la ventana vacía de FlexyGram y el icono circular de Cherrygram, pero no constituyen una medición equivalente del arranque en frío. Queda probar la APK en el dispositivo: inicio en frío/tibio, cambio de icono y reapertura, día/noche, cuenta conectada/login, entrada por notificación/enlace y visibilidad de chats locales frente a sincronización de red. No se afirma una mejora medida de milisegundos o FPS.
