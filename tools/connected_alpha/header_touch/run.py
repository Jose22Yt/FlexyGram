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


if __name__ == '__main__':
    result = pipeline.main(here=HERE,test_class='HeaderTouchTest',stubs_writer=write_stubs)
    print('PASS: native Android header touch/popup regression; production measure entry; app navigation/device not exercised.')
    raise SystemExit(result)
