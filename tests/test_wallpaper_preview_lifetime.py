"""Bitmap ownership regression using production helper + explicit Android API doubles, not HWUI/GPU."""
from test_render_work_reuse import JAVA, probe


def test_published_frames_survive_replace_detach_and_stale_jobs_are_disposed(tmp_path):
    files={
      'android/content/res/Resources.java':'package android.content.res;public class Resources{}',
      'android/graphics/Bitmap.java':'''package android.graphics;public class Bitmap{public enum Config{ARGB_8888}public static Bitmap last;int w,h;boolean recycled;public Bitmap(int w,int h){this.w=w;this.h=h;}public static Bitmap createBitmap(int w,int h,Config c){return last=new Bitmap(w,h);}public int getWidth(){return w;}public int getHeight(){return h;}public boolean isRecycled(){return recycled;}public void recycle(){recycled=true;}}''',
      'android/graphics/Rect.java':'package android.graphics;public class Rect{public Rect(){}public Rect(int l,int t,int r,int b){}public void set(int l,int t,int r,int b){}}',
      'android/graphics/Paint.java':'package android.graphics;public class Paint{public static final int FILTER_BITMAP_FLAG=2;public Paint(int flags){}}',
      'android/graphics/Color.java':'package android.graphics;public class Color{public static int argb(int a,int r,int g,int b){return a<<24|r<<16|g<<8|b;}}',
      'android/graphics/Canvas.java':'''package android.graphics;public class Canvas{public Canvas(Bitmap target){}public void drawColor(int c){}public void drawBitmap(Bitmap b,Rect src,Rect dst,Paint p){if(b.isRecycled())throw new IllegalStateException("recorded bitmap recycled");}}''',
      'android/graphics/drawable/Drawable.java':'''package android.graphics.drawable;public class Drawable{public int getIntrinsicWidth(){return -1;}public int getIntrinsicHeight(){return -1;}public void setBounds(android.graphics.Rect r){}public ConstantState getConstantState(){return null;}public Drawable mutate(){return this;}public void draw(android.graphics.Canvas c){}public static class ConstantState{public Drawable newDrawable(android.content.res.Resources r){return new Drawable();}}}''',
      'android/graphics/drawable/BitmapDrawable.java':'''package android.graphics.drawable;public class BitmapDrawable extends Drawable{final android.graphics.Bitmap bitmap;public BitmapDrawable(android.content.res.Resources r,android.graphics.Bitmap b){bitmap=b;}public android.graphics.Bitmap getBitmap(){return bitmap;}public void setFilterBitmap(boolean f){}@Override public void draw(android.graphics.Canvas c){c.drawBitmap(bitmap,null,null,null);}}''',
      'android/graphics/drawable/ColorDrawable.java':'package android.graphics.drawable;public class ColorDrawable extends Drawable{public ColorDrawable(int color){}}',
      'android/graphics/drawable/GradientDrawable.java':'package android.graphics.drawable;public class GradientDrawable extends Drawable{public enum Orientation{TL_BR}public GradientDrawable(Orientation o,int[] colors){}}',
      'android/view/View.java':'package android.view;public class View{public android.content.res.Resources getResources(){return new android.content.res.Resources();}public int getWidth(){return 100;}public int getHeight(){return 80;}}',
      'org/telegram/messenger/AndroidUtilities.java':'''package org.telegram.messenger;public class AndroidUtilities{static java.util.ArrayDeque<Runnable> pending=new java.util.ArrayDeque<>();public static void runOnUIThread(Runnable r){pending.add(r);}public static void drain(){while(!pending.isEmpty())pending.remove().run();}}''',
      'org/telegram/messenger/Utilities.java':'''package org.telegram.messenger;public class Utilities{public static final Queue globalQueue=new Queue();public static class Queue{java.util.ArrayDeque<Runnable> tasks=new java.util.ArrayDeque<>();public void postRunnable(Runnable r){tasks.add(r);}public void cancelRunnable(Runnable r){tasks.remove(r);}public int pending(){return tasks.size();}public void drain(){while(!tasks.isEmpty())tasks.remove().run();}}}''',
      'org/telegram/ui/ActionBar/Theme.java':'package org.telegram.ui.ActionBar;public class Theme{public static android.graphics.drawable.Drawable getCachedWallpaperNonBlocking(){return null;}public static void loadWallpaper(boolean async){}}',
      'org/telegram/ui/ChatBackgroundDrawable.java':'package org.telegram.ui;public class ChatBackgroundDrawable extends android.graphics.drawable.Drawable{public float getDimAmount(){return 0;}public android.graphics.drawable.Drawable getDrawable(boolean motion){return null;}}',
      'org/telegram/ui/Components/MotionBackgroundDrawable.java':'package org.telegram.ui.Components;public class MotionBackgroundDrawable extends android.graphics.drawable.Drawable{public android.graphics.Bitmap bitmap;public MotionBackgroundDrawable(android.graphics.Bitmap b){bitmap=b;}public android.graphics.Bitmap getBitmap(){return bitmap;}public int[] getColors(){return new int[]{0xff123456,0xff345678};}}',
      'org/telegram/ui/Components/AnimatedFileDrawable.java':'package org.telegram.ui.Components;public class AnimatedFileDrawable extends android.graphics.drawable.Drawable{public android.graphics.Bitmap getAnimatedBitmap(){return null;}}',
      'Probe.java':'''import android.graphics.*;import android.graphics.drawable.*;import android.view.View;import org.telegram.messenger.*;import app.flexygram.preview.SignatureWallpaperPreview;
public class Probe{
 static void check(boolean value){if(!value)throw new AssertionError();}
 public static void main(String[]args){
  Bitmap original=new Bitmap(1024,768);var source=new org.telegram.ui.Components.MotionBackgroundDrawable(original);int[] changes={0};
  var helper=new SignatureWallpaperPreview(new View(),source,()->changes[0]++);
  helper.refresh();check(changes[0]==0&&Utilities.globalQueue.pending()==0);
  helper.attach();check(Utilities.globalQueue.pending()==1);Utilities.globalQueue.drain();AndroidUtilities.drain();
  Drawable recorded=helper.drawable();Bitmap first=((BitmapDrawable)recorded).getBitmap();check(first.getWidth()<=512&&first.getHeight()<=512);
  helper.refresh();Utilities.globalQueue.drain();AndroidUtilities.drain();check(helper.drawable()!=recorded&&!first.isRecycled());
  Canvas canvas=new Canvas(new Bitmap(100,100));recorded.draw(canvas);
  Drawable second=helper.drawable();helper.close();check(helper.drawable()==null&&!first.isRecycled());second.draw(canvas);check(!original.isRecycled());
  int count=changes[0];helper.refresh();check(changes[0]==count&&Utilities.globalQueue.pending()==0);
  // Completed worker results that lose their owner before publication have never been drawn.
  helper.attach();Utilities.globalQueue.drain();Bitmap unpublished=Bitmap.last;helper.close();AndroidUtilities.drain();check(unpublished.isRecycled());check(!original.isRecycled());
  helper.attach();check(Utilities.globalQueue.pending()==1);helper.close();check(Utilities.globalQueue.pending()==0);
 }
}''',
    }
    probe(tmp_path,files,[JAVA/'app/flexygram/preview/SignatureWallpaperPreview.java'])
