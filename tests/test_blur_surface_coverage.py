"""Cross-surface routing; native Canvas regressions live in composer_surface."""
from test_render_work_reuse import JAVA


def test_trial_uses_native_material_for_custom_chat_surfaces_with_lazy_islands():
    home=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    dock=(JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    assert 'applyFlexyTabs' not in home and 'separateSearchButton' not in home
    assert 'createMainTab' in home and 'setBottomNavigationMode' in dock
    from test_composer_layout import method
    header=method((JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text(),'public boolean drawSignatureNativeGlass(')
    assert 'BuildConfig.NATIVE_BASELINE_TEST' not in header
    assert 'canvas.isHardwareAccelerated()' in header and 'SharedConfig.chatBlurEnabled()' in header
    source=(JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    lazy=method(source,'private void prepareCompactGlass()')
    assert '!FlexyComposerConfig.compact()' in lazy and '!org.telegram.messenger.SharedConfig.chatBlurEnabled()' in lazy
    assert 'compactGlass[0]!=null' in lazy



def test_folder_selection_has_distinct_glass_contrast_cache_and_uses_native_background():
    folders=(JAVA/'org/telegram/ui/Components/FilterTabsView.java').read_text()
    assert 'signaturePalette=themed?signatureGlassAccentColors:signatureGlassDefaultColors' in folders
    assert 'signaturePillGlass.draw(canvas)' in folders
    assert 'signatureGlassAccentColors.update(app.flexygram.home.SignatureHomeStyle.glassSelectionTint(signatureAccent)' in folders
    assert 'listView.invalidateViews();' in folders
