package org.telegram.ui.beta;

import android.os.Bundle;

/** Only local synthetic screen/theme. Never account/session credentials or a runtime-success assertion. */
final class BetaUiState {
    enum Route { HOME, CONVERSATION, SETTINGS }
    private static final String VERSION = "flexygram.beta.ui.version";
    private static final String ROUTE = "flexygram.beta.ui.route";
    private static final String DARK = "flexygram.beta.ui.dark";
    final Route route;
    final boolean dark;

    BetaUiState(Route route, boolean dark) { this.route = route; this.dark = dark; }
    @SuppressWarnings("deprecation")
    static BetaUiState restore(Bundle state, boolean currentDark) {
        BetaUiState empty = new BetaUiState(Route.HOME, currentDark);
        if (state == null) return empty;
        try {
            // Inspect types ourselves: typed Bundle getters can log supplied values on a mismatch.
            Object version = state.get(VERSION), route = state.get(ROUTE), dark = state.get(DARK);
            if (!(version instanceof Integer) || ((Integer)version) != 1 || !(route instanceof Integer)
                    || !(dark instanceof Boolean)) return empty;
            int index = (Integer)route;
            if (index < 0 || index >= Route.values().length) return empty;
            return new BetaUiState(Route.values()[index], (Boolean)dark);
        } catch (RuntimeException malformedFrameworkState) {
            return empty; // no Bundle contents or exception details in diagnostics
        }
    }
    void save(Bundle state) {
        state.putInt(VERSION, 1);
        state.putInt(ROUTE, route.ordinal());
        state.putBoolean(DARK, dark);
    }
}
