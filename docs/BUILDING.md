# Compilar FlexyGram

Esta guía prepara una compilación futura. **La misión de identidad no autoriza ejecutar los comandos de compilación que aparecen aquí.** No se ha compilado ni firmado la nueva Beta.

## Fuentes y herramientas

```bash
git clone https://github.com/Jose22Yt/FlexyGram.git
cd FlexyGram
git switch feat/official-identity-beta-preparation
git submodule update --init --recursive
```

Fija el commit aprobado antes de compilar. Esta rama deriva de `feat/signature-interaction-navigation-2`, SHA `258dd3590f40ca0083a4b7bad6b413433c4e2c14`. Su PR debe revisarse sobre esa base; no incorpora otros candidatos ni reemplaza Exteraless desde cero.

| Herramienta | Configuración del repositorio |
| --- | --- |
| JDK | 21 |
| Gradle / AGP | wrapper 9.7.1 / 9.3.1 |
| Android SDK | compile 37, target 36, mínimo 24 |
| Build Tools | 36.0.0 |
| NDK | 27.2.12479018 |
| CMake | 3.31.6 o compatible con la restricción del proyecto |
| Python / Chaquopy | 3.11 / 17.0.0 |
| ABI de entrega | arm64-v8a |

Instala también las dependencias exigidas por los submódulos y scripts nativos. Consulta sus instrucciones originales. No uses `NATIVE_TARGET=SKIP`: omitiría JNI y pruebas. x86_64 no sirve como validación del payload ARM64.

## Entradas privadas

Configura `sdk.dir`, `TELEGRAM_APP_ID` y `TELEGRAM_APP_HASH` propios en `local.properties` (ignorado), o las variables admitidas. Obtén las credenciales en https://my.telegram.org; no reutilices muestras ni claves ajenas.

Para Beta proporciona `TMessagesProj/src/beta/google-services.json` de una aplicación Firebase registrada como `com.flexygram.messenger` y todas las entradas de [SIGNING.md](SIGNING.md). No se crea ni activa un servicio externo durante esta misión. Si se desea autenticación Google, configura `FLEXYGRAM_GOOGLE_AUTH_CLIENT_ID` para Beta; nunca se hereda automáticamente el cliente OAuth de Alpha. Maps y Glyph requieren claves propias y restricciones de paquete/certificado cuando correspondan. La ausencia de estas credenciales limita sus funciones.

Para Alpha se conservan el JSON de `src/connectedAlpha`, la clave `config/connected-alpha-test.keystore` y las entradas `ALPHA_*`. El constructor privado y los verificadores de `tools/connected_alpha` siguen siendo **exclusivos de Alpha**, no sirven para entregar ni certificar una Beta.

## Solo después de autorizar la compilación

```bash
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:validateFlexyGramBetaConfiguration
NATIVE_TARGET=arm64-v8a ./gradlew :TMessagesProj:assembleBeta
```

La primera orden inspecciona configuración y certificado; no prueba una APK. La segunda compila JNI/Chaquopy y la aplicación completa. El artefacto futuro estará bajo `TMessagesProj/build/outputs/apk/beta/`, con prefijo `FlexyGram-Beta`. `connectedAlpha` mantiene su identidad y prefijo `FlexyGram-Alpha`. `debug`, `staging` y `release` no están habilitadas como variantes de entrega en esta base.

Antes de distribuir: verificar manifiesto combinado, DEX, recursos, firma y certificado con herramientas Android; comprobar los ELF ARM64 y alineación de 16 KB; instalar en dispositivo físico y probar login, contactos, compartir, notificaciones, enlaces y actualizaciones. No basta con cambiar el paquete esperado en el verificador Alpha: hace falta revisar el contrato completo de entrega Beta.

## Actions

El PR de identidad usa únicamente `tools/identity/check_identity.py`, sin Gradle ni Android SDK. Se omiten en esta rama los dos jobs generales de PR que incluyen herramientas Android. Los workflows de entrega Alpha conservan sus restricciones de ramas y no se disparan por esta rama. Los workflows heredados `release`, `canary` y `staging` no son una ruta de publicación Beta y no deben usarse para ella. No se ha añadido ni despachado un pipeline de empaquetado o publicación Beta.
