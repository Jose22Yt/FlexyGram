"""Cross-surface routing; native Canvas regressions live in composer_surface."""
from test_render_work_reuse import JAVA


def test_native_blur_routes_cover_home_dock_folders_header_and_composer():
    home=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    dock=(JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    folders=(JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    header=(JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
    composer=(JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    assert 'tabsView.setGlassBackground(dockFactory.create(tabsView, dockGlassColors)' in home
    assert 'glassBackground.draw(canvas)' in dock and 'SharedConfig.chatBlurEnabled()' in dock
    assert 'filterTabsView.setSignatureGlassFactory(iBlur3FactoryLiquidGlass)' in folders
    assert 'if (filterTabsView != null) filterTabsView.updateColors();' in folders
    assert 'public boolean drawSignatureNativeGlass(Canvas canvas' in header
    assert 'SharedConfig.chatBlurEnabled()' in header
    assert 'drawFlexyNativeGlassIslands(canvas, offsetX, offsetY, radius, attach)' in composer
    assert 'drawCompactGlass(canvas, 0, flexyPill, radius)' in composer


def test_folder_selection_has_distinct_glass_contrast_cache_and_uses_native_background():
    folders=(JAVA/'org/telegram/ui/Components/FilterTabsView.java').read_text()
    assert 'signaturePalette=themed?signatureGlassAccentColors:signatureGlassDefaultColors' in folders
    assert 'signaturePillGlass.draw(canvas)' in folders
    assert 'signatureGlassAccentColors.update(app.flexygram.home.SignatureHomeStyle.glassSelectionTint(signatureAccent)' in folders
    assert 'listView.invalidateViews();' in folders
