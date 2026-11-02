# FlexyGram 1.0

Proyecto Android con identidad y dirección de desarrollo propias, basado en [Exteraless](https://github.com/exteraless/exteraless).

- **Creador y responsable de FlexyGram:** [@Lukhou23](https://t.me/Lukhou23).
- **Cuenta GitHub propietaria:** [Jose22Yt](https://github.com/Jose22Yt).
- **Repositorio oficial:** [Jose22Yt/FlexyGram](https://github.com/Jose22Yt/FlexyGram).
- **Estado:** PASO 1 — creación y configuración del repositorio. No hay todavía una versión 1.0 compilada ni cambios funcionales propios.

## Identidad, autoría y licencia

@Lukhou23 es el creador y responsable del proyecto FlexyGram y de su dirección de desarrollo. Esto no atribuye a FlexyGram ni a su creador la autoría del código, diseños o recursos heredados.

La base procede de Exteraless y de sus proyectos de origen, incluidos Telegram, NagramX y exteraGram. El historial Git y los avisos de autoría y copyright se conservan. El archivo [LICENSE](LICENSE) mantiene la **GNU GPL versión 3 (GPL-3.0)**; las licencias y avisos específicos de componentes y recursos continúan aplicándose.

Se conserva íntegra, más abajo, la documentación original de Exteraless, incluidos sus créditos, enlaces e información técnica. En particular, el diseño y los iconos heredados de exteraGram mantienen los créditos a **@the8055u** y **@BlueprintDsgn**, y los derechos de sus autores.

## Prioridades permanentes

1. Estabilidad.
2. Velocidad de respuesta táctil.
3. Fluidez de navegación.
4. Rendimiento eficiente.
5. Funciones y diseño propios sin sacrificar las prioridades anteriores.

El objetivo futuro es conservar la capacidad de respuesta de Exteraless original mientras se desarrollan funciones propias. Son objetivos del proyecto, no mejoras ya implementadas ni resultados medidos.

## Origen registrado

| Dato | Valor |
| --- | --- |
| Repositorio de origen | https://github.com/exteraless/exteraless |
| Rama de origen | `main` |
| Commit completo de origen | `1ad6a60a6834ffca722b1a22f4fba27ecb29a061` |
| Árbol Git original | `c3f2721f7c29e4c99e1cd30a27343cb3dd986808` |
| Fecha de creación del fork | 2026-10-18 |
| Relación con upstream | Fork nativo de GitHub; historial conservado |

[Consultar el commit original](https://github.com/exteraless/exteraless/commit/1ad6a60a6834ffca722b1a22f4fba27ecb29a061).

## Ramas y alcance del PASO 1

- `main`: rama predeterminada. Código original sin modificaciones funcionales; la única modificación inicial es este README.
- `develop`: rama destinada al futuro desarrollo, creada desde el estado documentado de `main`.
- Los futuros cambios se propondrán en ramas específicas y se revisarán mediante pull requests antes de integrarlos.
- No se han implementado optimizaciones, modificado la interfaz, descargado dependencias de compilación ni generado APK.

**GitHub Actions está desactivado en la configuración del repositorio.** Los workflows heredados se conservan sin cambios y quedan pendientes de auditoría. Las instrucciones de compilación y CI del texto original se mantienen como referencia histórica de la base; no constituyen autorización para ejecutarlas en esta etapa.

## Sincronización futura con Exteraless

Procedimiento documentado para una etapa posterior; no ejecutado en el PASO 1:

1. En una copia local del repositorio, comprobar los remotos con `git remote -v`. `origin` debe apuntar a `https://github.com/Jose22Yt/FlexyGram.git`.
2. Añadir una sola vez el remoto de origen, si aún no existe:

   ```bash
   git remote add upstream https://github.com/exteraless/exteraless.git
   ```

3. Con el árbol de trabajo limpio, obtener las referencias sin descargar submódulos, actualizar `develop` y crear una rama de integración con un nombre de fecha único:

   ```bash
   git fetch --no-recurse-submodules upstream
   git fetch --no-recurse-submodules origin
   git switch develop
   git pull --ff-only --no-recurse-submodules origin develop
   git switch -c sync/exteraless-YYYYMMDD
   git rev-parse upstream/main
   git merge --no-ff --no-commit upstream/main
   ```

4. Registrar el SHA completo obtenido, revisar los cambios y resolver conflictos conservando la identidad FlexyGram, los créditos y licencias. Auditar especialmente workflows, scripts, dependencias y referencias a submódulos antes de autorizar ejecuciones. Si se decide cancelar la integración en curso, usar `git merge --abort`.
5. Tras la revisión y la validación autorizada para esa etapa, crear el commit de integración y un pull request de la rama `sync/...` hacia `develop`. La promoción posterior a `main` requiere su propia revisión.

No usar force-push, reemplazar el historial ni sobrescribir las ramas de FlexyGram con el contenido de upstream. Mantener Actions desactivado hasta completar su auditoría y autorizar su activación.

---

## Documentación original de Exteraless

El contenido siguiente se conserva íntegro desde el commit de origen indicado. Sus nombres, estado beta, enlaces e instrucciones describen Exteraless.

---

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
