"""Run real lazy destination creation, selection and gesture updates with sparse tab slots."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_trial_uses_native_tab_count_without_flexy_destination_registry():
    source=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'MainTabsHelper.getFragmentsCount()' in source
    assert 'ensureFlexyTab' not in source and 'LiquidNavigationDestinations' not in source
