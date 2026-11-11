"""Delivery regression: optional reports must never gate a verified APK."""
from pathlib import Path
import yaml


def test_verified_apk_is_uploaded_before_nonblocking_diagnostics():
    root = Path(__file__).resolve().parents[1]
    workflow = yaml.safe_load((root / '.github/workflows/ui-beta-debug.yml').read_text())
    steps = workflow['jobs']['build']['steps']
    names = [step['name'] for step in steps]
    verify = steps[names.index('Verify APK signature and native ABI')]
    apk = steps[names.index('Save debug APK')]
    reports = steps[names.index('Save build reports')]
    assert names.index(verify['name']) < names.index(apk['name']) < names.index(reports['name'])
    assert verify['id'] == 'verify_apk'
    # Verification failure/cancellation forbids delivery; unrelated report/summary
    # problems must not prevent the upload of an already verified binary.
    assert apk['if'] == "${{ !cancelled() && steps.verify_apk.outcome == 'success' }}"
    assert apk.get('continue-on-error', False) is False
    assert apk['with']['if-no-files-found'] == 'error'
    assert reports['continue-on-error'] is True
    assert reports['if'] == 'always()'
