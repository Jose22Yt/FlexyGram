/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import java.util.Locale;

/** Pure filename policy: a .plugin is a document, never an executable plugin. */
final class FlexyEditorFileTypes {
    private FlexyEditorFileTypes() { }

    static boolean isPlugin(String name) {
        return name != null && name.toLowerCase(Locale.ROOT).endsWith(".plugin");
    }

    /** Extension alone cannot establish whether a .plugin is text or binary. */
    static boolean canEditPlugin(String name, boolean decodedAsBoundedText) {
        return isPlugin(name) && decodedAsBoundedText;
    }

    /** Never load or execute a plugin as a side effect of opening it in FlexyFiles. */
    static boolean mayExecuteFromEditor(String name) {
        return false;
    }
}
