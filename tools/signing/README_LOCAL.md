# Custodia de la firma oficial en tu dispositivo

Este paquete contiene herramientas, guía y el certificado público oficial. **No contiene una clave privada, una contraseña ni una APK.** La identidad oficial ya fue generada por el propietario y su certificado público está registrado. Esta versión NO genera claves: verifica y respalda únicamente el PKCS12 oficial existente.

## Inicio en Android con Termux

1. Usa Termux de una fuente oficial: https://github.com/termux/termux-app#installation. Si ya lo tienes, conserva su instalación y sus datos; no desinstales para cambiar de fuente. Necesitas además un gestor de contraseñas con recuperación y dos soportes de backup independientes.
2. Instala las herramientas desde Termux:

```bash
pkg update
pkg install python openjdk-21 age unzip
termux-setup-storage
```

La última orden solicita acceso al almacenamiento compartido para leer el ZIP y mover **backups cifrados**. El PKCS12 original se guarda en el área privada de Termux, no en Descargas. Esta es una ruta prevista para Android; no ha sido probada físicamente en el Poco X8 Pro.

3. Si descargaste `FlexyGram_Firma_Local.zip` en Descargas, cópialo a tu directorio privado y extrae allí sus herramientas:

```bash
cp ~/storage/downloads/FlexyGram_Firma_Local.zip ~/
cd ~
unzip FlexyGram_Firma_Local.zip
cd FlexyGram_Firma_Local
python owner_wizard.py
```

Si trabajas desde el repositorio, ejecuta `python3 tools/signing/owner_wizard.py`. No necesitas descargar todo el repositorio cuando usas el paquete pequeño. En Linux/macOS instala Python 3.10+, JDK 17+ y age oficial por los métodos de tu sistema, extrae el paquete y usa la misma orden. El proyecto Android usará JDK 21 en su futura compilación. La herramienta requiere una terminal POSIX propia y rechaza CI o el entorno del asistente.

## Qué te pedirá

- Dos rutas de archivos `.age` en carpetas accesibles distintas para los backups A y B. Ejemplo: una unidad externa y otro soporte independiente. Las carpetas deben existir; el nombre completo termina en `.age`.
- La contraseña actual de tu PKCS12 oficial, de **32 caracteres o más**, conservada en tu gestor; no inventes una contraseña nueva para abrir el almacén existente. Se pide sin mostrarla y sin ponerla en argumentos.
- Tener el PKCS12 oficial existente en `~/FlexyGramSigning/flexygram-release.p12`. Si falta, recupera el original; no se genera otro.
- Contraseñas fuertes para los backups cuando age las solicite, diferentes de la del PKCS12. Guárdalas en el gestor con recuperación independiente del teléfono. No dejes sin registrar ninguna frase generada por age.
- Descifrar A y B para comprobar recuperación. Se compara cada archivo recuperado con el original y se prueba la posesión de la misma clave privada. Las copias temporales se mantienen en la carpeta privada y se retiran después; borrar un archivo no garantiza borrado físico en flash.
- Escribir `CONFIRMO` únicamente cuando los dos backups estén en soportes independientes y puedas recuperar sus contraseñas sin depender solo del teléfono original.

El programa no puede demostrar físicamente dónde están tus soportes: esa confirmación es tuya. Dos carpetas de un teléfono no cumplen la condición. Si necesitas trasladar los `.age` con el gestor de archivos a una nube privada u otro soporte, **no confirmes todavía**. Mueve solo los archivos cifrados, comprueba que están allí, recupera cada uno desde su destino a carpetas distintas accesibles y vuelve a ejecutar el asistente indicando los archivos recuperados. Si ya existen, no los sobrescribe: solo comprueba que recuperan exactamente el original. La confirmación final se refiere a las copias conservadas fuera del teléfono, no a los archivos temporales descargados para verificarlas.

Nunca importes una clave diferente para resolver un fallo. El certificado público está incluido para comprobación.

No se requieren claves de Telegram, Firebase ni secretos de GitHub para este proceso. El asistente no hace conexiones de red ni configura Actions. La instalación de herramientas sí usa la red.

## Si se corta o falla

El original está en `~/FlexyGramSigning/flexygram-release.p12`. **No desinstales Termux, no borres sus datos ni elimines esa carpeta.** Vuelve a ejecutar el asistente: si existe el almacén, lo verifica y no genera otra clave. Un backup existente tampoco se reemplaza. Usa siempre la misma contraseña PKCS12.

Si existe una huella fijada y falta el almacén, el asistente se detiene: debes recuperar el original desde un backup, no crear otra identidad. Si una generación empezó pero no dejó un archivo válido, también se detiene para revisión manual. Un bloqueo `.owner-custody.lock` puede quedar tras un apagado brusco: no lo retires hasta confirmar que no queda otra ejecución activa. No ejecutes dos asistentes a la vez.

Para consultar el estado sin abrir la clave:

```bash
python owner_wizard.py --status
```

El estado `OWNER_ATTESTED_AFTER_TWO_RESTORES` significa que se verificaron dos restauraciones y tú confirmaste su custodia independiente. El informe lleva fecha; no garantiza disponibilidad futura de los soportes. Repite las comprobaciones tras cambios de dispositivo o almacenamiento.

## Qué compartir después

Solo estos dos archivos públicos de `~/FlexyGramSigning/`:

- `flexygram-release.cer`: certificado público DER, sin clave privada.
- `public-verification.json`: huella y resultado público sin contraseñas ni rutas de backups.

Nunca compartas el `.p12`, los backups `.age`, `custody-state.json` o las contraseñas. La SHA-256 registrada es `5a598fb5ba42949b67b7c2635106fafd5f23179397e4c098757a73cd2d2ef66c`. Las dos copias independientes siguen pendientes de confirmación al proyecto.

## Protecciones y límites

Alias `flexygram-release`, PKCS12, RSA-3072, certificado autofirmado SHA256withRSA y CN `FlexyGram Release Key`. Se rechaza la identidad Alpha conocida/debug y se fija la huella tras la primera inspección. El programa no regenera automáticamente, no publica y no procesa APK/AAB.

La contraseña se transmite a keytool y al verificador únicamente en el entorno de su proceso hijo, nunca en argumentos, archivos de configuración ni informes. Esto evita exponerla en el historial normal de órdenes; no protege frente a otro proceso malicioso con acceso a tu usuario, root o memoria. Python/JVM no garantizan eliminar todas las copias de contraseñas en memoria. Usa un dispositivo confiable con cifrado, sin grabación de pantalla/terminal. Una carpeta con permisos privados no sustituye el cifrado del dispositivo.

Pruebas del paquete: `python -m unittest discover -s . -p 'test_owner_wizard.py' -v` (herramientas criptográficas simuladas; no genera claves) y `python check_verifier.py` (compila el verificador Java y rechaza entradas inválidas). La generación fue confirmada por el propietario. La recuperación real de dos backups sigue pendiente de confirmación; las pruebas simuladas del código no la sustituyen.

Referencias oficiales: JDK keytool https://docs.oracle.com/en/java/javase/21/docs/specs/man/keytool.html; age https://github.com/FiloSottile/age; paquetes Termux https://github.com/termux/termux-packages.
