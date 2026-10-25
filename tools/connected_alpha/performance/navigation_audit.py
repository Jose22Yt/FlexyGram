#!/usr/bin/env python3
"""Hash-only source lineage and reserved-file check, not a runtime profiler."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from .navigation_contract import BASE,ALPHA1272,ROOT,PRODUCTION,reserved

FILES=[
 'org/telegram/messenger/ApplicationLoader.java','org/telegram/messenger/DispatchQueue.java',
 'org/telegram/messenger/NotificationCenter.java','org/telegram/messenger/ImageLoader.java',
 'org/telegram/messenger/ImageReceiver.java','org/telegram/ui/LaunchActivity.java',
 'org/telegram/ui/DialogsActivity.java','org/telegram/ui/ChatActivity.java',
 'org/telegram/ui/Cells/DialogCell.java','org/telegram/ui/Cells/ChatMessageCell.java',
 'org/telegram/ui/Components/RecyclerListView.java','org/telegram/ui/Components/AvatarDrawable.java',
 'org/telegram/ui/Components/AnimatedEmojiDrawable.java','org/telegram/ui/Components/BackupImageView.java',
 'org/telegram/ui/Adapters/DialogsAdapter.java','org/telegram/ui/Components/FilterTabsView.java',
 'org/telegram/DispatchQueuePriority.java','org/telegram/ui/ActionBar/ActionBarLayout.java']

def audit():
    versions={'exteraless':'1ad6a60a6834ffca722b1a22f4fba27ecb29a061','alpha1272':ALPHA1272,'pr92':BASE}
    files={}
    for relative in FILES:
        path='TMessagesProj/src/main/java/'+relative
        hashes={}
        for label,sha in versions.items():
            data=subprocess.check_output(['git','show',sha+':'+path],cwd=ROOT)
            hashes[label]=hashlib.sha256(data).hexdigest()
        hashes['candidate']=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        files[path]=hashes
    protected=reserved()
    for path in protected:
        expected=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
        if (ROOT/path).read_bytes()!=expected:raise ValueError('Reserved Work1 file changed: '+path)
    return {'evidence':'source_hashes_not_runtime_measurement','base':BASE,'files':files,
            'production_candidate':sorted(PRODUCTION),'reserved_byte_identical_count':len(protected),
            'physical_navigation_ms':None,'physical_scroll_ms':None,'superiority':'NOT_ESTABLISHED'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(audit(),indent=2)+'\n')
