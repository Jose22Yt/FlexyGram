# Atribuciones y recursos

Inventario fijado a Alpha1274 `8d4fe2f0a7d47e05a34c2a2c7fc8c706ed781881`. [license-inventory.json](prebeta/license-inventory.json) registra31 archivos de licencia rastreados, sus SHA256 y los gitlinks de submódulos. La clasificación de familias es heurística: hay que leer los textos y sus excepciones.

| Conjunto | Evidencia conservada | Situación antes de Beta |
| --- | --- | --- |
| Código principal | `LICENSE`, cabeceras de archivos e historial | GPLv3 principal preservada; preparar fuentes correspondientes al binario distribuido y avisos de modificaciones |
| Telegram y forks anteriores | README heredado y [UPSTREAM](UPSTREAM.md) | Atribuciones conservadas; no presentar todo el código como creación de FlexyGram |
| Iconos/diseño exteraGram | Crédito heredado a @the8055u y @BlueprintDsgn | Crédito explícito no equivale a permiso de redistribución. Falta inventario por recurso con licencia o autorización demostrable |
| Identidad azul de FlexyGram | `tools/connected_alpha/identity/flexygram-blue-original.png`; `identity/build_icons.py` dice que adapta la imagen seleccionada por el propietario | Reutilizada en README sin editar el launcher. Conservar prueba de origen/derechos del archivo original; el script no constituye una cesión de derechos |
| Iconos alternativos/paquetes | `LauncherIconController`, `app/exteraless/icons`, drawables y recursos heredados | Revisar procedencia de cada familia, incluidos nombres y recursos de otros clientes; no borrar aliases para una limpieza visual |
| BoringSSL, codecs y medios | Licencias bajo `TMessagesProj/jni`, incluidas GPL/LGPL/FDL/Xiph/BSD y condiciones específicas | Inventario de textos disponible. Comprobar qué librerías se empaquetan realmente, variantes, obligaciones y fuentes correspondientes |
| Submódulos nativos, media, Chaquopy | URLs y commits exactos en inventario generado de `.gitmodules`/gitlinks | Sus licencias internas no se consideran revisadas por el solo hecho de registrar el gitlink; faltan notices de cada revisión y SBOM transitiva |
| Maven/AAR, Kotlin, Firebase y bibliotecas Java | Gradle y dependencias resueltas por la compilación | No hay SBOM completa de la APK en esta auditoría. Generarla desde la compilación real y conciliar NOTICE/licencias transitivas |
| Python y wheels reconstruidos | Chaquopy y `rebuild_python_wheels.py`/provenance | Conciliar versiones, fuentes, hashes y avisos del wheelhouse empaquetado |
| Capturas | No hay colección real aprobada identificada por versión en esta entrega | No publicar imágenes con datos de usuarios ni llamar captura de la app a un renderer sintético |

## Créditos en la aplicación

`OpenExteraSettingsActivity.showFlexyCredits()` ya conserva un acceso a licencia y upstream; `FlexySettingsCreditsBody` conserva agradecimientos. Debe permanecer accesible y complementarse con las licencias de dependencias efectivamente distribuidas. El About heredado `NekoAboutActivity` aún contiene enlaces que se presentan como canal/fuente de NagramX: no confundir un enlace legal a upstream con un enlace oficial de FlexyGram.

## Cierre de distribución

Antes de Beta: asociar cada binario a HEAD, SBOM, avisos y fuentes; verificar derechos de recursos gráficos/fuentes; revisar términos de Telegram y prestaciones heredadas; conservar el historial y los avisos. No renombrar copyrights de terceros ni sustituirlos por el nombre del responsable de FlexyGram. Esta rama no concede permisos sobre obras ajenas ni elimina avisos.
