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

## Publicación del trabajo y compilación en GitHub

El código se publicó en la rama `codex/flexygram-beta-glass`, a partir de `main`. El primer commit de los cambios de interfaz y cristal es `8d89304ad44c9bc15fcbff5a449328bb9d19a25c`.

Se añadió `.github/workflows/ui-beta-debug.yml`, un flujo de depuración ARM64 que se activa con los pushes a esa rama y admite ejecución manual. Compila el SHA del evento, ejecuta las pruebas, conserva el registro de Gradle y verifica la firma y las bibliotecas nativas de la APK antes de guardarla como artefacto por siete días. Usa firma de depuración, no solicita secretos ni modifica el flujo protegido de beta oficial. No crea releases ni envía mensajes externos.

El flujo se validó con actionlint 1.7.12. La publicación del YAML no demuestra que GitHub Actions esté habilitado ni que la ejecución haya terminado. La API `api.github.com` devuelve Forbidden desde el entorno, por lo que la comprobación del estado remoto queda pendiente hasta disponer de acceso o del resultado mostrado en Actions. La rama publicada permite revisar el código incluso mientras continúa ese bloqueo.


## Corrección de base funcional

La primera rama se creó desde `main`, tal como estaba montado el entorno. Al revisar el flujo oficial se identificó que la app usada por la beta procede de `932c9a6db84fab52ab167d4c8ee70957b3e57223`, con paquete `com.flexygram.messenger`, Signature y sus módulos de navegación/composición. Se integra ese historial en la rama de trabajo; los primeros commits quedan conservados como diagnóstico de la base anterior y no representan una nueva beta oficial.

La integración conserva el sistema original de destinos de la beta y su vista previa, añade los niveles de compactación a `LiquidNavigationConfig` y cambia el gesto a mantener pulsado y arrastrar para intercambiar posiciones. Se retiran las clases de navegación duplicadas de cuatro pestañas creadas en el primer intento. La nueva sección de cristal se registra en Universal mediante `Settings2Policy`, con preferencias independientes, conservando byte por byte `AppearanceConfig` y el contrato de contorno existente.

Los flujos oficiales/protegidos de `main` se conservan. Solo se modifica el flujo independiente de depuración, que compila el commit de la rama de integración, reconstruye las ruedas Python como requiere la fuente oficial y cancela intentos de depuración obsoletos de la misma rama. Esta APK de diagnóstico usa la firma debug; no reemplaza ni publica automáticamente la beta privada firmada.

Validación tras la integración: 186 pruebas Python aprobadas, 31 omitidas. Los resultados de compilación anteriores corresponden a la base inicial; la compilación Android de la integración debe validarse en la nueva ejecución de Actions.
