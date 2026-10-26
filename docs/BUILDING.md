# Compilar Connected Alpha

Estas instrucciones corresponden a Alpha1274, PR95, HEAD `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. Alpha1275 evoluciona por separado: revisa su workflow antes de cambiar de base. El README histórico de Exteraless y `tools/connected_alpha/cloud-build.md` describen etapas anteriores; sus instrucciones sobre debug, AGE o entrega de artefactos no representan el procedimiento actual.

## Fuentes y entorno real

```sh
git clone https://github.com/Jose22Yt/FlexyGram.git
cd FlexyGram
git checkout 8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881
git submodule update --init --recursive --depth=1
```

No uses `--remote` ni actualices dependencias/submódulos durante una reproducción. El commit y sus gitlinks forman parte de la versión.

| Componente | Configuración conservada |
| --- | --- |
| Java | JDK21; el workflow adapta el criterio de vendor a Temurin solo en su checkout efímero |
| Gradle / AGP | wrapper9.7.1 / plugin Android9.3.1, fijados en fuentes |
| Android | compileSdk37, targetSdk36, minSdk24; compilar con API37 no prueba ejecución en Android17 |
| Herramientas | build-tools36.0.0, NDK27.2.12479018, CMake3.31.6 |
| Python | Chaquopy17.0.0 y sus fuentes/wheels fijados; Python de construcción3.11 en CI |
| ABI de la Alpha | `NATIVE_TARGET=arm64-v8a` |

El workflow es la referencia ejecutable para paquetes de sistema, reconstrucción de wheels, límites de disco y preparación de entradas: [.github/workflows/connected-alpha-arm64.yml](../.github/workflows/connected-alpha-arm64.yml). No omitas JNI/Chaquopy ni validaciones para llamar exitosa una compilación incompleta.

## Entradas privadas

La compilación oficial usa ocho entradas existentes mediante mecanismos privados autorizados: `TELEGRAM_APP_ID`, `TELEGRAM_APP_HASH`, `ALPHA_STORE_PASSWORD`, `ALPHA_KEY_ALIAS`, `ALPHA_KEY_PASSWORD`, `ALPHA_FIREBASE_JSON_B64`, `ALPHA_KEYSTORE_B64`, `ALPHA_CERTIFICATE_SHA256`.

Obtén una aplicación propia en [my.telegram.org](https://my.telegram.org). No reutilices API ID/hash de otros clientes ni valores de ejemplo. Firebase debe coincidir con `io.github.jose22yt.flexygram.alpha`. Base64 no es cifrado. No incluyas valores privados en Git, logs o conversaciones. No generes otra firma para actualizar una instalación oficial; una firma distinta no es compatible con sus datos existentes.

## Ruta local autorizada

El ejecutor actual [build_private_apk.py](../tools/connected_alpha/build_private_apk.py) valida el certificado autorizado, exige entradas fuera del checkout con modo0600, comprueba submódulos/wheelhouse, enmascara el log y limpia material temporal. Consulta `--help` antes de usarlo:

```sh
python3 tools/connected_alpha/build_private_apk.py --help
python3 tools/connected_alpha/build_private_apk.py   --inputs /ruta/privada/entradas.json   --sdk-root /ruta/android-sdk --jdk-root /ruta/jdk21   --python /ruta/python3.11 --wheelhouse /ruta/wheels-verificados   --out /ruta/privada/salida
```

Las rutas son referencias, no credenciales de sustitución. La preparación del wheelhouse está implementada en `rebuild_python_wheels.py` y en el workflow; conserva su provenance. El ejecutor termina invocando la tarea real:

```sh
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleConnectedAlpha --no-daemon --console=plain --max-workers=2
```

La tarea por sí sola no sustituye la preparación privada. No hay promesa de fallback debug en Connected Alpha. El ejecutor y verificador de esta base esperan versionCode1274; no cambies números para saltar controles. Los mantenedores coordinan cada nueva versión con Work1.

## Validación y entrega

```sh
python3 -m pip install -r tools/connected_alpha/requirements-ci.txt
python3 tools/connected_alpha/run_checks.py
python3 tools/connected_alpha/check_resources.py --sdk-root "$ANDROID_HOME"
```

AAPT2 y los ensayos aislados no equivalen al manifest combinado ni a compilar la aplicación completa. `verify_apk.py` comprueba paquete, versión, firma V2, certificado, ZIP/zipalign, JNI y los ELF empaquetados, incluidos los archivos nativos anidados. Una APK aprobada está vinculada a su propio SHA256 y HEAD; una reconstrucción puede producir otro hash.

La entrega vigente es **APK nativa firmada privada, sin AGE ni instalador auxiliar**. El workflow público de esta base no publica esa APK: la verifica y después limpia su checkout; sus artefactos son evidencia de pruebas. Solo el destino privado autorizado por el propietario puede usarse para entregar el binario. No publiques una release o un artefacto de APK en el repositorio público. Esta auditoría no cambia ni ejecuta el proceso privado de entrega.
