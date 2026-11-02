#!/usr/bin/env python3
"""Stage authorized CI inputs. Errors identify fields, never their values."""
import base64
import binascii
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

APP = 'io.github.jose22yt.flexygram.alpha'
ROOT = Path(__file__).resolve().parents[2]


def fingerprint(value):
    normalized = re.sub(r'[:\s]', '', value).lower()
    if not re.fullmatch(r'[0-9a-f]{64}', normalized):
        raise ValueError('ALPHA_CERTIFICATE_SHA256 must be a SHA-256 certificate fingerprint')
    return normalized


def validate_api(env):
    app_id = env.get('TELEGRAM_APP_ID', '')
    app_hash = env.get('TELEGRAM_APP_HASH', '')
    if not re.fullmatch(r'[1-9][0-9]{0,9}', app_id) or int(app_id) > 2147483647 or app_id in {'4', '6', '2040'}:
        raise ValueError('TELEGRAM_APP_ID is missing, malformed or inherited/sample')
    if not re.fullmatch(r'[0-9a-fA-F]{32}', app_hash):
        raise ValueError('TELEGRAM_APP_HASH is missing or malformed')


def decode_input(env, name):
    try:
        value = base64.b64decode(re.sub(r'\s', '', env.get(name, '')), validate=True)
    except (ValueError, binascii.Error):
        raise ValueError(name + ' is not valid base64') from None
    if not value:
        raise ValueError(name + ' is empty')
    return value


def validate_firebase(data):
    try:
        config = json.loads(data)
        matching = [c for c in config['client'] if c.get('client_info', {}).get('android_client_info', {}).get('package_name') == APP]
        if not matching or not config['project_info'].get('project_id') or not config['project_info'].get('project_number'):
            raise ValueError()
        if not any(c.get('client_info', {}).get('mobilesdk_app_id') and any(k.get('current_key') for k in c.get('api_key', [])) for c in matching):
            raise ValueError()
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError('ALPHA_FIREBASE_JSON_B64 must contain your complete Firebase Android config for the Alpha package') from None
    return config


def stage(env, root=ROOT):
    validate_api(env)
    expected = fingerprint(env.get('ALPHA_CERTIFICATE_SHA256', ''))
    for name in ['ALPHA_KEY_ALIAS', 'ALPHA_STORE_PASSWORD', 'ALPHA_KEY_PASSWORD']:
        if not env.get(name):
            raise ValueError(name + ' is missing')
    firebase = decode_input(env, 'ALPHA_FIREBASE_JSON_B64')
    firebase_config = validate_firebase(firebase)
    if env.get('GITHUB_ACTIONS') == 'true':
        # Base64 secrets are masked automatically, but their decoded API keys are not.
        for client in firebase_config['client']:
            for item in client.get('api_key', []):
                value = str(item.get('current_key', ''))
                if value:
                    escaped = value.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
                    print('::add-mask::' + escaped)
    keystore = decode_input(env, 'ALPHA_KEYSTORE_B64')
    files = [(root/'config/connected-alpha-test.keystore', keystore),
             (root/'TMessagesProj/src/connectedAlpha/google-services.json', firebase)]
    try:
        for path, data in files:
            path.parent.mkdir(parents=True, exist_ok=True)
            # umask in main prevents a window with world-readable private files.
            path.write_bytes(data)
            path.chmod(0o600)
        cert = subprocess.run(['keytool', '-exportcert', '-keystore', str(files[0][0]),
                               '-alias', env['ALPHA_KEY_ALIAS'], '-storepass:env', 'ALPHA_STORE_PASSWORD'],
                              env=dict(env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if cert.returncode or not cert.stdout:
            raise ValueError('Cannot open authorized Alpha keystore/alias with supplied password')
        if hashlib.sha256(cert.stdout).hexdigest() != expected:
            raise ValueError('Keystore certificate differs from independently authorized ALPHA_CERTIFICATE_SHA256')
        # A certificate-only alias or wrong private-key password must fail before JNI work.
        csr = subprocess.run(['keytool', '-certreq', '-keystore', str(files[0][0]),
                              '-alias', env['ALPHA_KEY_ALIAS'], '-storepass:env', 'ALPHA_STORE_PASSWORD',
                              '-keypass:env', 'ALPHA_KEY_PASSWORD'],
                             env=dict(env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if csr.returncode or not csr.stdout:
            raise ValueError('Cannot access Alpha private signing key with supplied key password')
    except Exception:
        for path, _ in files:
            path.unlink(missing_ok=True)
        raise


def main():
    os.umask(0o077)
    try:
        stage(os.environ)
    except (ValueError, OSError):
        # Never expose keytool output, JSON/base64 data, or raw environment values.
        print('::error::Private input validation failed; verify API ownership/format, Firebase package, keystore/alias/password and independent certificate fingerprint.')
        return 1
    print('Authorized input formats and signing certificate checked; no values logged.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
