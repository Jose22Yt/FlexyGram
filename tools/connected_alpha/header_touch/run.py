#!/usr/bin/env python3
"""Exercise production header visibility/measurement with native Android touch and popup windows.

The app's navigation/account services are not initialized. Geometry is a fixed
fixture; the Signature onMeasure entry is extracted verbatim from production.
"""
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('header_touch_pipeline', HERE.parent/'music_visual/run.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def write_stubs(source, root):
    text = (root/'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatAvatarContainer.java').read_text()
    start = text.index('protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec)')
    prefix = text[start:text.index('        if (signatureMeasured)', start)]
    (source/'ControlOwner.java').write_text('''
import android.content.Context;import android.view.*;import android.widget.*;
public class ControlOwner extends FrameLayout {
 public final ImageView signatureMore,signatureCall;
 boolean signatureMeasured,active=true;
 public ControlOwner(Context c){super(c);signatureMore=new ImageView(c);signatureCall=new ImageView(c);addView(signatureMore);addView(signatureCall);}
 private boolean signatureActive(){return active;}
 private void measureSignature(int w,int h){
  signatureMore.setVisibility(VISIBLE);signatureCall.setVisibility(VISIBLE);
  for(View v:new View[]{signatureMore,signatureCall})v.measure(MeasureSpec.makeMeasureSpec(48,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(48,MeasureSpec.EXACTLY));
  setMeasuredDimension(200,60);
 }
 @Override PREFIX super.onMeasure(widthMeasureSpec,heightMeasureSpec);}
 @Override protected void onLayout(boolean changed,int l,int t,int r,int b){signatureCall.layout(56,6,104,54);signatureMore.layout(112,6,160,54);}
}'''.replace('PREFIX',prefix))


    chat = (root/'TMessagesProj/src/main/java/org/telegram/ui/ChatActivity.java').read_text()
    start = chat.index('                if (showSearchAsIcon || showAudioCallAsIcon || UserObject.isBotForumWithEditableTopics(currentUser))')
    end = chat.index('                if (showSearchAsIcon) {', start)
    margins = chat[start:end]
    (source/'HeaderHost.java').write_text('''
import android.content.Context;import android.view.*;import android.widget.*;
public class HeaderHost extends FrameLayout {
 final FrameLayout avatarContainer;final ImageView more,call;
 boolean signature=true,centered=false,showSearchAsIcon,showAudioCallAsIcon;
 Object currentUser;int chatMode;static final int MODE_SAVED=1;
 static class UserObject{static boolean isBotForumWithEditableTopics(Object u){return false;}}
 static class AndroidUtilities{static int dp(int value){return value;}}
 boolean isTitleCentered(){return centered;}boolean usesSignatureHeader(){return signature;}
 public HeaderHost(Context c){super(c);
  avatarContainer=new FrameLayout(c);avatarContainer.setClipChildren(false);
  more=new ImageView(c);call=new ImageView(c);
  avatarContainer.addView(call,new FrameLayout.LayoutParams(48,48));avatarContainer.addView(more,new FrameLayout.LayoutParams(48,48));
  addView(avatarContainer,new FrameLayout.LayoutParams(LayoutParams.MATCH_PARENT,60));
 }
 @Override protected void onMeasure(int w,int h){MARGINS super.onMeasure(w,h);}
 @Override protected void onLayout(boolean changed,int l,int t,int r,int b){
  super.onLayout(changed,l,t,r,b);
  // Signature geometry is calculated from the full ActionBar width, not the title width.
  more.layout(getWidth()-52,6,getWidth()-4,54);call.layout(getWidth()-104,6,getWidth()-56,54);
 }
}'''.replace('MARGINS',margins))


if __name__ == '__main__':
    result = pipeline.main(here=HERE,test_class='HeaderTouchTest',stubs_writer=write_stubs)
    print('PASS: native Android header touch/popup regression; production measure entry; app navigation/device not exercised.')
    raise SystemExit(result)
