"""Cross-surface routing; native Canvas regressions live in composer_surface."""
from test_render_work_reuse import JAVA


def test_trial_uses_native_dock_and_disables_flexy_glass_islands():
    home=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    dock=(JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    assert 'applyFlexyTabs' not in home and 'separateSearchButton' not in home
    assert 'createMainTab' in home and 'setBottomNavigationMode' in dock
    for path,signature in [('org/telegram/ui/ActionBar/ActionBar.java','drawSignatureNativeGlass'),('org/telegram/ui/Components/chat/ChatInputViewsContainer.java','setCompactGlassFactory')]:
        text=(JAVA/path).read_text();body=text[text.index(signature):]
        assert 'BuildConfig.NATIVE_BASELINE_TEST) return' in body[:500]


def test_folder_selection_has_distinct_glass_contrast_cache_and_uses_native_background():
    folders=(JAVA/'org/telegram/ui/Components/FilterTabsView.java').read_text()
    assert 'signaturePalette=themed?signatureGlassAccentColors:signatureGlassDefaultColors' in folders
    assert 'signaturePillGlass.draw(canvas)' in folders
    assert 'signatureGlassAccentColors.update(app.flexygram.home.SignatureHomeStyle.glassSelectionTint(signatureAccent)' in folders
    assert 'listView.invalidateViews();' in folders
