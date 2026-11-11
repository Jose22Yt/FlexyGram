#!/usr/bin/env python3
"""Type-check production motion against a real Android SDK jar; no APK."""
import argparse,pathlib,subprocess,tempfile
ROOT=pathlib.Path(__file__).resolve().parents[2]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--android-jar',type=pathlib.Path,required=True);args=p.parse_args()
 with tempfile.TemporaryDirectory(prefix='bubble-motion-types-')as tmp:
  tmp=pathlib.Path(tmp);stub=tmp/'app/flexygram/bubbles/interaction/BubbleInteractionSettings.java';stub.parent.mkdir(parents=True)
  stub.write_text('package app.flexygram.bubbles.interaction;public class BubbleInteractionSettings{public static boolean motionEnabled(){return true;}}')
  names=['app/exteraless/player/Spring','app/flexygram/bubbles/interaction/SelectedBubbleMotion','app/flexygram/bubbles/interaction/BubbleTapMotion','app/flexygram/bubbles/interaction/DampedSpringCurve']
  subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',str(args.android_jar),'-d',str(tmp/'classes'),str(stub),*map(str,(ROOT/'TMessagesProj/src/main/java'/(n+'.java')for n in names))],check=True)
 print('Four production motion classes passed against the supplied Android SDK; application preference gate is a double. No APK.')
