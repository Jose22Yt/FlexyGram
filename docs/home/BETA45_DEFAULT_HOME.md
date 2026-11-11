# Beta 45 — únicamente pantalla principal por defecto

11 de noviembre de 2026 (America/Bogota). Fuente `1.0.0-beta.45`, build `1334`. No se compila una APK en esta revisión, por petición del usuario.

Se retira el estilo de pantalla principal Telegram iOS, incluyendo su selector, cabecera, buscador, reglas de navegación y dimensiones/tipografía propias. Se cancela el pulido de ese modo solicitado previamente, porque el usuario decidió eliminarlo. Se conserva el diseño por defecto y no se recupera «Diseño esencial».

La barra inferior vuelve a leer todos los ajustes del usuario: mostrar/ocultar, destinos y orden, etiquetas, densidad, formato flotante y búsqueda separada. Se conservan las preferencias guardadas. Las filas de chat vuelven a la tipografía y distribución previas a beta 44, sin forzar tres líneas ni aumentar el texto al elegir un estilo.

El antiguo ajuste `flexygram_home.style` queda exclusivamente como compatibilidad de preferencias/copias antiguas. Al cargar, los valores de los diseños retirados se restablecen a cero; no existe ningún camino de interfaz o renderizado que vuelva a activarlos. FlexyStudio admite importar los valores antiguos 0/1/2 y la recarga los normaliza a por defecto. Los ajustes de líneas divisorias se conservan en un componente independiente, sin selector de diseños.

Los iconos originales, el reproductor y las mejoras de arranque, memoria y movimiento de mensajes de beta 42/43 no se retiran. Las medidas de protección ante acciones sobre una selección vacía también se conservan.

Verificación local: **386 pruebas correctas y 39 omitidas** por corpus/herramientas ausentes. Pruebas JVM de migración idempotente y conservación de preferencias ajenas, personalización de navegación después de una selección antigua de iOS, ausencia del selector/rutas de iOS y mantenimiento de los controles e iconos por defecto. Comprobación aislada de los ajustes con Android API35 y AndroidX Core; suite general de regresiones y sintaxis Java. No se afirma una medición de FPS o prueba visual en dispositivo de esta revisión.

El video de esta conversación no pudo abrirse con la herramienta disponible porque supera su límite de transferencia de 32 MiB. Esta revisión final responde a la posterior decisión explícita de retirar el modo, y no afirma haber analizado ese video.
