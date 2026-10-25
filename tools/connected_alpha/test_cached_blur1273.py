"""Execute the native static-image eligibility gate with explicit receiver data doubles."""
import subprocess,tempfile,unittest
from pathlib import Path
from test_preview_input1273 import body
from next_alpha_contract import ROOT
class CachedWallpaper(unittest.TestCase):
 def test_native_receiver_gate_rejects_moving_rotated_mirrored_and_incomplete_sources(self):
  source=(ROOT/'TMessagesProj/src/main/java/org/telegram/ui/ChatBackgroundDrawable.java').read_text()
  method=body(source,'public Bitmap getSignatureStaticBitmap(')
  fixture='''public class StaticSourceProbe {
 static class Bitmap{boolean recycled;boolean isRecycled(){return recycled;}}
 static class Drawable{}static class BitmapDrawable extends Drawable{Bitmap bitmap=new Bitmap();Bitmap getBitmap(){return bitmap;}}
 static class Settings{boolean motion;}static class Wallpaper{Settings settings=new Settings();}
 static class Receiver{boolean loaded=true;float alpha=1;int orientation,invert;Drawable drawable=new BitmapDrawable();android.graphics.RectF region=new android.graphics.RectF();boolean hasImageLoaded(){return loaded;}float getCurrentAlpha(){return alpha;}int getOrientation(){return orientation;}int getInvert(){return invert;}Drawable getDrawable(){return drawable;}android.graphics.RectF getDrawRegion(){return region;}}
 Object motionBackgroundDrawable;boolean isPattern;int alpha=255;Wallpaper wallpaper=new Wallpaper();Receiver imageReceiver=new Receiver();METHOD
 static void check(boolean b){if(!b)throw new AssertionError("unsafe native wallpaper eligibility");}
 public static void main(String[]args){StaticSourceProbe p=new StaticSourceProbe();android.graphics.RectF region=new android.graphics.RectF();check(p.getSignatureStaticBitmap(region)!=null);check(region.copied==p.imageReceiver.region);
 p.imageReceiver.loaded=false;check(p.getSignatureStaticBitmap(region)==null);p.imageReceiver.loaded=true;
 p.imageReceiver.alpha=.5f;check(p.getSignatureStaticBitmap(region)==null);p.imageReceiver.alpha=1;
 p.imageReceiver.orientation=90;check(p.getSignatureStaticBitmap(region)==null);p.imageReceiver.orientation=0;
 p.imageReceiver.invert=1;check(p.getSignatureStaticBitmap(region)==null);p.imageReceiver.invert=0;
 p.wallpaper.settings.motion=true;check(p.getSignatureStaticBitmap(region)==null);p.wallpaper.settings.motion=false;
 p.isPattern=true;check(p.getSignatureStaticBitmap(region)==null);p.isPattern=false;
 p.motionBackgroundDrawable=new Object();check(p.getSignatureStaticBitmap(region)==null);p.motionBackgroundDrawable=null;
 p.alpha=100;check(p.getSignatureStaticBitmap(region)==null);p.alpha=255;
 ((BitmapDrawable)p.imageReceiver.drawable).bitmap.recycled=true;check(p.getSignatureStaticBitmap(region)==null);
 }}'''.replace('METHOD',method)
  with tempfile.TemporaryDirectory()as tmp:
   java=Path(tmp)/'StaticSourceProbe.java';java.write_text(fixture)
   rect=Path(tmp)/'android/graphics/RectF.java';rect.parent.mkdir(parents=True);rect.write_text('package android.graphics;public class RectF{public RectF copied;public void set(RectF r){copied=r;}}')
   anim=Path(tmp)/'org/telegram/ui/Components/AnimatedFileDrawable.java';anim.parent.mkdir(parents=True);anim.write_text('package org.telegram.ui.Components;public interface AnimatedFileDrawable{}')
   subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(java),str(rect),str(anim)],check=True)
   subprocess.run(['java','-cp',tmp,'StaticSourceProbe'],check=True)
