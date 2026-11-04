from pathlib import Path

def write(dest,root):
 java=root/'TMessagesProj/src/main/java'
 for name in ['FastMotion','FastMotionTiming']:
  p=dest/'app/flexygram/animation'/(name+'.java');p.parent.mkdir(parents=True,exist_ok=True);p.write_text((java/'app/flexygram/animation'/(name+'.java')).read_text())
 p=dest/'org/telegram/messenger/ApplicationLoader.java';p.parent.mkdir(parents=True,exist_ok=True);p.write_text('package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext;}')
