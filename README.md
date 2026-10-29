<div align="center">
<img src="TMessagesProj/src/beta/res/drawable-nodpi/flexygram_launcher_art.png" width="112" alt="FlexyGram">

# FlexyGram

Tu Telegram, a tu manera.
</div>

Cliente Android independiente basado en Telegram y Exteraless, con interfaz Signature, personalización y herramientas propias. Creado y dirigido por **@Lukhou23**; repositorio administrado por **Jose22Yt**.

## Estado del proyecto

Desarrollo experimental Connected Alpha. Esta rama prepara la identidad de una futura **1.0.0-beta.1**; no constituye una Beta publicada ni validada. Se apoya en Alpha 1286 (PR #130), todavía en borrador y pendiente de aceptación física. Ningún cambio de esta rama promociona automáticamente esos candidatos.

## Interfaz y funciones

- Interfaz Signature: bienvenida, conversaciones, compositor y navegación personalizables.
- Ajustes de burbujas, contornos, transparencias y desenfoque nativo según tema y dispositivo.
- FlexyStudio, reproductor musical y ajustes de apariencia.
- Mensajería, cuentas, llamadas y herramientas compatibles heredadas de Telegram y Exteraless.
- En el candidato Alpha 1286: interacción de burbujas, Liquid Navigation 2.0, Bubble Fusion y presentación opcional de compartir. Su aceptación sigue pendiente.

Los efectos dependen de las opciones activadas y del soporte de Android. Las pruebas aisladas no demuestran fluidez, consumo o estabilidad en un teléfono real. Consulta [funciones y límites](docs/FEATURES.md).

## Android y compilación

La configuración declara **Android 7.0 / API 24 como mínimo**, compileSdk 37 y targetSdk 36. La ruta de entrega actual exige **ARM64-v8a**, con JNI y Chaquopy completos. El mínimo declarado no equivale a compatibilidad física verificada en todos los dispositivos.

[Guía de compilación](docs/BUILDING.md) · [Identidad y migración](docs/ANDROID_IDENTITY.md) · [Firma oficial](docs/SIGNING.md)

| Variante | Identificador | Propósito |
| --- | --- | --- |
| connectedAlpha | `io.github.jose22yt.flexygram.alpha` | Mantener el canal de pruebas existente |
| beta | `com.flexygram.messenger` | Nueva instalación independiente, preparada para validación futura |

## Versiones y participación

No hay una Beta oficial publicada por esta misión. No se activan nuevos canales de descarga ni publicaciones automáticas. Las entregas de prueba requieren el procedimiento privado autorizado del proyecto.

[Repositorio oficial](https://github.com/Jose22Yt/FlexyGram) · [Incidencias](https://github.com/Jose22Yt/FlexyGram/issues) · [Contribuir](CONTRIBUTING.md) · [Cambios](CHANGELOG.md)

No se anuncia un canal de Telegram propio sin verificarlo. [Capturas](docs/screenshots/README.md): espacio reservado para imágenes reales, con datos privados eliminados.

## Créditos y licencia

GNU GPL-3.0: [LICENSE](LICENSE). FlexyGram conserva código y recursos de Telegram, Exteraless, NagramX, exteraGram y otros proyectos. Sus autores mantienen la autoría de sus componentes. Consulta [CREDITS.md](CREDITS.md) para atribuciones y avisos.
