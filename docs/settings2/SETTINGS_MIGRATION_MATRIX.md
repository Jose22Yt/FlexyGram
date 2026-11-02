# Migration and integration map

No preferences are migrated, renamed, reset or copied. This change scopes original row creation and routes to existing controllers. Root categories are exactly the eight requested, in the requested order. About is a separate legal/information destination.

| Route | Parent | Visible title |
| --- | --- | --- |
| appearance | root | Apariencia e interfaz |
| navigation | root | Navegación y gestos |
| conversations | root | Mensajes y conversaciones |
| studio | root | FlexyStudio |
| files | root | Archivos y descargas |
| extensions | root | Extensiones |
| general | root | General y conexión |
| advanced | root | Opciones avanzadas |
| chat_list | appearance | Diseño de la lista de chats |
| avatars | appearance | Avatares |
| folders | appearance | Carpetas de chats |
| visible | appearance | Elementos visibles |
| bubbles | appearance | Burbujas de mensajes |
| header | appearance | Cabecera del chat |
| composer | appearance | Barra de escritura (Composer) |
| post_appearance | appearance | Presentación de publicaciones |
| icons | appearance | Iconos y emojis |
| fonts | appearance | Fuentes del sistema |
| effects | appearance | Efectos visuales |
| appearance_extra | appearance | Opciones adicionales de apariencia |
| bottom_tabs | navigation | Barra de navegación inferior |
| app_navigation | navigation | Menú lateral y navegación |
| gestures | navigation | Acciones de mensajes y deslizamiento |
| navigation_extra | navigation | Navegación adicional |
| messages | conversations | Comportamiento de mensajes |
| context | conversations | Interacción de mensajes |
| menus | conversations | Menús y acciones |
| stickers | conversations | Stickers, GIF y respuestas |
| media | conversations | Cámara y multimedia |
| profile | conversations | Información de contactos |
| archive | conversations | Archivo y organización |
| messages_extra | conversations | Opciones adicionales de conversación |
| stickers_extra | conversations | Opciones adicionales de stickers |
| media_extra | conversations | Opciones adicionales de reproducción |
| plugins | extensions | Plugins |
| ai | extensions | IA de Exteraless |
| translation | extensions | Traducción avanzada |
| pillstack | extensions | Pill Stack |
| translator | translation | Proveedor e idiomas |
| translation_options | translation | Presentación de traducciones |
| layout | chat_list | Disposición y títulos |
| smart_previews | chat_list | Smart Mini Pills |
| launcher | icons | Icono de la aplicación |
| icon_packs | icons | Paquetes de iconos |
| emoji | icons | Conjuntos de emojis |
| surfaces | effects | Superficies y efectos existentes |
| animations | effects | Animaciones de mensajes |
| general_controls | general | General, red, mapas y push |
| general_extra | general | Opciones generales adicionales |
| advanced_controls | advanced | Privacidad y mantenimiento |
| advanced_extra | advanced | Diagnóstico |
| cloud | advanced | Sincronización de ajustes heredada |
| passcode | advanced | Protección adicional de ajustes |
| appearance_extra_ng | appearance_extra | Estilos y elementos de interfaz |
| appearance_extra_nx | appearance_extra | Compatibilidad tipográfica |
| media_extra_ng | media_extra | Red y vista previa multimedia |
| media_extra_nc | media_extra | Archivos y calidad |
| media_extra_nx | media_extra | Vídeo y audio en llamadas |
| stickers_extra_ng | stickers_extra | Accesos a stickers |
| stickers_extra_nc | stickers_extra | Panel y recientes |
| stickers_extra_nx | stickers_extra | Límites y selección |
| navigation_extra_ng | navigation_extra | Visibilidad de pestañas |
| navigation_extra_nx | navigation_extra | Transiciones existentes |
| advanced_extra_ng | advanced_extra | Privacidad y protección adicional |
| advanced_extra_nx | advanced_extra | Clase del dispositivo y errores RPC |

## Special moves

| Old location | New location | Storage / behavior |
| --- | --- | --- |
| Studio → FlexyFiles enable/help | Files and downloads | Original `FlexyFiles.enabled()` and help; `flexyfiles_local` / `enabled` unchanged |
| General → custom save path and per-chat folders | Files and downloads | Original General handlers, SAF and keys |
| Native appearance → client launcher selector | Appearance → Icons → Launcher | Original AppIconsSelectorCell and launcher controller |
| Native privacy → additional system-account control | Advanced → additional controls | Original NekoGeneral callback/key |
| Language → extra translator controls | Extensions → Translation | Original translator screen/controllers |
| Old NagramX root / exteraless root | Eight-category FlexyGram root | Existing class/deep-link aliases retained |

Scoped pages save their source and route in fragment arguments. Legacy deep links resolve to a canonical editor and retain existing value import confirmation. Search uses distinct scoped GUIDs. Conditional row insertions require owner admission before adapter notifications. Existing native tabs and Signature dock preferences have distinct backends; they are not silently merged or migrated. Their mode-specific visibility must be checked physically.

## Integration

1. Review this draft against official Beta; do not replace entire files from another branch.
2. Retain official DialogsActivity and PR158 FlexyFiles changes; this branch does not modify either backend.
3. Run `python3 tools/settings2/checks.py`, general tests and the isolated Android probe as described in VALIDATION.md.
4. Obtain the normal protected source review before the full Beta build. Do not bypass frozen source scopes, signing or distribution controls.
5. Perform the device acceptance checklist, particularly legacy deep links, all conditional rows and launcher/icon visibility.
6. If regression occurs, revert this feature commit as a unit. Preference data has not been migrated; no data restoration should be needed.
