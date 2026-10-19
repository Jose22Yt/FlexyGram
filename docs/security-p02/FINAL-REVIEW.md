# P0.2 — endurecimiento final antes de revisar el PR #5

FlexyGram 1.0, creado y dirigido por **@Lukhou23**. Revisión de `e7a1db7a0fc2a0f4c44afa1332555f1d858e02fa` en la misma rama `security/paso-3-p02-identity-api`. No se fusiona el PR, no se modifica main, no se habilita Actions, no se publica una APK y no se inicia P0.3/P0.4/Paso 4. Se mantienen los créditos y licencias originales.

## Problema y alcance de la corrección

La ausencia de INTERNET y las guardas Java/C++ del PR eran necesarias, pero su manifiesto binario registrado todavía solicitaba 61 permisos y contenía 13 componentes habilitados/exportados. Algunos ofrecían integraciones de autorización, automóvil o multimedia innecesarias para abrir un diagnóstico limpio sin cuentas. Su existencia no demuestra ejecución, explotación ni relación causal con el incidente original.

Se cambia únicamente la superficie Android del diagnóstico y sus comprobaciones: permisos, enabled/exported, filtros externos de LaunchActivity y marcadores para dependencias. No se cambia código de autenticación, sockets, plugins, animaciones, navegación, renderizado o reproductor. Las guardas existentes y las correcciones de secretos P0.1 permanecen intactas.

La rama ya es exclusivamente diagnóstica en todos sus build types; estos cambios no afectan a una variante autenticable porque aquí no existe tal variante. Se conservan las clases/componentes originales en el código, pero sus servicios y providers de datos no son puntos de entrada externos del diagnóstico. Se conserva un inicializador gráfico local y privado, descrito abajo.

## Permisos conservados y fundamento

| Permiso | Tipo y motivo |
| --- | --- |
| `android.permission.ACCESS_NETWORK_STATE` | Permiso normal para consultas locales de ConnectivityManager. ApplicationLoader.postInitApplication y ensureCurrentNetworkGet observan la conectividad y registran callbacks durante la inicialización original. No concede sockets ni acceso a Internet. |
| `io.github.jose22yt.flexygram.diagnostic.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION` | Permiso **signature** de la propia app. Mantiene la protección de receptores dinámicos de compatibilidad AndroidX en versiones antiguas; no concede acceso a cuentas, contactos, teléfono u otras apps. |

El resto se excluye. INTERNET sigue explícitamente retirado. Se combinan exclusiones explícitas, marcadores `removeAll` y una lista permitida comprobada sobre el resultado real; la declaración propia conserva solo la protección signature anterior. El primer merge aún añadió recepción FCM, por lo que también se excluyó expresamente `com.google.android.c2dm.permission.RECEIVE`. No se confía únicamente en un marcador general. La prueba del manifiesto fusionado exige exactamente estos dos permisos y una única declaración signature propia. No hay permisos peligrosos que conceder para esta prueba de arranque; esto no sustituye observar la UI en Android.

### Permisos retirados

La lista literal completa antes/después y los cambios respecto a las solicitudes del fuente quedan en las evidencias de esta revisión. Se retiran 58 solicitudes adicionales del manifiesto principal; las contribuciones innecesarias de bibliotecas también se excluyen del resultado fusionado.

| Grupo | Motivo de exclusión |
| --- | --- |
| Cámara, micrófono, audio y Bluetooth | No se prueba captura, llamadas ni reproducción. Los servicios multimedia/VoIP quedan deshabilitados. La creación de buffers o la consulta de recursos no requiere conceder cámara/micrófono. |
| Ubicación fina/aproximada/en segundo plano y ubicación multimedia | No hay cuenta ni escenario de mapas o ubicación compartida. |
| Estado/números telefónicos, perfil, cuentas y sincronización | No hay login, importación de cuentas ni servicio sync activo. Las guardas de UserConfig/AuthTokensHelper y AccountManager siguen vigentes. |
| Superposición, llamadas propias y pantalla completa | No se necesita una llamada/ventana flotante para abrir la Activity. |
| Instalación de APK y excepciones de batería | El actualizador permanece bloqueado; esta revisión no instala actualizaciones ni mantiene servicios en segundo plano. |
| Foreground services, boot, notificaciones y wake lock | No hay servicios habilitados ni notificaciones de cuenta. El arranque interactivo no necesita conservar CPU con un wake lock. |
| Biometría, credenciales, shortcuts, insignias y servicios comerciales | No hay sesión restaurada ni flujo de passkey/biometría, anuncios, facturación o badges de cuentas que probar. |
| Otros permisos heredados, incluidos Wi-Fi y vibración | No son imprescindibles para este escenario de apertura. No se presenta el diagnóstico restringido como equivalente funcional ni como benchmark completo del cliente original. |

