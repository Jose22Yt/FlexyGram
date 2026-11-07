"""Beta verifies the intended new default without changing Alpha's expected alias."""
import importlib.util
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
from verify_apk import has_launcher_alias
from test_verify_apk import PACKAGED_MANIFEST


def test_beta_glossy_alias_is_explicit_and_alpha_default_is_preserved():
    glossy=PACKAGED_MANIFEST.replace('org.telegram.messenger.ExteralessIcon','org.telegram.messenger.FlexyGlossyIcon')
    assert has_launcher_alias(PACKAGED_MANIFEST)
    assert not has_launcher_alias(glossy)
    assert has_launcher_alias(glossy,('org.telegram.messenger.FlexyGlossyIcon',))
    assert not has_launcher_alias(PACKAGED_MANIFEST,('org.telegram.messenger.FlexyGlossyIcon',))
    assert not has_launcher_alias(glossy.replace('FlexyGlossyIcon','FlexyNeonIcon'),('org.telegram.messenger.FlexyGlossyIcon',))
