# Compilación de la beta ARM64

Se inició la compilación real de `:TMessagesProj:assembleDebug`, con `NATIVE_TARGET=arm64-v8a`. Todavía no hay una APK terminada ni validación en un teléfono.

## Entorno y Java

La descarga del proveedor Java JetBrains está bloqueada por HTTP 403 en la red del entorno. Para avanzar se instaló un JDK 21 completo de Debian en `/workspace/.flexygram/jdk21`, verificando el SHA-256 del paquete contra el índice HTTPS oficial. Gradle logró configurar el proyecto y compilar `buildSrc` y módulos multimedia con este JDK.

La restricción de proveedor del daemon se retira únicamente durante el comando local y se restaura al salir. El archivo versionado `gradle/gradle-daemon-jvm.properties` debe quedar sin cambios después de finalizar cada intento. No se modificó la versión Java 21 requerida por la aplicación.

Ayudante local: `/workspace/.flexygram/build-beta.sh`. Usa el SDK/NDK preparados y restaura automáticamente el criterio del daemon. Invocación de la APK completa:

```bash
/workspace/.flexygram/build-beta.sh \
  --init-script /workspace/.flexygram/native-pools.gradle \
  :TMessagesProj:assembleDebug
```

El init script limita compilación nativa a cuatro trabajos y enlace a uno, para no agotar los recursos de esta máquina.

## Bloqueos confirmados

1. `:TMessagesProj:installDebugPythonRequirements`: la descarga de paquetes Python Android desde `chaquo.com` devuelve HTTP 403.
2. Se intentó comprobar Java independientemente con `compileDebugJavaWithJavac`, excluyendo únicamente la instalación Python en ese intento diagnóstico. La resolución de `com.aliucord:Aliuhook:1.1.4` desde `maven.aliucord.com` también devuelve HTTP 403. No se ha validado aún la compilación de todo el código de la aplicación.

Se guardó el borrador de red con `api.foojay.io`, `maven.aliucord.com` y `chaquo.com`, preservando el preset de registros de paquetes. El borrador guardado no aplica esos permisos a la instancia actual. Deben revisarse y guardarse en la configuración del entorno y publicarse según lo solicite la interfaz. Después hay que repetir las solicitudes afectadas y la compilación completa. El ayudante local permite continuar con Java Debian sin depender de Foojay.

No se sustituyeron dependencias por simulaciones ni se desactivaron las funciones Python/plugins para producir una APK incompleta.

## Corrección y pruebas

Se corrigieron dos simulaciones en `tests/test_reflection_gate.py`: ahora exponen `get_reflection_policy`, igual que la API utilizada por el cargador. La prueba de instalación conserva el estado y comprueba que una segunda llamada no vuelve a instalar la misma política. Se mantiene la comprobación del error al fallar la instalación.

Resultado de la suite Python completa: **148 aprobadas, 31 omitidas, cero fallos**. Las omisiones corresponden al corpus externo y artefactos de análisis no disponibles. Este resultado no sustituye una compilación Android ni una prueba visual.

Se ejecutó por separado `:TMessagesProj:externalNativeBuildDebug` para validar y preparar C/C++ sin esperar a los dos dominios bloqueados. Terminó con **BUILD SUCCESSFUL** en 6 min 37 s, 29 tareas (3 ejecutadas y 26 actualizadas). Generó `TMessagesProj/build/intermediates/cxx/Debug/4p4gjk21/obj/arm64-v8a/libtmessages.49.so`, de aproximadamente 371 MiB con símbolos de depuración. Esto valida la biblioteca nativa principal ARM64, no una APK completa ni la ejecución en Android.

Al finalizar se restauró el criterio Java del daemon y `git diff --check` quedó correcto. Los cambios necesarios de red y las instrucciones de inicio actualizadas están guardados en el borrador del entorno. La herramienta solicita revisión, guardado y publicación por el usuario; no se ha afirmado que esa publicación o aplicación de red se haya realizado.
