"""Protect the packaged glyphs and touch lifecycle selected by the user."""
import hashlib

from test_render_work_reuse import JAVA
from test_composer_layout import method


def test_original_composer_artwork_matches_pre_change_resources():
    # Original resources at 6342e1d46; do not require history in shallow CI checkouts.
    expected = {
        'flexy_composer_clip.xml': '3e9af4c1fc36cdd32dc7ed1d8c8ed3f9dd91bdc25b3d5f895706af04a72f8086',
        'flexy_composer_voice.xml': '2bde1db52d7b3b7b11ac48be095c4329bb016cff8ae7317eedd20e4c6b4abb22',
        'flexy_composer_folded.xml': '6c56dbd4f830395b83d9fe2b9b5aac5d9bf3ded64a9e8a38a9a47c9775c409c4',
    }
    for name, digest in expected.items():
        assert hashlib.sha256((JAVA.parent/'res/drawable'/name).read_bytes()).hexdigest() == digest, name


def test_active_header_does_not_hide_controls_before_measure():
    source = (JAVA/'org/telegram/ui/Components/ChatAvatarContainer.java').read_text()
    measure = method(source, 'protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec)')
    active = measure.index('if (signatureActive())')
    assert active < measure.index('signatureMore.setVisibility(GONE)')
    assert active < measure.index('signatureCall.setVisibility(GONE)')
    controls = method(source, 'private void prepareFusionControls()')
    assert 'loadBitmap(getContext(),R.drawable.ic_ab_other)' in controls
    assert 'loadBitmap(getContext(),R.drawable.msg_callback)' in controls
    assert 'signatureMore.setRotation(90)' in controls
