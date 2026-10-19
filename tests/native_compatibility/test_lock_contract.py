"""Offline regressions for P0.4c's pinned Python requirements contract.

No wheel downloads, pip execution, Android build or network access.
"""
import copy
import json
import re
import unittest
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]


def canonical(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def require(condition, message='Invalid lock contract'):
    """Enforce checks even when Python is run with optimization (-O)."""
    if not condition:
        raise AssertionError(message)


def check_contract(lock, requirements):
    """Check equality between declared requirement hashes and ABI-specific wheel set."""
    require(lock['schema'] == 1 and lock['python'] == '3.11')
    require(sorted(lock['abis']) == ['arm64-v8a', 'x86_64'])
    reqs = {}
    for line in requirements.replace('\\\n', ' ').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s]+)((?:\s+--hash=sha256:[a-f0-9]{64})+)', line)
        require(match, 'Unexpected pip requirement syntax')
        name, version = canonical(match[1]), match[2]
        require(name not in reqs, 'Duplicate requirement')
        reqs[name] = (version, set(re.findall(r'--hash=sha256:([a-f0-9]{64})', match[3])))
    packages, filenames = set(), set()
    abi_counts = {abi: 0 for abi in lock['abis']}
    for package in lock['packages']:
        name = canonical(package['name'])
        require(name not in packages, 'Duplicate locked package')
        packages.add(name)
        require(name in reqs and reqs[name][0] == package['version'], 'Version mismatch')
        expected_hashes = set()
        require(package['files'], 'Empty wheel list')
        for row in package['files']:
            filename, digest = row['filename'], row['sha256']
            require(filename == Path(filename).name and filename.endswith('.whl'), 'Unsafe wheel filename')
            require(filename not in filenames, 'Duplicate wheel file')
            filenames.add(filename)
            require(re.fullmatch(r'[a-f0-9]{64}', digest), 'Malformed digest')
            expected_hashes.add(digest)
            parsed = urlsplit(row['url'])
            require(parsed.scheme == 'https' and not parsed.query and not parsed.fragment)
            require((parsed.netloc == 'files.pythonhosted.org') or
                    (parsed.netloc == 'chaquo.com' and parsed.path.startswith('/pypi-13.1/')), 'Unexpected wheel origin')
            require(parsed.path.endswith('/' + filename), 'Filename does not match origin')
        require(reqs[name][1] == expected_hashes, 'Lock/requirements hashes differ')
        for abi in lock['abis']:
            tag = abi.replace('-', '_')
            matched = [f for f in package['files']
                       if f['filename'].endswith('-any.whl') or f['filename'].endswith('_' + tag + '.whl')]
            require(len(matched) == 1, 'Package has missing or ambiguous wheel for ' + abi)
            abi_counts[abi] += 1
    require(set(reqs) == packages, 'Unlisted or missing requirement')
    return {'packages': len(packages), 'wheel_files': len(filenames), 'abi_counts': abi_counts}


def sample():
    packages = []
    lines = []
    for name, digest in [('samplea', 'a' * 64), ('sampleb', 'b' * 64)]:
        filename = name + '-1.0-py3-none-any.whl'
        packages.append({'name': name, 'version': '1.0', 'files': [
            {'filename': filename, 'url': 'https://files.pythonhosted.org/example/' + filename,
             'sha256': digest}]})
        lines.append(name + '==1.0 --hash=sha256:' + digest)
    return {'schema': 1, 'python': '3.11', 'abis': ['arm64-v8a', 'x86_64'],
            'packages': packages}, '\n'.join(lines)


class LockContractTests(unittest.TestCase):
    def test_synthetic_valid(self):
        lock, reqs = sample()
        self.assertEqual(check_contract(lock, reqs),
                         {'packages': 2, 'wheel_files': 2, 'abi_counts': {'arm64-v8a': 2, 'x86_64': 2}})

    def test_mismatched_digest_fails(self):
        lock, reqs = sample()
        lock['packages'][0]['files'][0]['sha256'] = 'c' * 64
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_undeclared_package_fails(self):
        lock, reqs = sample()
        with self.assertRaises(AssertionError): check_contract(lock, reqs.splitlines()[0])

    def test_duplicate_package_fails(self):
        lock, reqs = sample()
        lock['packages'].append(copy.deepcopy(lock['packages'][0]))
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_duplicate_filename_fails(self):
        lock, reqs = sample()
        lock['packages'][0]['files'].append(copy.deepcopy(lock['packages'][0]['files'][0]))
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_unapproved_origin_fails(self):
        lock, reqs = sample()
        lock['packages'][0]['files'][0]['url'] = 'https://chaquo.com.attacker.invalid/pypi-13.1/' + lock['packages'][0]['files'][0]['filename']
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_path_traversal_fails(self):
        lock, reqs = sample()
        lock['packages'][0]['files'][0]['filename'] = '../unsafe.whl'
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_unpinned_syntax_fails(self):
        lock, reqs = sample()
        with self.assertRaises(AssertionError): check_contract(lock, reqs + '\nother>=1')

    def test_unsupported_abi_fails(self):
        lock, reqs = sample()
        lock['abis'].append('armeabi-v7a')
        with self.assertRaises(AssertionError): check_contract(lock, reqs)

    def test_real_repository_lock(self):
        paths = [ROOT/'TMessagesProj/python/wheels.lock.json', ROOT/'TMessagesProj/python/requirements.lock']
        if not all(path.is_file() for path in paths):
            self.skipTest('Full repository checkout is unavailable in this test environment')
        actual = check_contract(json.loads(paths[0].read_text()), paths[1].read_text())
        self.assertEqual(actual, {'packages': 18, 'wheel_files': 26,
                                  'abi_counts': {'arm64-v8a': 18, 'x86_64': 18}})


if __name__ == '__main__':
    unittest.main()
