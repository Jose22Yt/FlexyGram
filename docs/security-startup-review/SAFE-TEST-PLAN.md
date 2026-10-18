# Plan seguro y condiciones para finalizar el Paso 3

Este documento es una propuesta para revisión. **No autoriza ni ejecuta una nueva APK, cambios funcionales, inicio de sesión o pruebas de revocación. No comienza el Paso 4.**

## Contención y preservación

No continuar experimentos autenticados con la APK heredada ni con la cuenta personal. Conservar el archivo/hash como evidencia; no redistribuirlo como cliente listo para autenticación. Guardar el aviso de Telegram de forma privada con su hora y zona horaria. Si el titular lo considera necesario, revisar la seguridad y contactar soporte desde un cliente oficial de confianza; esta auditoría no inicia sesiones, escribe mensajes ni realiza cambios sobre su cuenta o sus bots.

No desinstalar, borrar datos, restaurar, clonar ni reemplazar Exteraless/Telegram para intentar reproducir. Esas acciones pueden eliminar sesiones, chats secretos, archivos locales y configuración. No se da por supuesto que exista una copia recuperable de todo. La alternativa es un dispositivo/perfil de laboratorio sin cuentas y, posteriormente, un paquete independiente que coexista sin tocar esos datos.

## Datos mínimos que el titular puede aportar ahora

Los siguientes comandos consultan el sistema, no arrancan FlexyGram ni leen sus datos. Usar únicamente un ordenador de confianza con Android Platform Tools y autorizarlo personalmente; no compartir identificadores del dispositivo. No necesitan root.

```sh
adb shell getconf PAGE_SIZE
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.cpu.abilist
```

Compartir solo esas cinco salidas si desea completar la ficha. `PAGE_SIZE=4096` significa 4 KB y `16384`, 16 KB. Un SDK/version/modelo no sustituye ese dato. No activar un modo experimental de página ni cambiar ROM/boot para esta revisión. Desactivar o revocar la autorización de depuración al acabar si ya no se necesita.

Para la cronología basta responder en texto, sin archivos privados:

- Fecha/hora/zona aproximadas de instalación, primer login, cierres observados y aviso; qué ocurrió antes y después, incluyendo si todos los efectos fueron simultáneos.
- Si fue instalación nueva, actualización aceptada, reinstalación después de borrar, restauración, clonación OEM o segundo perfil. No extraer preferencias para averiguarlo.
- Si se activaron motor/plugins, modo inseguro/desarrollador, proxy o actualización original; si se tocaron Terminar otras sesiones, No en autorización desconocida o código de pánico. “No recuerdo” es un resultado válido.
- Si alguna vez se enviaron logs de esta APK y a quién, sin volver a adjuntarlos. Indicar solo si el aviso hablaba de sesiones, tokens de bots y bots congelados; no publicar usernames, IDs o capturas con datos.
- Qué pantalla tardó, duración aproximada recordada y si fue solo primera apertura o también posteriores. No volver a abrir la app autenticada para medirlo ahora.

No pedir ni compartir API Hash, contraseña/2FA, OTP, QR de login, tokens Bot API/FCM, pushAuthKey, auth keys, archivos `tgnet.dat`, userconfig, saved_tokens, copias de seguridad, bugreports o Logcat completo. Las rutas de log halladas pueden contener secretos. La autenticidad del aviso y la razón de la medida solo pueden confirmarse con información confiable del titular/Telegram, no con una prueba contra su cuenta.

## Puertas de la futura versión de diagnóstico

### A. Aprobar y preparar aislamiento

Revisión humana de estas conclusiones y de las propuestas P0. En un cambio posterior del Paso 3: applicationId y autoridades/cuentas/deep links independientes, firma diagnóstica propia, no restauración/importación ni actualizador heredado. Credenciales y servicios propios documentados o desconectados; sin fallback de autenticación. Si faltan credenciales, el cliente de diagnóstico no debe poder solicitar código ni autenticarse. Mantener plugins, desarrollador y modo inseguro apagados.

Eliminar secretos de todos los sumideros antes de recopilar trazas. Usar canarios sintéticos en pruebas locales de logs y backups, sin secretos operativos. Inventariar Firebase, OAuth, Maps y demás servicios antes de permitirles red. Sin cambios de navegación, interfaz, animaciones, reproductor, burbujas o semántica de plugins para “mejorar” las mediciones. Las restricciones de diagnóstico necesarias deben ser explícitas y revisables, sin presentarlas como una base funcionalmente equivalente cuando no lo sean.

### B. Laboratorio offline, sin cuentas

Dispositivo o emulador autorizado y limpio, sin cuentas personales, plugins descargados ni información privada; inicialmente sin salida de red. Verificar hash, certificado, paquete, versión y ABI antes de instalar **solo la futura identidad independiente**. No instalar la APK actual encima de otra app. Medir primer frame de pantalla sin cuenta, ausencia de cierre inmediato, JNI y creación de archivos/configuración. Si un servicio no es necesario para ese escenario, mantenerlo desactivado según la configuración aprobada y documentar esa diferencia.

