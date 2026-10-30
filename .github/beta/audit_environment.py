#!/usr/bin/env python3
"""Fail closed on unreadable/drifted protection. No signing secret is accepted here."""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = 'aeb6b5fc01f6332ab82194e311b52a19d702a81e'
REPO = 'Jose22Yt/FlexyGram'


def require(condition, code):
    if not condition:
        raise ValueError(code)


def provenance(env):
    require(env.get('GITHUB_REPOSITORY') == REPO, 'WRONG_REPOSITORY')
    require(env.get('GITHUB_EVENT_NAME') == 'workflow_dispatch', 'MANUAL_ONLY')
    require(env.get('GITHUB_REF') == 'refs/heads/main', 'MAIN_DISPATCH_ONLY')
    sha = env.get('GITHUB_SHA', '')
    require(re.fullmatch('[0-9a-f]{40}', sha), 'INVALID_DISPATCH_SHA')
    require(env.get('GITHUB_WORKFLOW_SHA') == sha, 'WORKFLOW_COMMIT_MISMATCH')
    require(env.get('GITHUB_WORKFLOW_REF') == REPO+'/.github/workflows/beta-private.yml@refs/heads/main',
            'WRONG_WORKFLOW')


def validate(policy, environment, branches, main):
    require(policy['source_commit'] == SOURCE and policy['repository'] == REPO
            and policy['dispatch_branch'] == 'main' and policy['environment'] == 'flexygram-beta', 'POLICY_IDENTITY')
    require(type(policy['environment_id']) is int and policy['environment_id'] > 0
            and environment['id'] == policy['environment_id'], 'ENVIRONMENT_ID_UNREVIEWED_OR_CHANGED')
    require(environment['name'] == 'flexygram-beta', 'ENVIRONMENT_NAME')
    require(environment.get('can_admins_bypass') is False, 'ADMIN_BYPASS_MUST_BE_DISABLED')
    rules = [r for r in environment.get('protection_rules', []) if r.get('type') == 'required_reviewers']
    require(len(rules) == 1 and rules[0].get('prevent_self_review') is True, 'REVIEW_AND_SELF_REVIEW_REQUIRED')
    require(all(r.get('type') == 'User' and r.get('reviewer', {}).get('type') == 'User'
                for r in rules[0].get('reviewers', [])), 'INDIVIDUAL_USER_REVIEWERS_REQUIRED')
    reviewers = sorted(r['reviewer']['id'] for r in rules[0].get('reviewers', []))
    require(reviewers and reviewers == sorted(policy['reviewer_ids']), 'REVIEWERS_UNREVIEWED_OR_CHANGED')
    require(environment.get('deployment_branch_policy') == {'protected_branches': False, 'custom_branch_policies': True},
            'CUSTOM_MAIN_BRANCH_REQUIRED')
    require(branches.get('total_count') == 1 and len(branches.get('branch_policies', [])) == 1,
            'ONLY_ONE_DEPLOYMENT_BRANCH')
    branch = branches['branch_policies'][0]
    require(branch.get('name') == 'main' and branch.get('type') == 'branch', 'MAIN_BRANCH_ONLY_NO_TAGS')
    require(main.get('name') == 'main' and main.get('protected') is True, 'MAIN_NOT_PROTECTED')
    ui = policy['ui_review']
    for flag in ['confirmed', 'admin_bypass_disabled', 'main_requires_pull_request_and_approval',
                 'main_blocks_force_push_and_deletion', 'main_applies_to_administrators']:
        require(ui.get(flag) is True, 'UI_PROTECTIONS_NOT_ATTESTED')
    require(isinstance(ui.get('reviewed_by'), str) and ui['reviewed_by'].strip()
            and re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', ui.get('reviewed_at') or ''),
            'UI_REVIEW_IDENTITY_REQUIRED')
    require(re.fullmatch(r'age1[0-9a-z]{58}', ui.get('delivery_age_recipient') or ''), 'REVIEWED_AGE_RECIPIENT_REQUIRED')
    return {'status': 'PASS_API_AND_RECORDED_UI_REVIEW', 'source_commit': SOURCE,
            'environment_id': environment['id'], 'reviewer_ids': reviewers,
            'private_input_scope': 'VERIFIED_FOR_BUILD' if ui.get('only_environment_scoped_beta_secrets') is True
                                   else 'PENDING_POST_AUDIT; BUILD_BLOCKED',
            'limitation': 'Detailed main rules require owner UI review; signing inputs are checked after this no-secret audit.'}


def get(tail):
    token = os.environ.get('GH_TOKEN')
    headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'FlexyGram-Beta-audit',
               'X-GitHub-Api-Version': '2022-11-28'}
    if token:
        headers['Authorization'] = 'Bearer '+token
    request = urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+tail, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def main():
    try:
        if '--owner-check' not in sys.argv:
            provenance(os.environ)
        policy = json.loads((ROOT/'policy.json').read_text())
        report = validate(policy, get('environments/flexygram-beta'),
                          get('environments/flexygram-beta/deployment-branch-policies?per_page=100'),
                          get('branches/main'))
        print(json.dumps(report, indent=2))
    except Exception:
        # No HTTP response body, token, traceback or external values go into logs.
        print('BLOCKED: environment unavailable, protection drift, or pending owner UI review.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
