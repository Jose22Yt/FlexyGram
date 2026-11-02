#!/usr/bin/env python3
"""Real Android clickable overlay regression; no full app/device claim.

Run music_visual/run.py first, to build the existing pinned Robolectric environment.
The only application code extracted here is the actual Dialogs cleanup callback.
"""
import argparse,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'tools/connected_alpha'))
from test_preview_input1273 import body

p=argparse.ArgumentParser();p.add_argument('--sdk-root',type=Path,required=True);p.add_argument('--maven',default='mvn');args=p.parse_args()
output=ROOT/'build/connected-alpha-music-visual'
if not (output/'target/aar/monitor.jar').exists():raise SystemExit('Run music_visual probe first; framework dependencies required')
source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/DialogsActivity.java').read_text()
methods=body(source,'public void onParentBecomeFullyVisible()')+body(source,'private void clearClosedPreviewOverlay()')
template=(Path(__file__).parent/'PreviewInputAndroidTest.java.in').read_text()
(output/'src/test/java/PreviewInputAndroidTest.java').write_text(template.replace('_METHODS_',methods))
subprocess.run([args.maven,'-o','-B','-f',str(output/'pom.xml'),'-Pmusic-compile','-Dandroid.sdk.jar='+str(args.sdk_root.resolve()/'platforms/android-37.0/android.jar'),'-Dtest=PreviewInputAndroidTest','test'],check=True)
print('PASS isolated Android API35 overlay input; navigation owner is a double; Poco acceptance PENDING')
