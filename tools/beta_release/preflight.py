#!/usr/bin/env python3
"""Read-only environment-input diagnostic. Never prints credentials or opens a private key."""
import json
import os
from pathlib import Path
from verify_beta_apk import ROOT, APP, OFFICIAL, expected_version


def inspect(environ=None, root=ROOT):
    environ = os.environ if environ is None else environ
    required = ['FLEXYGRAM_RELEASE_KEYSTORE','FLEXYGRAM_RELEASE_STORE_PASSWORD',
                'FLEXYGRAM_RELEASE_KEY_ALIAS','FLEXYGRAM_RELEASE_KEY_PASSWORD',
                'TELEGRAM_APP_ID','TELEGRAM_APP_HASH']
    missing = [name for name in required if not environ.get(name)]
    problems = []
    path = environ.get('FLEXYGRAM_RELEASE_KEYSTORE')
    if path:
        path = Path(path).resolve()
        if not path.is_file(): problems.append('OFFICIAL_KEYSTORE_FILE_UNAVAILABLE')
        elif path.is_relative_to(root.resolve()): problems.append('KEYSTORE_MUST_BE_OUTSIDE_CHECKOUT')
    alias = environ.get('FLEXYGRAM_RELEASE_KEY_ALIAS')
    if alias and alias != 'flexygram-release': problems.append('WRONG_OFFICIAL_ALIAS')
    firebase = root/'TMessagesProj/src/beta/google-services.json'
    if not firebase.is_file(): missing.append('BETA_FIREBASE_CONFIGURATION_FILE')
    else:
        try:
            config = json.loads(firebase.read_text())
            if not any(c.get('client_info',{}).get('android_client_info',{}).get('package_name') == APP
                       for c in config.get('client',[])):
                problems.append('FIREBASE_BETA_PACKAGE_MISSING')
        except (ValueError, OSError, AttributeError, TypeError):
            problems.append('INVALID_BETA_FIREBASE_CONFIGURATION')
    return {'status':'INPUTS_PRESENT_PRIVATE_VALIDATION_REQUIRED' if not missing and not problems else 'BLOCKED_MISSING_OR_INVALID_INPUTS',
            'missing_input_names':missing,'problems':problems,'expected_certificate_sha256':OFFICIAL,
            'private_key_certificate_correspondence':'NOT_CHECKED','apk':'NOT_BUILT',
            'scope':'ENVIRONMENT_INPUTS_ONLY; original Gradle validation remains mandatory'}


if __name__ == '__main__':
    expected_version()
    report = inspect()
    print(json.dumps(report, indent=2))
    raise SystemExit(2 if report['missing_input_names'] or report['problems'] else 0)
