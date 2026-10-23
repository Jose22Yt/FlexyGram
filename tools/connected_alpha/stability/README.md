# Connected Alpha — estabilidad y primera prueba física

> Evidencia histórica del PR #57. Para la integración con #56, consultar `../integration-result.json` y ejecutar `python3 tools/connected_alpha/run_checks.py`.

Base de esta revisión: PR #55, `4b0bf291284ff64c3cac89ccdf2b76bb00041e39`.
Origen: Exteraless `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`.
Rama independiente: `stability/connected-alpha-review`. Destino del borrador: la rama del PR #55; no main/develop.

## Corrección demostrable

PR #55 cambia `AyuMessagesController.attachmentsPath` desde Downloads a `getFilesDirFixed()/Saved Attachments`. El recurso principal `provider_paths.xml` no incluye ese directorio privado. `AndroidUtilities.openDocument` y `openForView` usan `FileProvider.getUriForFile` para abrir archivos con otras aplicaciones. Cuando el archivo está en esa nueva ruta, no existe una raíz configurada y la resolución se rechaza; puede mostrarse el aviso de que no hay visor aunque sí exista uno. Es una regresión de configuración identificada en código, no una reproducción en teléfono.

Se añade **solo en connectedAlpha** un overlay XML que conserva las ocho rutas anteriores y agrega `files-path` para `Saved Attachments/`. El proveedor sigue sin exportarse y exige permisos URI temporales; el código original de apertura ya concede lectura. No se mueve ningún archivo ni se expone todo `files/`. Las rutas amplias heredadas `/storage/` y almacenamiento externo se conservan; este cambio no es una auditoría integral de FileProvider.

Los tests modelan contención canónica según la configuración XML, no ejecutan AndroidX. El test positivo falla con el XML anterior (PDF y vídeo anidado) y pasa con el overlay. Comprueba además límites entre directorios, `..`, preferencias, bases de datos y preservación exacta de rutas anteriores. La compilación de recursos/manifest combinado y la apertura real siguen pendientes.

Referencia del contrato de FileProvider: https://developer.android.com/reference/androidx/core/content/FileProvider

## Auditoría técnica

| Área | Evidencia y conclusión | Riesgo o comprobación pendiente |
|---|---|---|
| Inicio/ciclo de vida | `ApplicationLoader.onCreate` carga NativeLoader antes de `native_setJava`; `postInitApplication` mantiene la inicialización original y su guardia. El único cambio funcional de ese archivo en #55 desactiva colección Crashlytics. | Arranque de proceso, inicio desde push, rotación, retorno y muerte de proceso; una configuración Firebase incorrecta puede impedir inicialización. No hay APK ejecutada. |
| Motor/JNI | NativeLoader, ConnectionsManager, controladores y árbol JNI completos conservados. `source-audit.json` amplía las 15 comparaciones existentes con otras 11. | Firma, ABI, carga Chaquopy y ELF reales 4/16 KiB deben validarse sobre la APK final. Paridad no demuestra compatibilidad de binarios. |
| Navegación/Atrás | LaunchActivity registra OnBackAnimationCallback en API >=34, OnBackInvokedCallback en API 33, y desregistra en destrucción; manifiesto habilita callback. ChatActivity, DialogsActivity y ActionBarLayout originales. | Cancelar/confirmar gesto, teclado, cajón, reproductor, chat raíz y pulsaciones rápidas. No se cambian animaciones sin reproducción de defecto. |
| Permisos/almacenamiento | Identidad de cuentas/proveedores separada; BuildVars conserva scoped storage en API >29; lectura multimedia y POST_NOTIFICATIONS declarados. Se corrige el hueco FileProvider de adjuntos privados. | Denegar/revocar contactos, fotos parciales, micrófono/cámara y notificaciones. Comprobar descargas, SAF, captura y apertura externa. No solicitar permisos extra para ocultar fallos. |
| Multimedia | MediaController, MusicPlayerService, FileLoader y AndroidUtilities idénticos al origen. Manifiesto conserva servicio mediaPlayback. ImageLoader cambia nombre del directorio de caché legacy; no se altera reproducción. | Audio iniciado en primer plano, pantalla apagada, controles de notificación/Bluetooth y audio focus en Android 17; llamadas no se consideran aprobadas. |
| Segundo plano/push | NotificationsController, NotificationsService, PushListenerController y proveedor Google originales. No se añade otro servicio. | Registro FCM propio, permiso de notificación y restricciones HyperOS; un cliente que recibe en primer plano puede fallar al apagar pantalla. No publicar tokens ni logs completos. |
| Rendimiento | No se cambia Java/Kotlin, JNI, colas de trabajo, navegación ni renderizado en este PR. El overlay no añade trabajo por frame. | Igualdad de fuentes no demuestra igualdad de fluidez. Configuración de build, calentamiento JIT, plugins, red y cachés pueden alterar resultados. |

