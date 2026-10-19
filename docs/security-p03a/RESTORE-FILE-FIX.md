# Corrección final de onRestoreFile — PR #6

Revisión sobre `2112c856ed053eeb3d1ece9fbca46e0c0854884e`. Único archivo funcional modificado: `BackupAgent.java`. No se modifica SettingsBackupPolicy, SettingsBackupHelper, CloudSettingsHelper, .extera, manifiesto, configuración de compilación ni guardas P0.1/P0.2.

## Defecto confirmado y descarte seguro

La implementación anterior pasaba destino null a `super.onRestoreFile`. El callback público AOSP consulta la elegibilidad y puede acceder a `destination.getCanonicalPath()` antes de llegar a `FullBackup.restoreFile`. Que el helper interno del framework acepte null para descartar no hace seguro pasarlo al callback público. El doble anterior solo guardaba el destino y no detectaba esa diferencia.

Ahora no se llama a ningún restaurador heredado de archivos, no se consulta el destino y no se escribe en almacenamiento. Ambas entradas públicas de restauración de archivos llaman a un descarte acotado:

- Tamaño negativo: IOException antes de tocar el descriptor.
- Tamaño cero (directorio/archivo vacío): no lectura, duplicación ni cierre del descriptor.
- Tamaño positivo: dup del descriptor, AutoCloseInputStream sobre la copia y buffer fijo de 8192 bytes. Cada lectura solicita como máximo min(buffer, bytes restantes). No se lee más allá de la entidad ni se consume la siguiente.
- Se cierra únicamente la copia propia, tanto en éxito como en error. POSIX dup comparte la posición del flujo con el descriptor original, pero no su propiedad de cierre. Nunca se usa AutoCloseInputStream sobre el original.
- EOF prematuro, falta de datos o lectura sin progreso: error controlado; no se finge haber descartado la entidad completa. No hay reintentos infinitos ni registros de valores privados.

## Rutas Android revisadas

| Ruta | Revisión / tratamiento |
|---|---|
| minSdk 24; callback File existente desde API 14 | AOSP android-7.0.0_r1 y SDK 34 revisados: resolución dominio/ruta valida el destino y llama al callback público File para ubicaciones válidas. Se sustituye este callback, sin delegar al escritor. |
| Dominio/ruta internos (no SDK público) | No se redefine la API oculta. AOSP dirige ubicaciones válidas al callback público y descarta por su helper interno las ubicaciones rechazadas. No confundir esa ruta interna con pasar null al callback público. |
| Key/value API 24+ | onRestore con versión int sigue siendo no-op, sin helpers ni restauración de preferencias. |
| Key/value API 28+ | La implementación heredada de la sobrecarga long dirige a la int; se conserva el rechazo. Probada esa delegación en el modelo local. |
| Android 36.1+ / SDK de compilación 37 | Existe otra entrada pública con FullRestoreDataInput. Se redefine explícitamente para descartar getData/getSize, sin asumir cómo su implementación predeterminada escribe o adapta la llamada. La clase de la API nueva no se invoca desde código de aplicación en Android anterior. |
| Full backup / manifiesto | onFullBackup sigue vacío; sin helpers/programación de tokens. Agente no registrado, allowBackup=false y exclusiones de extracción intactos. |

La anotación NewApi solo identifica el callback nuevo, no es una guarda de ejecución. Su enlace y funcionamiento real en ART/SDK soportados, incluyendo Android mínimo, siguen pendientes del laboratorio Android; el test JVM no los certifica. No se habilita el agente para completar pruebas.

## Regresiones reales ejecutadas en JVM, con límites explícitos

`restore_harness.py` reproduce la consulta de ruta del destino del callback padre, además de posición compartida y cierres independientes para descriptores duplicados. No se presenta como un framework Android completo.

