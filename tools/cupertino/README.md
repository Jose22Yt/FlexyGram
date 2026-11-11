# Historical Cupertino font tooling

This directory records the earlier Flutter Cupertino font/catalog and its provenance.
Starting in beta 41, the default icons and the former Cupertino UI selection use the verified Telegram-iOS import in `tools/ios_originals/`. This font is not the source of that import.

The old `android/` render probe describes historical font geometry and press effects; it does not validate the new original-icon loader or current UI. Use the current regression suite, `tools/ios_originals/generate.py --check` and `tools/ios_originals/check_android_types.py` for the beta 41 implementation. Earlier probe screenshots are not evidence of iOS 27 parity.
