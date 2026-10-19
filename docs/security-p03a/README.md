# P0.3a — Respaldos, restauración y datos de sesión

Proyecto FlexyGram 1.0, creado y dirigido por @Lukhou23. Créditos y licencias originales conservados.

## Estado de integración y bloqueo de beta

P0.2 (PR #5, código aprobado `7ce7ba1d8c4a35d0c15586a2ddb36cf65bf09acc`) se integró por autorización explícita del responsable **solo a nivel de código** en develop: `d31d0e780fe133337b343379563d65f579acf14d`.
La recomendación histórica de mantener PR #5 abierto quedó sustituida por esta autorización. **No existe validación de ejecución Android.** [VALIDACION-ANDROID-PENDIENTE.md](VALIDACION-ANDROID-PENDIENTE.md) sigue siendo bloqueo obligatorio de cualquier beta distribuible; permite correcciones independientes de código.

La creación del issue solicitado fue intentada con la herramienta GitHub. GitHub devolvió **410: Issues has been disabled in this repository**. El conector disponible no ofrece cambiar la configuración del repositorio. El documento enlazado contiene el texto listo para publicar una vez habilitado Issues. No se presenta un documento ni un PR como si fueran un issue creado.

Rama exclusiva: `security/paso-3-p03-services-backup`, creada desde la integración anterior. No fusionar este PR sin revisión. Main intacta, PR #2 abierto. Sin Actions, publicación de APK, autenticación, P0.3b, P0.4 ni Paso 4.

## Hallazgos y correcciones

1. **Agente heredado:** `BackupAgent` instalaba un `SharedPreferencesBackupHelper` para `saved_tokens` y `saved_tokens_login` cuando no estaba aislado. P0.2 ya lo había desregistrado y bloqueado en diagnóstico, por lo que no se afirma que se ejecutara. Ahora no instala helpers ni agenda respaldo en ninguna variante; rechaza restauración key/value, no realiza full backup y descarta entidades de full restore mediante el mecanismo de descarte del framework. No elimina datos existentes.
2. **Exportación manual y de nube:** el formato JSON permitía incluir API keys, exportaba configuraciones completas y datos de bloqueo local. `SettingsBackupPolicy` establece una lista positiva, tipada y común para salida y entrada. La opción heredada includeApiKeys no permite reincorporar credenciales. No se abren almacenes de cuenta ni AI durante exportación. Se inhabilita el opt-in visual heredado sin cambiar navegación ni diseño.
3. **Importación:** antes aceptaba nombres arbitrarios de SharedPreferences del JSON. Se filtra el documento **antes de abrir cualquier namespace**. Se rechazan tokens, cuentas, rutas, userconfing/userconfigN, namespaces desconocidos, claves nuevas no revisadas, objetos anidados, tipos incorrectos, desbordamientos y sufijos de tipo no admitidos. No hay clear(), borrado, migración ni sobrescritura de sesiones.
4. **Errores de archivos JSON:** los avisos ya no muestran la excepción original, que podría incluir texto del documento malicioso.

## Ajustes conservados y restricciones revisables

No se elimina el respaldo legítimo de ajustes. Se conservan exportación/importación manual, la misma frontera para el formato de nube (transporte bloqueado por P0.2), y `EtgBackup`/`.extera`, cuyo importador ya utiliza una tabla explícita de correspondencias y validaciones. No se modifica ese formato, no se extraen archivos privados de Exteraless y solo se aplican ajustes seleccionados por el usuario a las preferencias del paquete independiente.

El JSON portátil acepta únicamente `mainconfig`, `nkmrcfg` y `themeconfig`. Las claves exactas y tipos constituyen el contrato revisable en `SettingsBackupPolicy.java`: reproducción, fuentes, burbujas, apariencia, idioma, selección de tema y algunos ajustes visuales de Neko. No se copian passcodeHash, claves API/AI, auth keys, tokens push/login, identificadores de cuentas, rutas de almacenamiento, excepciones por usuario/chat ni switches de plugins/seguridad.

**Restricción deliberada:** este contrato es más estrecho que el exportador anterior. No conserva todos los ajustes avanzados, temas personalizados serializados (`themes2`/`accents_*`), campos por cuenta/chat, localización ni claves desconocidas. Los valores existentes en el dispositivo no se borran. Antes de ampliar el contrato, revisar origen, tipo y sensibilidad de cada campo y añadir regresiones; no habilitar un bypass para exportar todo. `.extera` continúa disponible para sus ajustes previamente admitidos.

## Identidad y futura variante autenticable

Se conserva el paquete `io.github.jose22yt.flexygram.diagnostic`, el sandbox separado, accountType/authorities independientes, allowBackup=false, ausencia de backupAgent y exclusiones de cloud/device transfer de P0.2. El nombre Java heredado de una clase o un archivo de preferencias relativo no concede acceso al sandbox de Exteraless. No se agregan lecturas de rutas ajenas, migraciones automáticas, restore de sesiones ni credenciales heredadas.

Una variante autenticable futura requerirá aprobación separada: identidad/firma/servicios/credenciales propios, sesiones y claves almacenadas privadamente y excluidas de backup/transferencia, reautenticación tras reinstalación, y un transporte de **solo ajustes** con esquema versionado y destino propio. No reutilizar el agente de tokens ni convertir includeApiKeys en una excepción. Si se diseña un helper Android, usar un nombre nuevo para que entidades antiguas no se interpreten como el nuevo esquema. Mantener P0.1 y la frontera de ajustes; no se implementa ni habilita esa variante aquí.

## Pruebas y límites

**20 pruebas aprobadas, 0 fallidas, 0 omitidas.** Gradle ARM64 completo (incremental, sin saltar JNI): BUILD SUCCESSFUL en 1m 59s; verificación del estado final de fuentes en 45s, ambas con 244 tareas, 13 ejecutadas y 231 al día. Ver [evidence/tests.log](evidence/tests.log), [evidence/build-result.json](evidence/build-result.json) y [evidence/final-source-build-result.json](evidence/final-source-build-result.json). El test nuevo compila la política Java completa y el agente reales, y ejecuta los métodos reales de exportación/importación con dobles locales de Android y JSON, usando Gson de la dependencia del proyecto. Comprueba las combinaciones local/nube y includeApiKeys=true/false, conservación de ajustes, rechazo de credenciales/namespaces, tipos malformados, no mutación de datos de sesión ficticios y descarte del agente. No es un test de framework Android.

Reproducción (sin red; Gson ya aprovisionado por Gradle):

```bash
export JAVA_HOME=/ruta/al/jdk21
export PATH="$JAVA_HOME/bin:$PATH"
export GRADLE_USER_HOME=/ruta/al/cache-gradle
export GSON_JAR=/ruta/al/cache/gson-2.14.0.jar
python -m unittest discover -s tests/security -v
# Con SDK/NDK/Chaquopy y configuración local de laboratorio aprovisionados:
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleDebug --offline --no-watch-fs --no-daemon --max-workers=2
```

La compilación es interna, no una distribución ni validación de arranque. No se utilizaron cuentas, datos personales, sesiones reales, solicitudes Telegram ni dispositivos físicos. Persisten la prueba Android, restauración real de framework/OEM, observación de tráfico y compatibilidad 16 KB. Las herramientas privilegiadas externas pueden ignorar exclusiones Android: no se afirma resistencia a root, extracción física ni a OEM que incumplan políticas.

Referencias: [Auto Backup y reglas](https://developer.android.com/identity/data/autobackup), [cambios de backup Android 12](https://developer.android.com/about/versions/12/behavior-changes-12#backup-restore). `allowBackup=false` por sí solo no evita todas las transferencias OEM; se conservan las exclusiones explícitas de P0.2.
