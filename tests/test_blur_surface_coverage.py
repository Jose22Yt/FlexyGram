"""Cross-surface routing; native Canvas regressions live in composer_surface."""
from test_render_work_reuse import JAVA
from test_composer_layout import method


def test_trial_keeps_native_dock_and_enables_hardware_chat_glass():
    home = (JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    dock = (JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    assert 'applyFlexyTabs' not in home and 'separateSearchButton' not in home
    assert 'createMainTab' in home and 'setBottomNavigationMode' in dock
    header = method((JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text(),
                    'public boolean drawSignatureNativeGlass(')
    composer = method((JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text(),
                      'private boolean canDrawCompactGlass(')
    for route in (header, composer):
        assert 'NATIVE_BASELINE_TEST' not in route
        assert 'isHardwareAccelerated()' in route and 'isBlurEnabled()' in route


def test_folder_selection_has_distinct_glass_contrast_cache_and_uses_native_background():
    folders=(JAVA/'org/telegram/ui/Components/FilterTabsView.java').read_text()
    assert 'signaturePalette=themed?signatureGlassAccentColors:signatureGlassDefaultColors' in folders
    assert 'signaturePillGlass.draw(canvas)' in folders
    assert 'signatureGlassAccentColors.update(app.flexygram.home.SignatureHomeStyle.glassSelectionTint(signatureAccent)' in folders
    assert 'listView.invalidateViews();' in folders
