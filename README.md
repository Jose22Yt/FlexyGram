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

<img src="assets/logo.png" width="128" alt="exteraless">

# exteraless

Открытая версия exteraGram — с моделью разрешений для плагинов

[![Канал](https://img.shields.io/badge/Telegram-@exteraless-2CA5E0?logo=telegram&logoColor=white)](https://t.me/exteraless)

</div>

---

## Что это

exteraless — форк [NagramX](https://github.com/risin42/NagramX), в котором возможности
exteraGram реализованы с открытым исходным кодом.

Отдельный упор — **безопасность плагинов**. В exteraGram плагин не ограничен ни в чём;
здесь у него есть модель разрешений: плагин объявляет, что ему нужно, это
видно на экране установки, и получает он только заявленное.

Проект **в бете**: часть возможностей exteraGram ещё не перенесена. Если заметили, что
каких-то функций не хватает, — откройте issue или напишите в [канал](https://t.me/exteraless?direct).

* Имя пакета: `com.exteraless.app`
* Что перенесено: экраны настроек, оформление и параметры чатов, иконпаки, полоса
  пилюль (Pill Stack), боковое меню, движок Python-плагинов

### Ссылки

* Канал: [@exteraless](https://t.me/exteraless)
* Исходники: [github.com/exteraless/exteraless](https://github.com/exteraless/exteraless)

### Сборка

1. Склонировать репозиторий вместе с подмодулями:

    ```bash
    git clone --recursive --shallow-submodules https://github.com/exteraless/exteraless.git exteraless
    ```

    Если репозиторий уже склонирован без подмодулей:

    ```bash
    git submodule update --init --recursive --depth=1
    ```

2. Получить `TELEGRAM_APP_ID` и `TELEGRAM_APP_HASH` на [my.telegram.org](https://my.telegram.org/auth)
   и создать `local.properties` в корне проекта:

   ```properties
   TELEGRAM_APP_ID=<ваш_app_id>
   TELEGRAM_APP_HASH=<ваш_app_hash>
   ```

3. Для подписи APK положить свой `TMessagesProj/release.keystore` и дописать в `local.properties`:

   ```properties
   KEYSTORE_PASS=<пароль_хранилища>
   ALIAS_NAME=<имя_ключа>
   ALIAS_PASS=<пароль_ключа>
   ```

   Ключа в репозитории нет намеренно. Без него сборка не падает — APK подписывается
   отладочным ключом Android.

4. Для push-уведомлений положить свой `TMessagesProj/google-services.json`
   (Firebase, имя пакета `com.exteraless.app`).

5. Заменить метаданные проекта:

    - ключ Google Maps в записи `com.google.android.maps.v2.API_KEY` в `TMessagesProj/src/main/AndroidManifest.xml`;
    - `BaseRemoteHelper.CHANNEL_METADATA_ID` — числовой id вашего канала метаданных, без префикса `-100`.

6. Собрать: `./gradlew :TMessagesProj:assembleDebug` или открыть проект в Android Studio.

**Про ABI.** Собираются только 64-битные `arm64-v8a` и `x86_64`: Chaquopy собирает
Python 3.12 лишь под них, и на `armeabi-v7a` конфигурация обрывается. Переменная
`NATIVE_TARGET` задаёт цель: `arm64-v8a` (один ABI, быстрее), `universal` (оба),
`SKIP` (без нативной части — только Java и ресурсы).

### Сборка через GitHub Actions

Нужны два секрета репозитория:

* `LOCAL_PROPERTIES` — содержимое `local.properties` в base64:

  ```bash
  base64 -w0 local.properties
  ```

* `RELEASE_KEYSTORE` — файл ключа в base64:

  ```bash
  base64 -w0 TMessagesProj/release.keystore
  ```

Дальше запустить workflow **Release Build**. Готовый APK лежит в артефактах прогона.

### Авторы дизайна

Иконки и оформление, унаследованные от exteraGram, созданы его дизайнером —
[@the8055u](https://t.me/the8055u) и студией [@BlueprintDsgn](https://t.me/BlueprintDsgn).
Права на эти материалы принадлежат авторам.

### Благодарности

- [AyuGram](https://github.com/AyuGram/AyuGram4A)
- [Cherrygram](https://github.com/arsLan4k1390/Cherrygram)
- [Dr4iv3rNope](https://github.com/Dr4iv3rNope/NotSoAndroidAyuGram)
- [exteraGram](https://github.com/exteraSquad/exteraGram)
- [Inugram](https://github.com/teidesu/inugram)
- [Nagram](https://github.com/NextAlone/Nagram)
- [NagramX](https://github.com/risin42/NagramX)
- [Nekogram](https://github.com/Nekogram/Nekogram)
- [OctoGram](https://github.com/OctoGramApp/OctoGram)

---

## English

### What this is

exteraless is a fork of [NagramX](https://github.com/risin42/NagramX) that implements
exteraGram's features open-source.

The special focus is **plugin security**. In exteraGram a plugin is not restricted in
any way; here it comes with a permission model and isolation: a plugin declares what it
needs, you see that on the install sheet, and it gets only what was declared.

The project is **in beta**: some exteraGram features have not been ported yet. If you
notice a missing feature, open an issue or write to the [channel](https://t.me/exteraless?direct).

* Package name: `com.exteraless.app`

### Design credits

Icons and visual design inherited from exteraGram are the work of its designer,
[@the8055u](https://t.me/the8055u), and the [@BlueprintDsgn](https://t.me/BlueprintDsgn)
studio. Rights to those materials belong to their authors.

### Building

1. Clone with submodules:

    ```bash
    git clone --recursive --shallow-submodules https://github.com/exteraless/exteraless.git exteraless
    ```

2. Get `TELEGRAM_APP_ID` and `TELEGRAM_APP_HASH` from [my.telegram.org](https://my.telegram.org/auth)
   and put them into `local.properties` in the project root.

3. For release signing, drop your own `TMessagesProj/release.keystore` and add
   `KEYSTORE_PASS`, `ALIAS_NAME`, `ALIAS_PASS` to `local.properties`. No keystore is
   shipped with the repository; without one the build is signed with the Android debug key.

4. For push notifications, replace `TMessagesProj/google-services.json` with your own
   Firebase config for `com.exteraless.app`.

5. Build with `./gradlew :TMessagesProj:assembleDebug` or from Android Studio.

Only 64-bit ABIs are built (`arm64-v8a`, `x86_64`): Chaquopy ships Python 3.12 for those
only, and `armeabi-v7a` fails at configuration time. `NATIVE_TARGET` selects the target:
`arm64-v8a`, `universal` (both) or `SKIP` (no native part).

For CI, set two repository secrets — `LOCAL_PROPERTIES` and `RELEASE_KEYSTORE`, both
base64-encoded — and run the **Release Build** workflow. The APK ends up in the run
artifacts.
