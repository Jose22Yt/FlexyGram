"""DEX review fixtures; these tests do not execute Android."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('combined_apk_review', ROOT / 'tools/real_alpha/review_apk.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
LIFECYCLE = """
    #1
      name : 'onResume'
      invoke-super {v0}, Lorg/telegram/ui/LaunchActivity;.onResume:()V
      invoke-virtual {v0}, Lorg/telegram/ui/realalpha/local/RealAlphaLocalLoginHost;.attachEntry:()V
    #2
      name : 'onDestroy'
      invoke-virtual {v0}, Lorg/telegram/ui/realalpha/local/RealAlphaLocalLoginHost;.close:()V
      invoke-super {v0}, Lorg/telegram/ui/LaunchActivity;.onDestroy:()V
"""
LISTING = """Class #0
  Class descriptor : 'Lorg/telegram/ui/realalpha/RealAlphaActivity;'
  Superclass : 'Lorg/telegram/ui/LaunchActivity;'
    #0
      name : 'getClientNotActivatedFragment'
      new-instance v0, Lorg/telegram/ui/DialogsActivity;
      invoke-direct {v0,v1}, Lorg/telegram/ui/DialogsActivity;.<init>
""" + LIFECYCLE + """Class #1
  Class descriptor : 'Lorg/telegram/ui/LaunchActivity;'
      name : 'onBackPressed'
      invoke-interface registerOnBackInvokedCallback
      invoke-interface unregisterOnBackInvokedCallback
      check-cast OnBackAnimationCallback
Class #2
  Class descriptor : 'Lorg/telegram/ui/DialogsActivity;'
      name : 'offlineAwareEmptyView'
Class #3
  Class descriptor : 'Lorg/telegram/ui/realalpha/local/RealAlphaLocalLoginHost;'
Class #4
  Class descriptor : 'Lorg/telegram/ui/realalpha/local/LocalLoginRehearsal;'
Class #5
  Class descriptor : 'Lorg/telegram/ui/realalpha/offline/OfflineDialogsUi;'
Class #6
  Class descriptor : 'Lio/github/jose22yt/flexygram/login/local/LocalLoginSession;'
Class #7
  Class descriptor : 'Lorg/telegram/ui/LoginActivity;'
      name : 'bindClosedLocalPages'
Class #8
  Class descriptor : 'Lorg/telegram/ui/Adapters/DialogsSearchAdapter;'
    #0
      name : 'cancelOfflineSearch'
    #1
      name : 'searchOfflineDialogs'
"""

class CombinedApkTests(unittest.TestCase):
    def check(self, listing, combined=True):
        with tempfile.TemporaryDirectory() as folder:
            apk = Path(folder) / 'fixture.apk'
            with zipfile.ZipFile(apk, 'w') as z:
                z.writestr('classes.dex', b'synthetic DEX fixture')
            with patch.object(r, 'command', return_value=listing):
                r.verify_dex_linkage(apk, Path('fixture-dexdump'), combined)

    def test_combined_cleanup_is_accepted_only_with_explicit_profile(self):
        self.check(LISTING)
        with self.assertRaises(ValueError):
            self.check(LISTING, False)

    def test_missing_cleanup_super_delegation_or_extra_call_is_rejected(self):
        for old, new in (
            ('LocalLoginHost;.close:', 'LocalLoginHost;.other:'),
            ('LaunchActivity;.onDestroy:', 'LaunchActivity;.other:'),
            ('LaunchActivity;.onResume:', 'LaunchActivity;.other:'),
            ('LocalLoginHost;.attachEntry:', 'LocalLoginHost;.other:'),
            ("name : 'onDestroy'", "name : 'onDestroy'\n      invoke-static external.Service;.connect:()V")):
            with self.subTest(old=old), self.assertRaises(ValueError):
                self.check(LISTING.replace(old, new))

    def test_cleanup_order_back_override_and_missing_combined_classes_rejected(self):
        close = '      invoke-virtual {v0}, Lorg/telegram/ui/realalpha/local/RealAlphaLocalLoginHost;.close:()V'
        parent = '      invoke-super {v0}, Lorg/telegram/ui/LaunchActivity;.onDestroy:()V'
        for listing in (LISTING.replace(close+'\n'+parent, parent+'\n'+close),
                        LISTING.replace("name : 'onDestroy'", "name : 'onBackPressed'"),
                        LISTING.replace("name : 'bindClosedLocalPages'", "name : 'unrelatedMethod'"),
                        LISTING.replace("name : 'searchOfflineDialogs'", "name : 'unrelatedMethod'"),
                        LISTING.replace('realalpha/offline/OfflineDialogsUi;', 'fixture/Missing;')):
            with self.subTest(listing=listing[-80:]), self.assertRaises(ValueError):
                self.check(listing)

if __name__ == '__main__':
    unittest.main()
