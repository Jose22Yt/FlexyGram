# realAlpha offline + login: gate conjunto de fuentes

Rama apilada sobre PR #49. Este control **no** modifica la interfaz, los permisos,
la identidad, las credenciales ni las versiones Android. No firma ni instala nada.

## Ejecución en checkout completo (Python 3.11)

Primero ejecutar la nueva comprobación *solo de fuentes*, que es de lectura:

```sh
python3.11 tools/real_alpha_integration/check_combined.py --static
python3.11 -m unittest discover -s tests/real_alpha_integration -v
python3.11 -O -m unittest discover -s tests/real_alpha_integration -v
```

Después preparar ambas copias Java generadas **sin modificar** los originales;
el comando aborta ante hashes alterados, rutas sospechosas o fuentes inesperadas:

```sh
python3.11 tools/real_alpha_integration/check_combined.py --prepare
python3.11 tools/real_alpha_integration/check_combined.py --check
```

Solo con los SDK, submódulos y dependencias verificadas disponibles:

```sh
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleRealAlphaDebug \
  -PflexygramRealAlpha=true \
  -PflexygramLocalLoginPages=true \
  -PflexygramOfflineDialogsUi=true --no-daemon
```

La comprobación cubre **7 fuentes originales + 7 copias Java generadas**,
hashes de los parches, selección Gradle, ausencia de clases duplicadas entre
ambos overlays y negación de variantes distintas de realAlphaDebug.
No intenta sustituir una compilación Gradle/AGP ni prueba JNI, Chaquopy,
recursos Android, rendimiento o navegación real. El indicador
`android_compiled=false` nunca debe interpretarse como un build aprobado.

## Alcance y entrega

- Mantener PR #42, #43, #44 y #49 sin fusionar y conservar la APK estable.
- Si falla `--prepare`, no cambiar hashes ni omitir el verificador: investigar
  primero si cambió el original o el parche.
- Para Android, verificar además JDK 21, SDK 37, NDK 27.2.12479018,
  CMake 3.31.6, módulos nativos, Chaquopy y la política sin INTERNET.
- Una salida estática satisfactoria solo permite **intentar** el build unsigned.
  Registrar el resultado real, la evidencia del empaquetado y sus hashes
  antes de solicitar permiso para cualquier firma o instalación.
