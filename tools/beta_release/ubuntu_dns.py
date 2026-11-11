#!/usr/bin/env python3
"""Bounded DNS fallback for the official Ubuntu archive on ephemeral CI runners.

Only emits IPv4 hosts entries. APT still verifies the repository signatures and
HTTPS certificates for archive.ubuntu.com; this changes no trust settings.
"""
import argparse
import ipaddress
import json
from pathlib import Path
import subprocess
import urllib.request

HOST = 'archive.ubuntu.com'
PROVIDERS = (
    'https://dns.google/resolve?name=archive.ubuntu.com&type=A',
    'https://cloudflare-dns.com/dns-query?name=archive.ubuntu.com&type=A',
)


def ipv4_answers(document):
    if not isinstance(document, dict) or document.get('Status') != 0:
        raise ValueError('DNS resolver did not return a successful answer')
    result = []
    for answer in document.get('Answer', []):
        if answer.get('type') != 1:
            continue
        address = ipaddress.IPv4Address(answer['data'])
        if not address.is_global or address.is_multicast or address.is_reserved:
            raise ValueError('DNS response contains a non-public address')
        if str(address) not in result:
            result.append(str(address))
    if not result:
        raise ValueError('DNS response contains no public IPv4 address')
    return result


def fetch_answers():
    for provider in PROVIDERS:
        try:
            request = urllib.request.Request(provider, headers={'Accept': 'application/dns-json'})
            with urllib.request.urlopen(request, timeout=12) as response:
                return ipv4_answers(json.load(response))
        except (OSError, ValueError, KeyError):
            continue
    raise RuntimeError('Unable to resolve the official Ubuntu archive through HTTPS DNS')


def prepare(output, resolver=None, fetch=None):
    resolver = resolver or subprocess.run
    fetch = fetch or fetch_answers
    output = Path(output)
    # Always replace the temporary output so rerunning cannot append stale entries.
    output.write_text('')
    try:
        result = resolver(['getent', 'ahostsv4', HOST], capture_output=True, text=True, timeout=6)
        if result.returncode == 0 and result.stdout.strip():
            print('Ubuntu archive: system DNS is available')
            return
    except (OSError, subprocess.TimeoutExpired):
        pass
    addresses = fetch()
    # Validate again at the boundary which writes the hosts fragment.
    addresses = ipv4_answers({'Status': 0, 'Answer': [{'type': 1, 'data': value} for value in addresses]})
    output.write_text(''.join(f'{address} {HOST}\n' for address in addresses))
    print('Ubuntu archive: HTTPS DNS fallback prepared for the official hostname')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--hosts-file', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.hosts_file)