Se compila y ejecuta el BackupAgent de producción. Casos: dos entidades consecutivas, lectura parcial, entidad mayor que el buffer, destino null ignorado localmente, directorio/archivo vacío, callback FullRestoreDataInput, tamaño negativo, entrada ausente, EOF truncado, error de lectura y lectura sin progreso. Se comprueban las copias cerradas y originales abiertos. Un fixture crea archivos privados y tokens sintéticos; al terminar se comparan bytes, preferencias y número de archivos, sin mutaciones ni archivos de destino nuevos.

La prueba de mutación repone exactamente el defecto `super.onRestoreFile(..., null, ...)`: el nuevo doble lo rechaza con NullPointerException y el caso deja de pasar. También se fortaleció el doble utilizado por la prueba anterior de exportación/importación.

Resultado de la suite: **22 aprobadas, 0 fallidas, 0 omitidas**. No se usaron cuentas, claves, sesiones reales ni servidores Telegram. La construcción ARM64 completa incremental terminó con **BUILD SUCCESSFUL en 41s**, salida 0, 244 tareas (7 ejecutadas, 237 al día), JNI incluido sin SKIP nativo; 42.17s de tiempo total del proceso. Los logs están en `evidence/restore-fix/`. Sigue pendiente validación en Android real de laboratorio, Binder/descriptores nativos, ART y comportamiento OEM, además del bloqueo de beta y 16 KB ya documentados.

## Ajustes que dejaron de exportarse, sin cambiar la política

Ver [PORTABLE-SETTINGS-CHANGES.json](PORTABLE-SETTINGS-CHANGES.json). Comparación reproducible con el exportador anterior a P0.3a en develop d31d0e7; no contiene valores privados.

- `userconfing`: saveIncomingPhotos, passcodeHash, passcodeType, autoLockIn, useFingerprint. No se reincorporan hashes ni credenciales.
- `mainconfig`: ajustes de ubicación/amanecer de modo nocturno, umbral de brillo (autoNightBrighnessThreshold), directShareHash, dominios restringidos, timestamps de mantenimiento y avisos/hints. El inventario lista cada clave exacta (18).
- `nkmrcfg`: solo permanecen las claves booleanas/enteras y stickerSize_float declaradas en la política. Los demás valores, incluidas API keys, identificadores, rutas, preferencias por cuenta y claves nuevas, no son portátiles.
- `themeconfig`: solo permanecen lastDayTheme/lastDarkTheme válidos y accent_current_* enteros con nombre válido; themes2, accents_* serializados y otros metadatos no se exportan.
- `aiConfig`: deja de exportarse toda la sección. No confundir ajustes de AI con una excepción para copiar claves.

El exportador anterior enumeraba preferencias almacenadas de nkmrcfg/themeconfig, incluyendo claves dinámicas y futuras. No existe una lista finita exacta de todos los campos posibles sin inventariar datos reales; por ello se documentan el conjunto permitido exacto y la regla complementaria de exclusión. Se revisarán ajustes inocuos excluidos en otra etapa, sin relajar esta corrección ni permitir credenciales. No se borra ningún valor local.

## Fuentes primarias

- [AOSP Android 7.0 BackupAgent](https://github.com/aosp-mirror/platform_frameworks_base/blob/android-7.0.0_r1/core/java/android/app/backup/BackupAgent.java).
- [AOSP SDK 34 BackupAgent](https://android.googlesource.com/platform/prebuilts/fullsdk/sources/+/refs/heads/androidx-compose-integration-release/android-34/android/app/backup/BackupAgent.java).
- [Contrato público BackupAgent](https://developer.android.com/reference/android/app/backup/BackupAgent): tamaño máximo de lectura, sobrecarga long y callback 36.1.
- [ParcelFileDescriptor](https://developer.android.com/reference/android/os/ParcelFileDescriptor): dup y propiedad del descriptor.
- [AutoCloseInputStream](https://developer.android.com/reference/android/os/ParcelFileDescriptor.AutoCloseInputStream): cierre del ParcelFileDescriptor asociado.

Proyecto creado y dirigido por @Lukhou23; créditos originales conservados. PR #6 debe permanecer abierto y sin fusionar.
