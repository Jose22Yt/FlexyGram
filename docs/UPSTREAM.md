# Procedencia de FlexyGram

FlexyGram es el cliente Android dirigido por @Lukhou23, publicado bajo la cuenta Jose22Yt. Es una obra derivada; la identidad de FlexyGram no sustituye la autoría de Telegram, Exteraless ni de otros colaboradores.

## Historia verificable

- Origen conservado: [Exteraless](https://github.com/exteraless/exteraless), commit `1ad6a60a6834ffca722b1a22f4fba27ecb29a061`.
- Base de esta auditoría: [Alpha1274, PR95](https://github.com/Jose22Yt/FlexyGram/pull/95), `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`.
- El README de `main`, revisado en `db1bea24b7b705de33f8ff8c8e174011c153cac7`, describe el Paso1 inicial; no refleja el estado de las ramas Connected Alpha.
- La [copia histórica exacta del README heredado](upstream/README.exteraless.md) conserva sus textos, enlaces y créditos. Sus comandos y su declaración de Beta describen Exteraless, no el estado actual de FlexyGram. Sus rutas relativas se interpretan desde la raíz del repositorio de origen: no son instrucciones nuevas ni enlaces oficiales de distribución de FlexyGram.

El historial Git no se reescribe ni se eliminan avisos existentes. La comparación reproducible es `git diff 1ad6a60a6834ffca722b1a22f4fba27ecb29a061 8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. El árbol y los gitlinks concretos, no solo el nombre de una rama, identifican las dependencias.

## Proyectos y agradecimientos conservados

La documentación original identifica NagramX como base de Exteraless y describe implementación abierta de funciones de exteraGram. Se reconoce a [Telegram](https://github.com/DrKLO/Telegram), [Exteraless](https://github.com/exteraless/exteraless), [NagramX](https://github.com/risin42/NagramX), [exteraGram](https://github.com/exteraSquad/exteraGram), [Nagram](https://github.com/NextAlone/Nagram), [Nekogram](https://github.com/Nekogram/Nekogram), [AyuGram](https://github.com/AyuGram/AyuGram4A), [Cherrygram](https://github.com/arsLan4k1390/Cherrygram), [Dr4iv3rNope](https://github.com/Dr4iv3rNope/NotSoAndroidAyuGram), [Inugram](https://github.com/teidesu/inugram) y [OctoGram](https://github.com/OctoGramApp/OctoGram).

Esta lista conserva atribuciones del proyecto; no afirma una cadena directa de commits para todos ellos, una asociación comercial ni que hayan aprobado FlexyGram.

El diseño y los iconos heredados de exteraGram conservan los créditos a [@the8055u](https://t.me/the8055u) y [@BlueprintDsgn](https://t.me/BlueprintDsgn). Los derechos de esos recursos pertenecen a sus autores. Los archivos de paquetes, clases, preferencias, servicios y proveedores que contienen nombres heredados se conservan cuando funcionan como identificadores técnicos.

## Licencias y distribución

La licencia principal del repositorio es [GNU GPLv3](../LICENSE). Cada archivo/componente puede tener avisos y condiciones adicionales. No se sustituye la licencia de una dependencia por la del proyecto principal. El [inventario de atribuciones](ATTRIBUTIONS.md) detalla qué se comprobó y qué falta.

Al distribuir binarios se debe revisar el suministro del código fuente correspondiente, modificaciones, scripts de construcción y avisos aplicables a esa versión, incluidas bibliotecas y submódulos. Una release debe enlazar un commit real y conservar fuentes de los componentes modificados; no basta con un enlace genérico a una rama que continúa cambiando. Los secretos de firma y credenciales de servicio no se incluyen en la publicación de fuentes.

Referencias primarias: [GPLv3, secciones4–6](https://www.gnu.org/licenses/gpl-3.0.en.html), [condiciones de la API de Telegram](https://core.telegram.org/api/terms), [API ID y publicación de código](https://core.telegram.org/api/obtaining_api_id). El inventario técnico no certifica por sí solo el cumplimiento legal de una distribución.
