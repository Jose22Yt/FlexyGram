# Primera prueba sólo desde el teléfono

Esta guía sirve para la APK offline ACTUAL aprobada de Work2. No necesita ordenador,
ADB, depuración USB ni otras herramientas. No constituye autorización de instalar:
primero deben estar aprobados el archivo concreto, la firma y la entrega privada.
Las nuevas funciones de exportación descritas al final requieren OTRA compilación.

1. Instala únicamente el archivo aprobado de Work2. Conserva su nombre/versión.
   Si Android/HyperOS lo rechaza, captura el mensaje completo y detente; no fuerces
   una instalación ni desactives protecciones para ocultar el error.
2. Mantén la prueba offline. Abre FlexyGram desde su icono. Debe aparecer la lista
   de demostración, sin login ni petición de datos personales. Si se cierra al
   instante, graba un segundo intento y detente en ese fallo.
3. Abre Synthetic conversation y vuelve a la lista cinco veces, despacio. Luego
   repite diez ciclos rápidos. Prueba Atrás del sistema/gesto que ya tengas
   configurado y vuelve también durante una transición. No cambies las escalas
   de animación ni actives opciones de desarrollador.
4. Haz varios toques consecutivos abrir/Atrás/abrir durante unos5s. Graba qué
   pantalla queda al final y si todavía responde; no atribuyas cada toque físico
   a un evento si no existe evidencia. No hay conversaciones Telegram reales.
5. Settings → Dark mode: alterna claro/oscuro cinco veces y vuelve al chat de
   demostración. Comprueba legibilidad, pantalla incompleta, cierre o bloqueo.
6. Pulsa Home y vuelve a la app tres veces. Si tu configuración ya permite
   rotación, gira una vez en Settings y otra en la conversación. Si no rota,
   anótalo como NO PROBADO; no actives «No conservar actividades».
7. Settings → Local Python: pulsa una vez y espera el resultado. Captura
   "Python initialized; JNI loaded; sys imported; plugins disabled", o el error
   concreto visible: "JNI not loaded", "Python start failed", "Python import
   failed" o "POST_INIT_FAILED". No pulses repetidamente si sigue inicializando.
   Este indicador no certifica todas las bibliotecas/plugins/funciones nativas.
8. En la APK actual, Local observations guarda lotes PRIVADOS. No permite aún
   guardarlos desde Archivos ni enviarlos sin otra compilación. Para esta primera
   prueba bastan capturas/vídeos y el paso exacto que provoca el fallo.

Graba sólo FlexyGram y sus fixtures; evita mostrar notificaciones/datos de otras
apps y audio privado. Si el fallo exige grabar desde el icono, revisa el vídeo
antes de compartirlo. Repite una vez el caso sin grabación y anota si cambia.
Una grabación permite estudiar el comportamiento visible; no demuestra FPS
presentados, latencia táctil física, ANR ni carga correcta de todos los ELF.

Si no responde durante aproximadamente5s, registra «bloqueo observado» y cuánto
tarda en recuperarse. No lo llames ANR confirmado. Ante cierre/bloqueo reproducible,
detén ese caso y conserva el primer vídeo, sin repetir indefinidamente.

Mensaje mínimo al compartir voluntariamente:
- Archivo/versión de beta y caso de esta lista.
- Pasos exactos y resultado esperado/observado.
- Tema claro/oscuro, gesto/botón utilizado y si estaba grabando.
- Se recuperó / se cerró / siguió bloqueada; duración aproximada si se conoce.
- Captura o vídeo recortado al fallo. Ninguna contraseña, cuenta o código Telegram.

## En una FUTURA beta con exportación integrada y validada

Settings → Exportar diagnósticos → elegir almacenamiento local en el selector
nativo → Guardar. Después puedes adjuntar voluntariamente el ZIP desde Archivos.
No hay envío automático ni cuenta requerida. Elegir Descargas/local evita usar
un proveedor de nube: EXTRA_LOCAL_ONLY es una indicación al selector, no una
prueba universal de que el proveedor no sincroniza por su cuenta.

Cancelar conserva el snapshot privado. Reintentar exporta ESE snapshot sin volver
a consumir eventos. Tras un guardado correcto, una nueva pulsación prepara otro
snapshot que incluye los lotes de la sesión y las acciones más recientes.
Un error puede dejar un ZIP externo incompleto: no usarlo como evidencia válida;
conservar la copia privada y volver a elegir destino. No se borra automáticamente
ningún documento del usuario.

El ZIP sólo contiene eventos sintéticos y estado enumerado del probe local,
no Logcat, cuentas, mensajes, sesiones, preferencias, texto de excepciones o datos
de otras aplicaciones. Un crash anterior a la primera pantalla puede impedir
exportar; sin ADB esa primera evidencia será el vídeo/error visible. No se añaden
capturadores de crashes permanentes ni se promete una traza que no se obtuvo.
