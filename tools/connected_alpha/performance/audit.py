#!/usr/bin/env python3
"""Hash-only reference inventory and explicit reviewed findings; no secrets or device access."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from .contract import ROOT,BASE,RESERVED
ORIGINAL='1ad6a60a6834ffca722b1a22f4fba27ecb29a061'
FILES=(
 'org/telegram/messenger/ApplicationLoader.java', 'org/telegram/messenger/NativeLoader.java',
 'org/telegram/ui/LaunchActivity.java', 'org/telegram/ui/ChatActivity.java',
 'org/telegram/ui/DialogsActivity.java', 'org/telegram/ui/Cells/DialogCell.java',
 'org/telegram/ui/Cells/ChatMessageCell.java', 'org/telegram/ui/ActionBar/MessageDrawable.java',
 'org/telegram/ui/ActionBar/ActionBarLayout.java', 'org/telegram/ui/Components/FilterTabsView.java',
 'org/telegram/messenger/NotificationCenter.java', 'org/telegram/messenger/ImageLoader.java',
 'org/telegram/messenger/ImageReceiver.java', 'org/telegram/messenger/DispatchQueue.java',
 'org/telegram/messenger/MediaController.java', 'org/telegram/messenger/MusicPlayerService.java',
 'app/exteraless/plugins/PluginsController.java','app/exteraless/plugins/PythonPluginsEngine.java',
 'app/exteraless/player/LyricsFill.java','app/exteraless/player/LyricsView.java','app/exteraless/player/PlayerArt.java',
 'app/exteraless/player/PlayerColors.java','app/exteraless/player/RingPlayButton.java',
 'app/exteraless/player/WavySeekBar.java','app/exteraless/player/PlayerMiniView.java',
 'app/exteraless/player/SignatureMusicBubble.java',
)


def snapshot():
    for ref in (ORIGINAL,BASE):
        subprocess.run(["git","cat-file","-e",ref+"^{commit}"],cwd=ROOT,check=True,capture_output=True)
    rows=[]
    for name in FILES:
        path='TMessagesProj/src/main/java/'+name
        row={'path':path,'reserved':Path(path).name in RESERVED}
        for label,ref in [('exteraless',ORIGINAL),('alpha1271',BASE)]:
            result=subprocess.run(['git','show',ref+':'+path],cwd=ROOT,capture_output=True)
            row[label+'_sha256']=hashlib.sha256(result.stdout).hexdigest() if result.returncode==0 else None
        row['candidate_sha256']=hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
        row['candidate_changed']=row['candidate_sha256']!=row['alpha1271_sha256']
        rows.append(row)
    return {'evidence':'source_inventory_only','base':BASE,'original':ORIGINAL,
            'rows':rows,'physical_metrics':None,'superiority':'NOT_ESTABLISHED'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(snapshot(),indent=2)+'\n')
if __name__=='__main__':main()