No ejecutar RPC de terminación contra servidores para “probar seguridad”. Las rutas de reset/logout pueden verificarse primero con dobles/fakes de transporte locales y datos sintéticos: confirmar que no se envían sin acción explícita; incluir la ruta UndoView, rechazos de autorizaciones y el código de pánico. Revisar controles de plugins por separado, sin instalar código de procedencia desconocida.

### C. JNI/Python y 4 KB/16 KB

Tras aprobar el tratamiento de dependencias, pruebas sintéticas sin cuenta: cargar JNI raíz, iniciar motor Python explícitamente en escenario aparte, importar módulos críticos y usar XML/XSLT/fuentes con fixtures inocuos. Probar con motor apagado y encendido como escenarios distintos. Registrar errores del linker/import, versiones, page size y modo de compatibilidad. No borrar módulos ni ignorar excepciones para pasar la prueba.

Para confirmar compatibilidad completa hacen falta Android ARM64 de 4 KB y 16 KB. Si el Poco usa 4 KB, el caso 16 KB requiere otro entorno; un resultado bueno en ese Poco no certifica ambos. La prueba ARM64 no cubre ABI x86_64 ni otros teléfonos.

### D. Rendimiento y variante comparable

Mismo commit y configuración de servicios/fixture para las variantes comparadas. Primero aislar diferencia debuggable; después cuantificar R8/shrinkResources sin confundir ambos factores. Variante no depurable profileable para Macrobenchmark/Perfetto; Debug con medidas diagnósticas comparables etiquetadas. No fabricar tiempos ni usar la supresión de validación de Macrobenchmark como resultado de producción.

Trazas y logs con marcadores fijos: inicio de proceso, Application, postInit, JNI, Activity, primer frame y listo; errores con tipos y stack saneado. No argumentos RPC, contenido de mensajes, teléfonos, tokens, IDs de usuario, direcciones proxy o rutas personales. Recoger solo proceso diagnóstico sobre entorno limpio; Perfetto puede incluir metadatos de otros procesos, por eso no grabar el teléfono personal en uso normal. No existe garantía de que un simple filtro de texto elimine todos los secretos.

Comparar primera instalación y cold/warm/hot por separado, con CompilationMode, perfiles/cachés, temperatura y repeticiones declarados. TTID/TTFD deben corresponder a la misma pantalla sin cuenta. El plan no necesita nuevas funciones de producto ni cambiar la experiencia visual.

### E. Red y autenticación, solo después de otra aprobación

Únicamente tras superar aislamiento, logs y pruebas offline: evaluar red de servicios propios con captura de metadatos autorizada en laboratorio. Si resulta imprescindible probar autenticación, usar una cuenta de prueba controlada y permitida por las reglas de Telegram, sin datos personales ni bots operativos, con credenciales API propias y sin importar sesiones. Definir límites y aprobar ese experimento antes de realizarlo. No crear cuentas automatizadas, no probar sanciones, no revocar autorizaciones ajenas ni ejecutar llamadas destructivas contra Telegram. El diagnóstico inicial no depende de ninguna cuenta.

## Pendientes exclusivos del teléfono físico y del servidor

| Comprobación | Quién/entorno la resuelve | Estado |
| --- | --- | --- |
| Page size, ABI y versión real del Poco | Titular, cinco comandos de sistema anteriores | Pendiente |
| Forma de instalación/restauración y ajustes usados | Recuerdo/registro privado del titular; no extracción de sesión | Pendiente |
| Cronología y autenticidad contextual del aviso | Titular y soporte oficial | Pendiente |
| Causa de la invalidación de sesiones/tokens y congelación | Telegram, con sus registros de servidor | No determinable por análisis estático ni por adb |
| Arranque/TTID/TTFD y recursos en este Poco | Futura identidad segura, después de aprobación | No medido |
| Carga JNI/Python/imports en este Poco | Futura compilación aprobada con datos sintéticos | No ejecutado |
| Compatibilidad 16 KB | Poco solo si PAGE_SIZE=16384; de otro modo laboratorio adicional | No certificada |

## Condiciones de cierre

Mantener PR #2 abierto. Esta auditoría se publica en un PR exclusivamente documental separado; no se fusiona automáticamente. Confirmar el estado administrativo de Actions desde GitHub si es necesario; no activarlo para el plan.

Para finalizar con seguridad el Paso 3: aprobar conclusiones/P0; resolver identidad, credenciales, logs y política de datos mediante cambios controlados; volver a verificar el artefacto resultante; completar instalación/arranque sin cuentas, evaluación nativa e informe de mediciones. Registrar resultados, errores y límites, incluyendo cualquier pendiente 16 KB aceptado expresamente. Si Telegram no aclara el incidente, conservarlo como causa no confirmada, sin inventar una absolución ni atribución. Una auditoría y pruebas locales satisfactorias no sustituyen la explicación del servidor.

**Estado de esta entrega: auditoría documental completa dentro de su alcance; ejecución Android, causa del incidente y cierre del Paso 3 pendientes. Detenerse aquí para revisión.**
