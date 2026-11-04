# FlexyStudio configuration backup

The current beta previously exported only 23 visual options and omitted defaults. Header style 3 made export fail validation, and message/external-file handling was still gated to Connected Alpha.

New exports contain a typed, versioned `client.settings` bundle inside the existing checksummed `.flexyGram` envelope. The catalog uses the native ConfigItem metadata from Neko, Na, OpenExtera, Appearance, Chats, General, Icons, PillStack, Utils and Glyph, plus explicit native Flexy preference keys. Retired universal blur-editor preferences are ignored. It includes native Liquid Glass/power-saving preferences, bubble outlines/fusion, header, composer, navigation, previews, Member Lens, files, inline conversion, portable AI toggles, Telegram appearance/behavior, launcher icon and the active theme colors/wallpaper. Each key records presence; absent source keys remove corresponding destination values, restoring native defaults rather than leaving destination customization behind.

Only registered files/keys and their native types can be written. Integer sets/maps use typed JSON, never deserialization of imported Java objects. Session databases, passcodes, API keys/tokens, AI conversation history, plugin code/grants, and device runtime state are excluded. Custom icon packs, plugin installations, external storage grants and custom language files must already exist on the receiving device. Per-account/per-chat Telegram data is outside this portable client preset. Active linked wallpapers retain the native link and may require a download; embedded bitmap wallpapers are bounded to 4 MiB (PNG, falling back to native JPEG87 for large images). The envelope limit is 8 MiB. This is a configuration preset, not a device/account backup.

Import validates the whole bundle before edits. A durable atomic rollback journal covers the complete previous state; its length-prefixed UTF-8 format supports strings over writeUTF's 64 KiB limit and still reads old journals. Failed writes trigger restoration; interrupted imports recover at startup. Native caches are reloaded explicitly once, not observed during rendering. Undo compares the actual applied state and refuses to overwrite subsequent user edits. Old partial visual presets remain supported.

SAF export streams a private staged file rather than placing large byte arrays in fragment state. Explicit import verifies contents even when a provider renames the file or omits its display name. Share uses a bounded private cache, an octet-stream send intent and a dedicated FileProvider read grant. Pending export files are outside the provider's exposed path. Failure to schedule optional cache cleanup does not cancel sharing.

Validation without APK packaging:

- `python -m pytest -q tests tools/connected_alpha/test_flexystudio.py`
- `python tools/connected_alpha/check_studio_client.py`: production catalog/backup/codec/transaction round trips, default restoration, primitive/collection types, excluded secrets, undo conflicts and injected mid-import write failure. Android persistence/theme/owner APIs are doubles.
- `python tools/connected_alpha/check_studio_types.py`: all Studio Java against Android API37 and explicit native API doubles.

A physical-device check of SAF/cloud providers, Android share targets, theme rendering, process recreation and external asset availability remains necessary when the next beta is authorized. These checks do not build or validate a full APK.
