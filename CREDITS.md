# Créditos y avisos

FlexyGram es un proyecto creado y dirigido por [@Lukhou23](https://t.me/Lukhou23), con el repositorio mantenido por [Jose22Yt](https://github.com/Jose22Yt). Estos roles corresponden al proyecto FlexyGram y no sustituyen la autoría de sus componentes.

**Asistencia de desarrollo:** Codex, como herramienta de apoyo en implementación, revisión y pruebas bajo la dirección del responsable de FlexyGram.

## Código y proyectos de origen

| Proyecto | Aportación / procedencia |
| --- | --- |
| [Telegram para Android](https://github.com/DrKLO/Telegram) | Base de mensajería y numerosos componentes Android y nativos. Se conservan los avisos de sus autores, incluidos los de Nikolai Kudashov. |
| [Exteraless](https://github.com/exteraless/exteraless) | Base directa del repositorio; origen registrado en `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`. |
| [NagramX](https://github.com/risin42/NagramX) | Base declarada por el proyecto de origen y componentes reconocidos en sus fuentes. |
| [exteraGram](https://github.com/exteraSquad/exteraGram) | Funciones, diseños y recursos acreditados por el proyecto de origen. |
| [Nagram](https://github.com/NextAlone/Nagram) y [Nekogram](https://github.com/Nekogram/Nekogram) | Componentes, opciones y utilidades que mantienen sus namespaces y avisos de origen. |

También se conservan los reconocimientos heredados a [AyuGram](https://github.com/AyuGram/AyuGram4A), [Cherrygram](https://github.com/arsLan4k1390/Cherrygram), [Dr4iv3rNope](https://github.com/Dr4iv3rNope/NotSoAndroidAyuGram), [Inugram](https://github.com/teidesu/inugram) y [OctoGram](https://github.com/OctoGramApp/OctoGram). Un reconocimiento no implica incorporar todo el código de un proyecto.

## Diseño y recursos visuales

- **Diseño e iconos heredados de exteraGram:** [@the8055u](https://t.me/the8055u) y el estudio [@BlueprintDsgn](https://t.me/BlueprintDsgn). Sus derechos y avisos se conservan.
- **Solar Icons:** [480 Design / @Design480](https://github.com/480-Design/Solar-Icon-Set). Las cadenas de atribución y conversiones se encuentran en `strings_nax.xml`, `SolarIcons.kt` y los recursos con sufijo `_solar`.
- **Remix Icon:** [Remix Design / @Remixicon](https://github.com/Remix-Design/RemixIcon). Acreditados en `strings_nax.xml` y las conversiones de iconos; los recursos con sufijo `_remix` conservan su procedencia. Debe respetarse la licencia de la versión concreta incorporada, que puede diferir de la versión actual del proyecto.
- **Icono de FlexyGram en esta portada:** el mismo recurso de identidad que utiliza la línea beta del proyecto. No se presenta como un recurso nuevo ni se atribuye su autoría a otra persona. Las marcas y elementos de terceros mantienen los derechos que les correspondan.

No se deben sustituir licencias ausentes por una licencia supuesta. Antes de distribuir un conjunto de recursos heredados, hay que comprobar su revisión de origen y conservar los avisos exigidos. El crédito de una imagen no equivale por sí solo a un permiso de uso.

## Efectos de borrado

Las mallas, curvas y fórmulas de renderizado de fractura, caída, vórtice y TNT se
adaptan de **Bubble Fracture v1.0**, de [@larrat23](https://t.me/larrat23), a partir
del archivo proporcionado para esta integración. Se conservan los valores
predeterminados del efecto. La integración nativa, el ciclo de vida y el selector
son propios de FlexyGram; no se incorpora el cargador DEX ni los hooks del plugin.
El archivo recibido no declara una licencia específica: esta atribución no
sustituye los derechos ni supone una licencia nueva para sus fuentes originales.

## Bibliotecas y componentes

Los manifiestos técnicos son la referencia de las dependencias y revisiones de cada rama:

- [`.gitmodules`](.gitmodules): libvpx, dav1d, FFmpeg, Ogg, Opus, opusfile, jlatexmath, tlottie, módulos multimedia, Abseil, WAMR, tgcalls, wallet-engine, Boost.Regex, libprisma y Chaquopy.
- [`TMessagesProj/build.gradle`](TMessagesProj/build.gradle): AndroidX, Material Components, ZXing, AndroidSVG, nv-websocket-client, Vosk, Firebase, Google Play services/ML Kit, Gson, Guava, mp4parser, Markwon, Stripe, Billing, coroutines, osmdroid, OkHttp, dnsjava, TrueTypeParser, UnifiedPush, Room, Commons Text, el traductor de Nekogram, Aliuhook, MVEL, DexMaker y HiddenApiBypass, entre otros.
- [`TMessagesProj/jni`](TMessagesProj/jni): componentes nativos y sus avisos, incluidos BoringSSL, WebRTC, SQLite y FFmpeg.
- `TMessagesProj/libs/glyph-matrix-sdk-2.0.aar`: SDK de terceros; su licencia y condiciones de redistribución deben comprobarse con su proveedor antes de distribuir una entrega que lo incluya.

Este índice no sustituye los archivos `LICENSE`, `COPYING`, `NOTICE` ni los encabezados de cada componente; tampoco es un inventario jurídico exhaustivo de las dependencias transitivas. Las versiones y componentes pueden variar entre ramas.

## Licencia y contribuciones

El repositorio mantiene [GNU GPL versión 3](LICENSE). Los avisos específicos de los archivos y componentes de terceros siguen siendo aplicables, incluidos los encabezados GPL v2 o posterior que existan en el código de origen.

La autoría de las contribuciones permanece en el historial Git. Los nuevos componentes deben registrar fuente, revisión y licencia, además de incluir los avisos que correspondan en la distribución.

## Iconos originales de Telegram para iOS (beta 41)

Dibujos importados de [TelegramMessenger/Telegram-iOS](https://github.com/TelegramMessenger/Telegram-iOS/tree/24638bc69bd083981b178dd1e7f921eebbf7fc46), revisión `24638bc69bd083981b178dd1e7f921eebbf7fc46`. Se conservan archivos fuente y metadatos originales con SHA-256 y Git blob, junto al [README original](tools/ios_originals/UPSTREAM-README.md). La conversión a recursos Android conserva las geometrías o rasteriza el archivo original; no procede de Flutter Cupertino, SF Symbols recreados ni generación de imágenes.

El [informe de importación](docs/icons/beta41-original-ios.md) detalla formatos, tamaños, roles y excepciones. Estos recursos no cambian el nombre ni el logotipo de FlexyGram. La revisión original no incluye un archivo LICENSE en la raíz; se mantiene su README y no se atribuye a Telegram una licencia nueva a través de esta conversión.