Los permisos de datos compartidos/contactos que el PR ya había retirado continúan ausentes. No se concede permiso de almacenamiento para recuperar sesiones ni se extraen datos de otro cliente.

## Componentes revisados

La única entrada habilitada/exportada que se conserva es el alias de lanzador `org.telegram.messenger.ExteralessIcon`, con ACTION_MAIN y categorías de launcher; apunta a `org.telegram.ui.LaunchActivity`. El nombre de clase/alias heredado no es el application ID. LaunchActivity permanece habilitada, pasa a no exportada y deja de registrar enlaces, shares y demás filtros externos. No se renombra el lanzador ni se modifica su aspecto.

Todos los otros aliases están deshabilitados y no exportados. Las actividades internas permanecen disponibles para la navegación original, pero son explícitamente no exportadas. No se altera ningún layout ni motor de navegación. Los aliases no filtran por sí solos todos los extras de un intent explícito: la autorización, restauración y red siguen bloqueadas por las políticas fijas ya probadas, independientemente de la ruta de entrada. No se considera un intent-filter una barrera de autenticación.

| Componente antes habilitado/exportado | Resultado y motivo |
| --- | --- |
| LaunchActivity | Habilitada, privada y sin filtros externos. Acceso público normal solo mediante su alias de launcher. |
| CallsActivity (alias) | Deshabilitado/no exportado: sin cuentas ni llamadas que iniciar. |
| WearAuthListenerService | Deshabilitado/no exportado: su callback procesa ofertas Wear y puede abrir LaunchActivity/WearAuthSheet. No es necesario para el arranque. |
| TelegramCarAppService | Deshabilitado/no exportado: Debug usa un validador de hosts amplio y crea sesiones de automóvil. No se prueban Auto/Automotive. |
| BringAppForegroundService | Deshabilitado/no exportado: no se necesita que una app externa lleve el diagnóstico al frente. |
| VideoEncodingService | Deshabilitado/no exportado: sin codificación de vídeos en segundo plano. |
| MusicPlayerService / MusicBrowserService | Deshabilitados/no exportados: no se abre una API de reproducción/biblioteca para otras apps. |
| RefererReceiver | Deshabilitado/no exportado: el referrer de instalación no es necesario, aunque antes tuviera protección de permiso. |
| CallNotificationSoundProvider | Deshabilitado/no exportado: no hay sonido de notificaciones de llamadas que servir a otro UID. |
| ChooserTargetServiceCompat (biblioteca) | Se excluye del merge: no hay integración de compartir/targets que probar. |
| ProfileInstallReceiver (biblioteca) | Se excluye del merge: no es necesario para apertura; esta revisión no prepara Macrobenchmark ni perfiles. |

Además se revisan y deshabilitan los servicios, receptores y providers de datos locales no exportados: FileProvider, imágenes de notificación, streaming, icon packs, widgets, acciones de notificación/VoIP, push, sync, migración e importación. Ninguno es necesario para la apertura limpia sin cuenta; el acceso directo a recursos, JNI y directorios privados de la app permanece disponible. No se borran sus clases ni sus archivos.

Se excluyen expresamente los servicios de ChooserTarget, metadatos de credenciales, descubrimiento de componentes ML Kit/Firebase e invalidación multiproceso Room, y los receivers de notificación Car y ProfileInstaller. Son integraciones externas, de SDK o de trabajo entre procesos no requeridas para abrir el diagnóstico sin cuentas; el almacenamiento de mensajes utiliza SQLite y no necesita el servicio de invalidación Room para este escenario. Las dependencias de código permanecen. Los marcadores generales no bastaron en el primer merge: la auditoría detectó estas contribuciones y se añadieron exclusiones concretas. El manifiesto final se comprueba contra una lista permitida, sin deducir el resultado de los marcadores. Las evidencias enumeran cada componente final y su estado, incluidos los privados.

### Inicializador local conservado

