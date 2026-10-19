# FlexyGram 1.0 — prueba segura del Paso 3 en el Poco X8 Pro

Esta guía no acredita que se haya instalado ni arrancado la APK en el teléfono. La compilación y el análisis estático no sustituyen esas pruebas. No introducir cuentas personales ni credenciales en esta referencia Debug. Para el primer arranque sin autenticar servicios, usar modo avión. La base conserva la configuración heredada; una configuración definitiva de servicios requiere un trabajo controlado posterior.

## 1. Evitar pérdida de datos y conflictos

El identificador sigue siendo `com.exteraless.app` y la etiqueta visible puede ser `exteraless`. Si ya tienes Exteraless, DETENTE antes de instalar. La firma Debug de esta reconstrucción puede diferir de cualquier instalación previa, incluso de otro Debug.

No desinstales, borres almacenamiento, fuerces una sustitución ni aceptes un downgrade para hacer pasar la prueba. Desinstalar puede eliminar sesiones, ajustes, plugins, archivos privados y chats secretos locales; que algunos chats estén en la nube no garantiza recuperar todos los datos. Un respaldo genérico de Android tampoco garantiza recuperarlos. La alternativa segura es un dispositivo Android ARM64 separado y vacío o un emulador compatible limpio. Una variante con otro identificador requiere revisar servicios y una modificación explícita posterior: esta referencia no lo cambia. Otro perfil de usuario no garantiza evitar un conflicto de firma, porque Android comparte la identidad del paquete entre usuarios.

Con un ordenador propio y ADB autorizado, comprobar primero:

```sh
adb devices -l
adb shell pm path com.exteraless.app
```

Si devuelve una ruta APK, ya existe el paquete: no continuar con la instalación sobre ese teléfono. Si no devuelve nada, comprobar también visualmente que no haya una instalación existente o una política de administración que impida verla.

## 2. Identidad del archivo y del dispositivo

Comparar el SHA-256 con el de `SHA256SUMS.txt` y el informe de esta entrega. En Linux usar `sha256sum`, en macOS `shasum -a 256` y en PowerShell `Get-FileHash -Algorithm SHA256`. No usar el hash antiguo para validar una reconstrucción nueva.

Leer el dispositivo real:

```sh
adb shell getprop ro.product.model
adb shell getprop ro.build.version.release
adb shell getprop ro.build.version.sdk
adb shell getprop ro.product.cpu.abilist
adb shell getconf PAGE_SIZE
```

Registrar HyperOS desde Ajustes. Una respuesta `4096` significa páginas de 4 KB; `16384`, de 16 KB. El modelo o la cantidad de RAM no prueban el tamaño de página. En 16 KB esta base tiene incompatibilidades ELF documentadas; un posible modo de compatibilidad del sistema no equivale a soporte nativo completo. No cambiar opciones del sistema para ocultar el resultado.

## 3. Instalar solamente en un entorno vacío

Después de verificar el hash y la ausencia del paquete:

```sh
adb install --no-streaming FlexyGram-1.0-Clean-Baseline-arm64-debug.apk
```

No añadir `-r`, `-d`, `-g` ni opciones para eludir comprobaciones. Si falla, guardar el mensaje exacto y detenerse. En instalación manual desde el administrador de archivos, permitir temporalmente la instalación a esa fuente y retirarle después ese permiso. Si Android informa de conflicto de paquete o firma, cancelar; no desinstalar para resolverlo.

## 4. Primer arranque y logs

Usar modo avión y abrir desde el icono, sin introducir teléfono, contraseñas, códigos ni API Hash. La pantalla inicial de acceso no equivale a la lista principal de chats ni valida conectividad. Esperar al menos un minuto y comprobar que no haya cierre inmediato, pantalla congelada o reinicios.

En un ordenador propio, iniciar antes del arranque una captura local y detenerla con Ctrl+C al terminar:

```sh
adb logcat -v threadtime > flexygram-first-start-local.log
```

Ese archivo puede incluir mensajes de todo el dispositivo. No publicarlo completo: conservarlo en privado y compartir únicamente extractos revisados de `com.exteraless.app`, AndroidRuntime, linker, Chaquopy/Python y errores relevantes, sin tokens, identificadores ni contenido personal. No es necesario borrar el buffer general de Logcat.

Una apertura correcta no prueba que Python ni sus dependencias se hayan cargado. Se requieren evidencia de inicialización del motor, imports controlados y ejercicio de JNI/Python. No instalar plugins desconocidos para provocar esas rutas. La lista de chats solo se puede validar posteriormente en un entorno autorizado con una cuenta de prueba propia y servicios propios preparados de forma privada.

## Pendientes exclusivos de Android físico o emulado compatible

- Modelo, Android/API, HyperOS, ABI y tamaño de página reales.
- Ausencia de conflicto de package/firma y resultado exacto de instalación.
- Primer arranque, permanencia sin cierre, pantalla alcanzada y Logcat depurado.
- Carga efectiva de JNI y del runtime Python personalizado; imports de dependencias nativas afectadas.
- Comportamiento de las cuatro bibliotecas de 4 KB y de los segmentos RELRO bajo el linker real; registrar si hay compatibilidad de 16 KB del sistema.
- Acceso a pantalla principal con cuenta de prueba propia, solo tras configurar servicios propios de forma privada.

Un único dispositivo de 4 KB no certifica soporte de 16 KB; un dispositivo de 16 KB tampoco sustituye pruebas separadas en 4 KB. No se medirán ni declararán mejoras de rendimiento en este paso.
