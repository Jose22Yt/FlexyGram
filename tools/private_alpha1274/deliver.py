#!/usr/bin/env python3
"""Verified, unpublished GitHub draft delivery. Never publishes a release."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import urllib.error
import urllib.parse
import urllib.request

REPO = 'Jose22Yt/FlexyGram'
SOURCE = 'd659b062d6a591e4a2b2f7900ab884a363aeae07'
CERT = 'c8f04cad685ca5757d35b25ea4b0b4613c7399909948d821e6ada61f9fb12b2c'
APP = 'io.github.jose22yt.flexygram.alpha'
NAME = 'FlexyGram_Alpha_1285_ARM64_TEST.apk'
API = 'https://api.github.com/repos/' + REPO


class DeliveryError(Exception):
    pass


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def digest(stream):
    h = hashlib.sha256()
    size = 0
    while chunk := stream.read(1024 * 1024):
        h.update(chunk)
        size += len(chunk)
    return h.hexdigest(), size


class Client:
    def __init__(self):
        self.token = os.environ.get('GH_TOKEN', '')
        if not self.token or os.environ.get('GITHUB_REPOSITORY') != REPO:
            raise DeliveryError('Authorized repository token required')
        self.opener = urllib.request.build_opener(NoRedirect())

    def request(self, url, *, method='GET', data=None, accept='application/vnd.github+json', authenticated=True, content_type=None, size=None):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'https' or parsed.username or parsed.password:
            raise DeliveryError('Invalid delivery transport')
        if authenticated and parsed.hostname not in {'api.github.com', 'uploads.github.com'}:
            raise DeliveryError('Refusing to send repository credentials to another host')
        headers = {'Accept': accept, 'User-Agent': 'FlexyGram-private-delivery', 'X-GitHub-Api-Version': '2022-11-28'}
        if authenticated:
            headers['Authorization'] = 'Bearer ' + self.token
        if content_type:
            headers['Content-Type'] = content_type
        if size is not None:
            headers['Content-Length'] = str(size)
        req = urllib.request.Request(url, method=method, data=data, headers=headers)
        try:
            return self.opener.open(req, timeout=120)
        except urllib.error.HTTPError as response:
            return response

    def json(self, path, *, method='GET', data=None):
        body = None if data is None else json.dumps(data).encode()
        with self.request(API + path, method=method, data=body, content_type='application/json' if body else None) as r:
            if r.status not in {200, 201, 204}:
                raise DeliveryError('GitHub delivery API rejected ' + method + ' (HTTP ' + str(r.status) + ')')
            return json.loads(r.read(1024 * 1024)) if r.status != 204 else None

    def draft(self, release_id):
        release = self.json('/releases/' + str(int(release_id)))
        if release.get('draft') is not True or release.get('published_at') is not None or release.get('target_commitish') != SOURCE:
            raise DeliveryError('Delivery destination must remain an unpublished draft of the approved source')
        return release

    def private_asset(self, release_id, asset):
        self.draft(release_id)
        direct = asset['browser_download_url']
        parsed = urllib.parse.urlsplit(direct)
        if parsed.scheme != 'https' or parsed.netloc != 'github.com' or not parsed.path.startswith('/' + REPO + '/releases/download/') or parsed.query or parsed.fragment:
            raise DeliveryError('Unexpected browser download endpoint')
        for url in (API + '/releases/assets/' + str(int(asset['id'])), direct):
            with self.request(url, authenticated=False, accept='application/octet-stream') as response:
                # A redirect is also a failure: it could grant unauthenticated access.
                if response.status not in {401, 404}:
                    self.json('/releases/assets/' + str(int(asset['id'])), method='DELETE')
                    raise DeliveryError('Anonymous download was not denied; asset removed')

    def download_hash(self, asset):
        response = self.request(API + '/releases/assets/' + str(int(asset['id'])), accept='application/octet-stream')
        if response.status in {301, 302, 303, 307, 308}:
            location = response.headers.get('Location', '')
            response.close()
            p = urllib.parse.urlsplit(location)
            if p.scheme != 'https' or p.netloc not in {'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}:
                raise DeliveryError('Unexpected authenticated storage redirect')
            # The presigned URL is transient and never printed. No repository token
            # follows the redirect, even to GitHub's storage service.
            response = self.request(location, authenticated=False, accept='application/octet-stream')
        with response:
            if response.status != 200:
                raise DeliveryError('Authenticated download failed (HTTP ' + str(response.status) + ')')
            return digest(response)

    def upload(self, release_id, path, name):
        self.draft(release_id)
        url = 'https://uploads.github.com/repos/' + REPO + '/releases/' + str(int(release_id)) + '/assets?name=' + urllib.parse.quote(name, safe='')
        with path.open('rb') as f, self.request(url, method='POST', data=f, content_type='application/octet-stream', size=path.stat().st_size) as r:
            if r.status != 201:
                raise DeliveryError('Private asset upload failed (HTTP ' + str(r.status) + ')')
            asset = json.loads(r.read(1024 * 1024))
        if asset.get('state') != 'uploaded' or asset.get('name') != name or asset.get('size') != path.stat().st_size:
            raise DeliveryError('Private upload metadata differs')
        self.private_asset(release_id, asset)
        with path.open('rb') as f:
            expected = digest(f)
        if self.download_hash(asset) != expected:
            raise DeliveryError('Private download hash/size differs from the uploaded file')
        self.draft(release_id)
        return asset


def validate(report, apk):
    expected = {'commit': SOURCE, 'application_id': APP, 'version_code': 1285, 'certificate_sha256': CERT, 'elf_count': 96, 'status': 'PASS_ARTIFACT_ONLY'}
    if any(report.get(k) != v for k, v in expected.items()):
        raise DeliveryError('Full approved APK verification report required')
    with apk.open('rb') as f:
        actual = digest(f)
    if actual != (report.get('sha256'), report.get('bytes')):
        raise DeliveryError('APK bytes differ from the verifier report')
    return actual


def preflight(client, directory):
    # No APK is uploaded until this same destination has passed an actual
    # authenticated roundtrip and two independent anonymous denial checks.
    run = os.environ['GITHUB_RUN_ID'] + '-' + os.environ['GITHUB_RUN_ATTEMPT']
    release = client.json('/releases', method='POST', data={
        'tag_name': 'alpha1285-universal-private-' + run,
        'target_commitish': SOURCE,
        'name': 'FlexyGram Alpha 1285 Signature iOS27 — PRIVATE TEST ' + run,
        'body': 'PRIVATE UNPUBLISHED TEST DELIVERY. Keep draft. Approved source: ' + SOURCE + '. No APK transferred yet.',
        'draft': True, 'prerelease': True, 'make_latest': 'false'})
    rid = int(release['id'])
    client.draft(rid)
    probe = directory / 'private-destination-probe.txt'
    probe.write_text(secrets.token_hex(32))
    asset = client.upload(rid, probe, probe.name)
    client.json('/releases/assets/' + str(int(asset['id'])), method='DELETE')
    probe.unlink()
    with open(os.environ['GITHUB_OUTPUT'], 'a') as out:
        out.write('release_id=' + str(rid) + '\n')
    print('PRIVATE_DESTINATION_READY ' + json.dumps({'release_id': rid, 'draft': True, 'authenticated_roundtrip': 'PASS', 'anonymous_api_and_browser': 'DENIED'}))


def deliver(client, rid, apk, report_path):
    report = json.loads(report_path.read_text())
    sha, size = validate(report, apk)
    release = client.draft(rid)
    # Preserve the verifier evidence privately too. If the network fails after an
    # upload, the unpublished assets survive runner cleanup and can be rechecked.
    client.upload(rid, report_path, 'FlexyGram_Alpha_1285_verificacion.json')
    asset = client.upload(rid, apk, NAME)
    proof = dict(source_commit=SOURCE, sha256=sha, bytes=size, release_id=rid, asset_id=asset['id'],
                 private_download_url=asset['browser_download_url'], draft_url=release['html_url'],
                 draft=True, authenticated_download='PASS', anonymous_download='DENIED')
    client.json('/releases/' + str(rid), method='PATCH', data={'draft': True, 'body': 'PRIVATE TEST. DO NOT PUBLISH.\n\n' + json.dumps(proof, indent=2)})
    client.private_asset(rid, asset)
    client.draft(rid)
    print('PRIVATE_APK_DELIVERED ' + json.dumps(proof, sort_keys=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode', choices=['preflight', 'deliver'])
    p.add_argument('--release-id', type=int)
    p.add_argument('--apk', type=Path)
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    client = Client()
    if args.mode == 'preflight':
        preflight(client, Path(os.environ['RUNNER_TEMP']))
    else:
        if not args.release_id or not args.apk or not args.report:
            raise DeliveryError('Verified APK, report and private destination required')
        deliver(client, args.release_id, args.apk, args.report)


if __name__ == '__main__':
    try:
        main()
    except DeliveryError as failure:
        raise SystemExit('Private delivery: '+str(failure))
    except (OSError, ValueError, KeyError):
        raise SystemExit('Private delivery failed. No release is published and no APK is uploaded as an Actions artifact.')