`ru.noties.jlatexmath.JLatexMathInitProvider` permanece habilitado, **no exportado**, con authority propia `${applicationId}.jlatexmathinitprovider`. Su `onCreate` llama a `JLatexMathAndroid.init(getContext())`, que conserva el contexto de recursos de la app; sus operaciones de consulta/escritura no suministran datos. La biblioteca usa ese contexto para assets y fuentes del renderizado matemático. Se mantiene para conservar la inicialización gráfica y evitar un fallo por contexto no preparado, no como servicio externo. No requiere permisos, cuentas ni red y no permite a otro UID entrar en la app. El verificador permite exclusivamente esta excepción entre los providers habilitados.

## Verificación y límites

Se mantienen las **18 pruebas existentes**. Se amplía el contrato del manifiesto para no permitir permisos o componentes heredados que se pasaran por alto; las pruebas de secretos, resolver API, callbacks y transporte Java/nativo continúan ejecutándose con datos ficticios y dobles locales. La nueva utilidad `tests/security/manifest_surface.py` valida además un manifiesto fusionado real y genera un inventario JSON. Las pruebas unitarias no equivalen a un Android ejecutándose.

Reproducción de las comprobaciones adicionales, después de compilar:

```sh
python tests/security/manifest_surface.py TMessagesProj/build/intermediates/merged_manifest/debug/processDebugMainManifest/AndroidManifest.xml
python tests/security/manifest_surface.py --negative-checks TMessagesProj/build/intermediates/merged_manifest/debug/processDebugMainManifest/AndroidManifest.xml
python tests/security/manifest_surface.py --apk RUTA_APK_INTERNO RUTA_BUILD_TOOLS/aapt2
```

La última orden inspecciona el manifiesto binario real mediante aapt2, sin instalar ni subir el archivo. Debe superar la misma lista permitida que el XML fusionado; un éxito de Gradle o del XML intermedio no sustituye este control.

El entorno anterior ya no estaba disponible. Se recuperan fuente/submódulos y se prepara de nuevo el toolchain fijado: JDK 21, Wrapper 9.7.1, AGP 9.3.1, SDK 37 r2 y SDK 35, Build Tools 36.0.0, NDK 27.2.12479018, CMake 3.31.6, Python 3.11/Chaquopy 17. La compilación requerida es ARM64 completa, sin `NATIVE_TARGET=SKIP`. Una clave diagnóstica local nueva no se publica ni se incluye en evidencias.

No hay dispositivo Android conectado ni emulador instalado; /dev/kvm tampoco está disponible. No se usa el Poco ni ninguna cuenta. Instalación, apertura sin crash, ausencia real de diálogos, tráfico del UID, servicios en ejecución y restauración en Android **siguen pendientes**. No se infiere un resultado de tráfico por la ausencia del permiso ni se inventa un Logcat.

Las cuatro bibliotecas Python previamente señaladas siguen siendo un pendiente para compatibilidad nativa plena con 16 KB. No se sustituyen ni eliminan en este endurecimiento. El page size real de un futuro laboratorio debe medirse antes de interpretar un fallo.

## Variante autenticable futura: propuesta, no implementación

Mantener esta rama identificada como diagnóstico offline e inmutable. Una futura variante autenticable requerirá un cambio separado y aprobado: application ID y firma propios separados del diagnóstico; credenciales Telegram propias cuya titularidad verifique el responsable; recursos/manifiesto y servicios de Firebase/OAuth/push/Maps/actualización bajo su control; permiso INTERNET únicamente en esa variante; política explícita de datos/backup y permisos por funcionalidad. Conservar íntegramente los arreglos de logging P0.1 y sus pruebas para ambas variantes.

La configuración ausente debe seguir fallando de manera segura; nunca recuperar un fallback heredado ni desbloquear esta APK mediante preferencias. Separar políticas y artefactos en build, con pruebas negativas que impidan mezclar identidad, claves de firma, permisos y servicios. Comenzar con pruebas sin cuentas y aprobar por separado cualquier uso de una cuenta de laboratorio permitida por Telegram. No se implementa ni se habilita nada de ello aquí, ni se inicia P0.3/P0.4.

## Decisión para revisión

Mantener PR #5 abierto y sin fusionar. El endurecimiento y una compilación correcta permiten revisar el código, pero no prueban que el arranque Android tolere todas las restricciones. Se recomienda completar una prueba offline limpia en Android de laboratorio antes de dar por validado el arranque y decidir la fusión. Los resultados reales de esta ejecución y sus límites deben consultarse en las evidencias finales adjuntas a este documento.

