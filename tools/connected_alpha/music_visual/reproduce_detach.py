#!/usr/bin/env python3
"""Require the original bubble to reproduce the owner's ViewGroup NPE in the isolated Android probe.
Run music_visual/run.py first. Never opens Telegram, accounts or a physical device.
"""
import argparse,os,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE='997ac40a65be00c672dc8009b61f55825537d498'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sdk-root',type=Path,required=True);p.add_argument('--maven',default='mvn');a=p.parse_args()
 out=ROOT/'build/connected-alpha-music-visual';folder=out/'src/test/java/app/exteraless/player';bubble=folder/'SignatureMusicBubble.java';host=folder/'SignatureMusicHost.java';original={f:f.read_bytes()for f in [bubble,host]}
 try:
  bubble.write_bytes(subprocess.check_output(['git','show',BASE+':TMessagesProj/src/main/java/app/exteraless/player/SignatureMusicBubble.java'],cwd=ROOT))
  host.write_text(host.read_text().replace('bubble.releaseFromWindow()','bubble.release()'))
  r=subprocess.run([a.maven,'-o','-B','-f',str(out/'pom.xml'),'-Dandroid.sdk.jar='+str(a.sdk_root.resolve()/'platforms/android-37.0/android.jar'),'-Pmusic-compile','-Dtest=MusicVisualTest#detachedRootKeepsStableChildArrayAndReusesDormantBubble','test'],cwd=ROOT,capture_output=True,text=True)
  text=r.stdout+r.stderr
  if r.returncode==0 or not all(s in text for s in ['NullPointerException','ViewGroup.dispatchDetachedFromWindow','children[i]']):raise RuntimeError('The old source did not reproduce the expected framework crash')
  print('PASS: original1271 bubble reproduced ViewGroup.dispatchDetachedFromWindow NPE (children[i] null). Corrected isolated suite must pass separately; Poco acceptance pending.')
 finally:
  for f,data in original.items():f.write_bytes(data)
if __name__=='__main__':main()
