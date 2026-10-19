"""Executable DESIGN ONLY. Not imported, packaged or trusted by the Android app.

No SDK/network/account/credential handling. Grants below are synthetic snapshots
of a future trusted resolver's output, not evidence of ownership or a user toggle.
"""
from dataclasses import dataclass, field
from enum import Enum
import re
from urllib.parse import urlsplit


class Provider(str, Enum):
    OWN_OFFICIAL = 'own_official'
    TELEGRAM = 'telegram_official'
    LOCAL = 'local_optional'
    LEGACY_LOCAL = 'legacy_google_local'
    LEGACY_LIBRARY = 'legacy_google_library'
    LEGACY_WEB = 'legacy_google_web'


@dataclass(frozen=True)
class Context:
    isolated: bool = True
    android_id: str = 'io.github.jose22yt.flexygram.diagnostic'
    scope: str = ''
    now: int = 0
    network_permitted: bool = False
    telegram_session_authorized: bool = False


@dataclass(frozen=True)
class Grant:
    provider: Provider
    android_id: str
    scope: str
    expires_at: int
    rights_verified: bool = False
    features: frozenset = frozenset()
    endpoint: str = field(default='', repr=False)
    approved_endpoint: str = field(default='', repr=False)
    model_installed: bool = False


@dataclass(frozen=True)
class Request:
    requested: Provider
    effective: Provider
    feature: str = 'text'
    # Represents a future explicit, scoped selection record, NOT a blanket fallback.
    selected_scope: str = ''
    text: str = field(default='', repr=False)
    entities: tuple = field(default=(), repr=False)


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class Outcome:
    reason: str
    value: object = field(default=None, repr=False)


def authorize(context, request, grant):
    """Deny by default, including direct calls and unavailable feature mappings."""
    deny = lambda reason: Decision(False, reason)
    if context.isolated:
        return deny('diagnostic_denied')
    if request.effective not in (Provider.OWN_OFFICIAL, Provider.TELEGRAM, Provider.LOCAL):
        return deny('provider_not_authorized')
    if (not re.fullmatch(r'io\.github\.jose22yt\.flexygram\.[a-z][a-z0-9_.]*', context.android_id)
            or context.android_id.endswith('.diagnostic')):
        return deny('identity_denied')
    if (grant is None or grant.provider != request.effective or not grant.rights_verified
            or grant.android_id != context.android_id):
        return deny('grant_required')
    if (not re.fullmatch(r'[a-f0-9]{64}', context.scope)
            or grant.scope != context.scope or context.now <= 0
            or grant.expires_at <= context.now):
        return deny('grant_stale')
    if request.feature not in grant.features:
        return deny('capability_unavailable')
    if request.requested != request.effective and request.selected_scope != context.scope:
        return deny('provider_switch_denied')
    if request.effective in (Provider.OWN_OFFICIAL, Provider.TELEGRAM):
        if not context.network_permitted:
            return deny('network_denied')
    if request.effective == Provider.OWN_OFFICIAL:
        try:
            endpoint = urlsplit(grant.endpoint)
            if (grant.endpoint != grant.approved_endpoint or endpoint.scheme != 'https'
                    or not endpoint.hostname or endpoint.username or endpoint.password
                    or endpoint.query or endpoint.fragment or endpoint.port not in (None, 443)
                    or endpoint.hostname in ('translate-pa.googleapis.com', 'translate.google.com')):
                return deny('endpoint_denied')
        except ValueError:
            return deny('endpoint_denied')
    if request.effective == Provider.TELEGRAM and not context.telegram_session_authorized:
        return deny('session_denied')
    if request.effective == Provider.LOCAL and not grant.model_installed:
        return deny('model_unavailable')  # Never downloads or falls back itself.
    return Decision(True, 'authorized')


def dispatch(context_at_execution, request, grant, adapter):
    """Fake-adapter harness only. Re-evaluates at execution, never retries/falls back.

    A real implementation must obtain/recheck a fresh grant too; this supplied
    immutable grant becomes unusable when context scope/expiry changes.
    """
    decision = authorize(context_at_execution(), request, grant)
    if not decision.allowed:
        return Outcome(decision.reason)
    try:
        return Outcome('completed', adapter(request))
    except Exception:
        return Outcome('provider_failed')  # No exception/body/URL/token propagation.