## Resultados reales de esta ejecución

- **18 pruebas aprobadas, 0 fallidas y 0 omitidas**, incluyendo P0.1. Además, diez mutaciones del manifiesto fusionado (INTERNET/cámara, Wear/Car, providers expuestos, permiso propio debilitado, backup y servicio desconocido) fueron rechazadas por el verificador.
- Compilación Gradle ARM64 completa con JNI y runtime Python: **BUILD SUCCESSFUL**, salida 0, **8 min 44 s**, 244 tareas, sin SKIP nativo. Después de incorporar las exclusiones precisas hubo una integración de **32 s**, salida 0. La comprobación del binario detectó que el enlace de recursos conservaba un manifiesto anterior; se eliminaron únicamente salidas generadas de recursos/APK y se reconstruyó sin caché ni watch-fs: **BUILD SUCCESSFUL en 28 s**, 244 tareas, salida 0. El APK de esa última pasada sí pasó el control binario. No se publicó ningún candidato.
- Manifiesto fusionado **y manifiesto binario del APK final**: exactamente dos permisos; **61 → 2**, con 59 retirados del resultado anterior. **13 → 1** componentes habilitados/exportados. Se inventariaron los **89 componentes finales**, privados o deshabilitados salvo el alias público de launcher y el provider gráfico privado explicado arriba.
- Se verificó el bytecode de la dependencia real `jlatexmath-android:0.2.0`, además de su fuente, para justificar conservar su inicializador local. SHA-256 del AAR: `b16824328d45ed86892f7f8aa74a542fc361b8a94004de8ca5ae86113b78a89f`.
- APK **interno**, no instalado ni distribuido: paquete propio correcto, etiqueta FlexyGram Diagnostic, firma verificada, CRC del APK y seis contenedores IMY correcto, zipalign correcto y 18 ELF instalables AArch64. El SHA-256 se conserva solo como trazabilidad en la evidencia; no es un enlace a una APK. La firma de laboratorio es nueva: no se afirma reproducción bit a bit de la compilación anterior.
- Revisión estructural del binario nuevo: 97 ELF en total; persisten exactamente cuatro fallos PT_LOAD de 16 KB en libexslt, libfreetype, libxml2 y libxslt. No se certifica compatibilidad completa ni se confunden estos fallos con una causa de lentitud o del incidente Telegram.
- **Android no ejecutado:** cero targets en adb, sin binario de emulador y sin KVM. Instalación, primer arranque, diálogos reales, red por UID, plugins/servicios en ejecución y restauración siguen pendientes. No hubo cuentas, llamadas Telegram ni uso del Poco.
- Los primeros intentos fallaron por proxy del host, esquemas de metadatos del SDK y materialización de alias/permisos de ejecución del NDK. Se corrigió solamente el entorno local; no se modificaron versiones, guardas ni fuentes Java/C++ para resolverlos. Los resultados de todos los intentos se distinguen de la compilación satisfactoria. Persisten avisos de Gradle/CMake, recursos, Java/C++ y del merge; no se ocultaron ni se declaran fallos de la aplicación por sí solos.

Evidencias: [resultados y logs de pruebas](evidence/final-review/tests.log), [comparación exacta de superficie](evidence/final-review/surface-changes.json), [inventario del APK final](evidence/final-review/binary-surface.json), [compilación completa](evidence/final-review/assemble-arm64-aliasfix-result.json), [última compilación validada](evidence/final-review/assemble-arm64-repackage-result.json), [validación del artefacto interno](evidence/final-review/internal-apk-validation.json), [estado real del laboratorio](evidence/final-review/android-runtime.json) y [prueba de ausencia de cambios en el núcleo](evidence/final-review/source-verification.json). Los logs completos depurados de las tres pasadas satisfactorias están en esa misma carpeta. No contiene APK, claves privadas, contraseñas ni datos de cuenta.

Fuentes primarias para las reglas de merge y permisos: [Manifest merger](https://developer.android.com/build/manage-manifests), [services](https://developer.android.com/guide/topics/manifest/service-element), [uses-permission](https://developer.android.com/guide/topics/manifest/uses-permission-element). La evaluación de las rutas concretas se basa en el código de este repositorio.
