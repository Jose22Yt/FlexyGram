"""Removed feature cannot keep suppressing native notifications after an update."""
from pathlib import Path
import xml.etree.ElementTree as ET
from test_render_work_reuse import JAVA,ROOT
from test_composer_layout import method


def test_notification_island_has_no_runtime_hooks_settings_or_resources():
    assert not (JAVA/'app/flexygram/camerapop').exists()
    for path in [JAVA/'org/telegram/ui/LaunchActivity.java',
                 JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java',
                 JAVA/'app/flexygram/settings/signature/Settings3LinksSection.java']:
        source=path.read_text()
        assert 'CameraPop' not in source and 'camera_pop' not in source and 'camerapop' not in source
    for locale in ['values','values-es']:
        names=[e.get('name','') for e in ET.parse(ROOT/f'TMessagesProj/src/main/res/{locale}/strings.xml').getroot()]
        assert not any(n.startswith('CameraPop') for n in names)


def test_native_notification_paths_use_original_pending_messages_without_island_filter():
    source=(JAVA/'org/telegram/messenger/NotificationsController.java').read_text()
    assert 'islandVisibleMessages' not in source and 'routesToIsland' not in source and 'flexy_camera_pop_' not in source
    summary=method(source,'private void showOrUpdateNotification(boolean notifyAboutLast)')
    detail=method(source,'private void showExtraNotifications(')
    assert 'pushMessages.get(' in summary and 'pushMessages.get(' in detail
    assert 'ArrayList<MessageObject> pushMessages =' not in summary+detail
    assert 'showExtraNotifications(' in summary
    assert (JAVA/'org/telegram/ui/Components/ProfileGooeyView.java').is_file()
    assert 'NotchInfoUtils' in (JAVA/'org/telegram/ui/Components/ProfileGooeyView.java').read_text()
