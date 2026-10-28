"""Reverse exact reviewed P11 hunks before the existing P1-P10 whole-class byte proofs."""
import json
from pathlib import Path

def restore(path,content):
    patches=json.loads(Path(__file__).with_name('reveal_review.json').read_text()).get(path,[])
    for patch in patches:
        assert content.count(patch['after'])==1,'Unreviewed reveal hunk: '+path
        content=content.replace(patch['after'],patch['before'],1)
    return content