## Android 17: separar dispositivo de target SDK

Esta base declara **compileSdk 37, targetSdk 36, minSdk 24** en `build.gradle`. Compilar con 37 no equivale a apuntar a 37. No se modifica Gradle ni la rama/sistema de compilación de Work 1 (#56).

Documentación oficial consultada el 22-10-2026:

- https://developer.android.com/about/versions/17/behavior-changes-all : restricciones de audio en segundo plano y límites de memoria afectan a aplicaciones ejecutadas en Android 17. Probar audio iniciado por el usuario, retomar desde notificación y sesiones largas. La protección OTP puede impedir autolectura; mantener entrada manual nativa. Las concesiones implícitas URI se endurecen en Android 18, no deben presentarse como fallo obligatorio de Android 17.
- https://developer.android.com/about/versions/17/behavior-changes-17 : carga nativa dinámica de archivos solo lectura, MessageQueue nuevo y restricciones de campos static final se vinculan a target 37. NativeLoader conserva un fallback que escribe un archivo cargable: **riesgo para un futuro target 37**, no motivo demostrado para modificar ahora código original ni elevar/bajar el target. Revisar también Chaquopy/plugins antes de ese cambio.
- https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture : verificar callbacks, cancelación y navegación real; no inferir el resultado por tener el atributo en el manifiesto.

El modelo comercial, ROM, API y tamaño de página del Poco no se han observado. Usar los valores reales del dispositivo; el nombre del teléfono no demuestra ARM64/16 KiB ni una versión de HyperOS.

## Controles para el laboratorio

Usar la APK final autorizada de Work 1 y su informe de verificación. Registrar commit exacto de compilación, SHA-256 APK, certificado, versión de Android/API, ROM, ABI, tamaño de página y fecha. Si ese commit no contiene este cambio, el resultado no valida esta corrección. Nunca subir claves, códigos de acceso, sesiones, mensajes, capturas con contactos o logs sin revisar.

El preflight **solo lee metadatos**, no instala, no inicia la aplicación, no cambia ajustes ni completa pruebas. Requiere selección explícita de dispositivo; no imprime su número de serie. No prueba firma ni identidad de la APK instalada: contrastar eso con el artefacto verificado. Lista solo presencia de Alpha, Exteraless y Telegram oficial, no toda la lista de aplicaciones.

```sh
python3 tools/connected_alpha/stability/physical_preflight.py --serial SERIAL_ELEGIDO > preflight-local.json
```

Rechaza API distinta de 37, ABI distinta de ARM64, emulador declarado, tamaño de página desconocido y errores ADB. Incluso con metadatos correctos, los diez escenarios quedan PENDING. Un valor qemu vacío es metadato habitual, no certificación de que se trata del Poco: verificar visualmente el equipo. El informe es local y debe revisarse antes de compartirse.

| # | Procedimiento | Aceptación y evidencia mínima | Estado |
|---|---|---|---|
| 1 | Instalar Alpha junto a clientes existentes, sin desinstalar ni borrar datos. Comparar antes/después. | Paquete independiente y otras apps abren con sus cuentas intactas; verificación de certificado/APK y registro de instalación sin datos privados. | PENDING |
| 2 | Tres arranques en frío, tres relanzamientos, diez retornos desde segundo plano; rotar y recrear proceso en pantalla no sensible. | Sin crash/ANR ni bloqueo; retorno coherente. Registrar tiempos y categoría de error, no contenido de pantalla. | PENDING |
| 3 | Primera apertura sin cuenta. Iniciar sesión manualmente. | Login original por teléfono/código/2FA; sin pantallas offline. No registrar número/código/contraseña. | PENDING |
| 4 | Abrir lista con cuenta autorizada y esperar sincronización en red estable. | Conversaciones reales y actualización tras reconexión; anotar duración y resultado. | PENDING |
| 5 | 30 ciclos de abrir/cerrar chat; Atrás físico/3 botones y gesto; cancelar gesto a mitad; repetir con teclado, cajón, foto/vídeo y audio abiertos. | Un solo retroceso por acción, cancelación conserva pantalla, sin pantalla negra/toques bloqueados ni cierre incorrecto. | PENDING |
| 6 | Intercambiar mensajes inocuos con cuenta de prueba consentida; desconectar/reconectar y reenviar. | Envío/recepción y estados correctos sin duplicados inesperados; registrar solo tiempos/cantidad. | PENDING |
| 7 | Foto, vídeo, voz, música y documento; cargar/descargar, pausa/búsqueda; abrir PDF guardado en historial con visor externo. Denegar y luego conceder permisos. | Reproduce/abre correctamente, cancelación/denegación manejadas; probar adjunto de Saved Attachments con visor instalado. | PENDING |
| 8 | Conceder notificaciones y recibir mensaje con pantalla apagada; probar 1/5/15 minutos, retorno desde notificación y audio de fondo. Repetir con ajustes HyperOS predeterminados registrados. | Mensaje notificado, destino correcto, audio esperado; anotar entrega/latencia. No usar force-stop como prueba de push: Android lo bloquea por diseño. | PENDING |
| 9 | Confirmar API 37/ABI/páginas reales; repetir escenarios 2/5/7/8 y sesión de 30 minutos con cambios de orientación/tema y memoria. | Sin excepción nativa, crash/ANR ni pérdida de estado; revisar causas de cierre localmente. Una página 4 KiB no valida 16 KiB. | PENDING |
| 10 | Comparar Exteraless y Alpha en el mismo teléfono, red, frecuencia, temperatura, ajustes/temas/plugins y contenido de prueba; alternar orden A/B. | Registrar muestras y distribución, no solo impresión subjetiva; metodología siguiente. | PENDING |

### Medición de fluidez

Registrar 10 arranques fríos y 10 calientes por aplicación, excluyendo login de las medidas; 30 aperturas/cierres del mismo chat y desplazamiento de 30 segundos en el mismo contenido. Separar tiempo de red de tiempo de UI. Mantener mismas versiones y configuración de optimización, ahorro de batería y frecuencia de pantalla; documentar cualquier diferencia entre las builds. No borrar datos ni forzar cachés para fabricar igualdad.

En laboratorio, `adb -s SERIAL shell am start -W -n PAQUETE/org.telegram.ui.LaunchActivity` permite medir tiempos de lanzamiento (el comando inicia la app). Para arranque frío detener únicamente el paquete de prueba entre muestras y reabrirlo; finalizar esta serie antes de probar push. Usar `dumpsys gfxinfo PAQUETE reset` antes y `dumpsys gfxinfo PAQUETE framestats` después del recorrido para separar contadores; recoger `dumpsys meminfo PAQUETE` y causas de salida con `dumpsys activity exit-info PAQUETE` **solo localmente**, revisando datos antes de compartir. Los comandos cambian contadores/inician la app; el preflight no los ejecuta.

Comparar mediana y p95 de tiempos, frames lentos y memoria. Umbral inicial propuesto para investigar, no garantía del producto: regresión repetida >10% en mediana o p95 con al menos dos series comparables. Si hay discrepancia, perfilar primero y corregir solo la causa demostrada. Gfxinfo no representa por sí solo todas las superficies de vídeo; observar reproducción por separado. No hay mediciones ejecutadas en este entorno.

## Validación reproducible de esta rama

```sh
git fetch origin 1ad6a60a6834ffca722b1a22f4fba27ecb29a061
python3 tools/connected_alpha/check_source.py
python3 tools/connected_alpha/stability/audit_sources.py
python3 -m unittest discover -s tools/connected_alpha -p 'test_*.py' -v
python3 -m unittest discover -s tools/connected_alpha/stability -p 'test_*.py' -v
git diff --check
```

Resultados: 8 pruebas existentes del verificador + 9 nuevas de configuración/collector = **17/17 PASS host**. Las subpruebas no se cuentan como pruebas adicionales. El XML anterior reproduce el fallo de cobertura; el overlay lo corrige. 15 componentes críticos del verificador original + 11 adicionales son idénticos al origen, y el árbol JNI comprometido es idéntico. Ver `validation.txt` y `source-audit.json`. Se necesita el objeto upstream para comparar (una copia shallow no lo incluye automáticamente).

No se ha ejecutado Gradle, AAPT2, AndroidX ni instrumentación en esta revisión: este host no dispone de ADB/SDK/JDK. No se compila ni firma otra APK para competir con Work 1. El verificador del PR #55 espera erróneamente libtmessages.so; #56 ya corrige a libtmessages.49.so. Se registra aquí y se evita tocar los archivos de build/verificación de #56. **Los 10 escenarios físicos permanecen pendientes.** La ausencia de defectos demostrados en los demás componentes no equivale a certificar estabilidad ni Android 17.
