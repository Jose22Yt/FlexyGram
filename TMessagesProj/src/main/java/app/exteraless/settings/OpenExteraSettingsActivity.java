/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.exteraless.settings;
/** Stable class/entry alias for deep links and plugins. No second settings tree. */
public class OpenExteraSettingsActivity extends app.flexygram.settings.signature.SignatureSettingsActivity {
    public OpenExteraSettingsActivity(){super("root");}
    @Override protected String getKey(){return "exteraless";}
    @Override public int getSearchGuid(){return 24000;}
    @Override public String getSearchPrefix(){return "OpenExtera";}
}
