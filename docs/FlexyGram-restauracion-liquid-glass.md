# Restauración de Liquid Glass nativo

Se retira el sistema personalizado «Blur y bordes» de FlexyGram a petición del
propietario. Su editor de Universal, los materiales SimpleGlass, el contorno
personalizado y su configuración dejan de formar parte de la aplicación. Sus
antiguas claves guardadas quedan ignoradas, sin borrar otras preferencias.

Liquid Glass vuelve a su casilla original en Opciones de ahorro de energía →
Efectos en chats, con las condiciones originales de versión de Android y capacidad
del dispositivo. Se restaura su bandera, el procesamiento refractivo y los
proveedores de materiales de la base original de la beta
`932c9a6db84fab52ab167d4c8ee70957b3e57223`.

Las correcciones de navegación, el diseño compacto de ajustes y las optimizaciones
independientes de caché se conservan. Las superficies Signature existentes usan
el control nativo de desenfoque en lugar del interruptor personalizado eliminado.

Las pruebas específicas de la función retirada se eliminan y se comprueba que las
consultas nativas respetan las preferencias activadas, desactivadas y combinadas.
Se verifican también los recursos XML/AAPT2 y la sintaxis de los archivos Java
modificados. No se genera APK ni se afirma validación visual en un dispositivo.

Resultado: **240 pruebas aprobadas y 31 omisiones opcionales**. Los seis archivos
restaurados completos coinciden con la base nativa; 22 archivos Java modificados
pasan el análisis de sintaxis Java 21. Estas verificaciones no son una compilación
completa de Android.
