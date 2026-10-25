/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
/** Separate authority: cannot expose logs, accounts, arbitrary cache or external storage. */
public final class FlexyStudioProvider extends androidx.core.content.FileProvider {
    @Override public String getType(android.net.Uri uri){return app.flexygram.studio.core.StudioSchema.MIME;}
}
