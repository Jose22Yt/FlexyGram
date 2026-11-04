package app.flexygram.settings.signature;

/** Classifies off-screen neighbors too, so scrolling cannot change a group's corner shape. */
public interface SettingsSectionTypes {
    boolean isSettingsContentType(int viewType);
}
