# Prueba manual en el Poco: instrucciones condicionadas a obtener una APK

No se ha realizado esta prueba en el teléfono. No instalar un archivo que no figure en el informe con SHA-256, firma y resultado de compilación comprobados.

1. Comparar el SHA-256 del archivo recibido con el publicado en el informe. Conservar APK, informe, huella de firma y SHA fuente como conjunto de referencia.
2. Comprobar Android/API, ABI y tamaño de página reales. Con ADB autorizado: `adb shell getprop ro.product.model`, `adb shell getprop ro.build.version.sdk`, `adb shell getprop ro.product.cpu.abilist`, `adb shell getconf PAGE_SIZE`. Registrar además versión HyperOS, frecuencia elegida, navegación y temperatura aproximada.
3. La base conserva `com.exteraless.app`. Si ya está instalado Exteraless, no desinstalarlo ni reemplazarlo para forzar una firma distinta: podría perder datos. Detenerse y preparar una variante aislada revisada, o usar un dispositivo/perfil de prueba compatible. Un package diferente también puede requerir configuración de servicios distinta; no es una equivalencia automática con la base.
4. Antes de iniciar sesión real, configurar y reconstruir con Telegram API ID/API Hash propios mediante el archivo privado descrito en [reproduction.md](reproduction.md). No enviarlos por chat ni escribirlos en la documentación. Revisar también Firebase/Maps y el actualizador heredado; la referencia original no constituye una configuración final de servicios FlexyGram.
5. Si no hay conflicto y se ha aprobado la configuración de prueba, instalar desde el gestor de paquetes o `adb install /ruta/baseline-debug.apk`. Verificar el mensaje real de instalación y arrancar manualmente. Evitar comandos de desinstalación o borrado de datos.
6. Comprobar arranque, lista de chats, apertura y cierre de una conversación de prueba, Back del sistema, teclado, scroll y apertura de un recurso multimedia. Registrar fallos con hora y pasos exactos. No concluir rendimiento general con esta prueba básica.
7. Para diagnóstico, `adb logcat -v threadtime` en una sesión privada. Revisar y ocultar teléfonos, mensajes, identificadores, tokens, rutas privadas y credenciales antes de compartir fragmentos. Los bugreports/heap dumps deben tratarse como potencialmente sensibles.

Las mediciones formales se preparan en [measurement-plan.md](measurement-plan.md). No se han activado módulos de benchmark, trazas permanentes ni funciones propias en el cliente.

Propuesta si existe conflicto: una variante separada `baselineIsolatedDebug` con applicationId `com.jose22yt.flexygram.baseline.debug`, firma Debug propia y configuración de servicios compatible. No se ha implementado. Documentar package, servicios, certificado y variante como diferencias frente a la referencia original y conservar ambos artefactos; no atribuir cualquier diferencia de comportamiento únicamente al rendimiento.

Durante la comparación, conservar exactamente la APK identificada por hash y no aplicar actualizaciones del actualizador heredado de Exteraless. Una actualización cambia la referencia aunque el proyecto siga teniendo el mismo nombre.
