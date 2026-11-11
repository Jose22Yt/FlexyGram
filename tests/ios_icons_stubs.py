"""Small host doubles for Drawable/Resources contracts. No Android rendering claim."""
import json
from test_render_work_reuse import ROOT


def fixtures():
    mapping=json.loads((ROOT/'tools/exact_icons/mapping.json').read_text())
    names=sorted(set(mapping)|{v['asset']for v in mapping.values()})
    fields=''.join(f'public static int {n}={len(names)-i+100};'for i,n in enumerate(names))
    return {
'org/telegram/messenger/R.java':'package org.telegram.messenger;public class R{public static class drawable{'+fields+'}}',
'app/exteraless/icons/BaseIconPacks.java':'package app.exteraless.icons;public class BaseIconPacks{public static int BASE_DEFAULT=0,BASE_CUPERTINO=3,selected,reads;public static int getSelected(){reads++;return selected;}}',
'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
'android/content/Context.java':'package android.content;public class Context{public android.content.res.Resources getResources(){return new android.content.res.Resources();}public android.content.res.Resources.Theme getTheme(){return null;}}',
'android/content/res/ColorStateList.java':'package android.content.res;public class ColorStateList{}',
'android/graphics/ColorFilter.java':'package android.graphics;public class ColorFilter{}',
'android/graphics/PorterDuff.java':'package android.graphics;public class PorterDuff{public enum Mode{SRC_IN,MULTIPLY}}',
'android/graphics/Rect.java':'''package android.graphics;public class Rect{public int left,top,right,bottom;public int width(){return right-left;}public int height(){return bottom-top;}public void set(int l,int t,int r,int b){left=l;top=t;right=r;bottom=b;}}''',
'android/graphics/Canvas.java':'package android.graphics;public class Canvas{public android.graphics.drawable.Fake last;}',
'android/graphics/drawable/Drawable.java':'''package android.graphics.drawable;
import android.graphics.*;import android.content.res.*;
public abstract class Drawable{
 public int tint,alpha=255;public boolean mirrored;public ColorFilter filter;private int layout,level;private int[]state={};private Callback callback;private final Rect bounds=new Rect();
 public abstract void draw(Canvas c);public int getIntrinsicWidth(){return 0;}public int getIntrinsicHeight(){return 0;}
 public void setBounds(int l,int t,int r,int b){bounds.set(l,t,r,b);onBoundsChange(bounds);}public void setBounds(Rect r){setBounds(r.left,r.top,r.right,r.bottom);}public Rect getBounds(){return bounds;}protected void onBoundsChange(Rect r){}
 public void setAlpha(int a){alpha=a;}public int getAlpha(){return alpha;}public void setColorFilter(ColorFilter f){filter=f;}public ColorFilter getColorFilter(){return filter;}
 public void setTint(int c){tint=c;}public void setTintList(ColorStateList c){}public void setTintMode(PorterDuff.Mode m){}
 public void setAutoMirrored(boolean b){mirrored=b;}public boolean isAutoMirrored(){return mirrored;}
 public final boolean setLayoutDirection(int d){layout=d;return onLayoutDirectionChanged(d);}public int getLayoutDirection(){return layout;}public boolean onLayoutDirectionChanged(int d){return false;}
 public boolean isStateful(){return true;}public boolean setState(int[]s){state=s;return onStateChange(s);}public int[]getState(){return state;}protected boolean onStateChange(int[]s){return true;}
 public final boolean setLevel(int l){level=l;return onLevelChange(l);}public final int getLevel(){return level;}protected boolean onLevelChange(int l){return true;}
 public int getOpacity(){return -3;}public Drawable mutate(){return this;}public void setCallback(Callback c){callback=c;}
 public void invalidateSelf(){if(callback!=null)callback.invalidateDrawable(this);}public void scheduleSelf(Runnable r,long t){if(callback!=null)callback.scheduleDrawable(this,r,t);}public void unscheduleSelf(Runnable r){if(callback!=null)callback.unscheduleDrawable(this,r);}
 public interface Callback{void invalidateDrawable(Drawable who);void scheduleDrawable(Drawable who,Runnable what,long when);void unscheduleDrawable(Drawable who,Runnable what);}
 public abstract ConstantState getConstantState();public abstract static class ConstantState{
  public abstract Drawable newDrawable();public Drawable newDrawable(Resources r){return newDrawable();}public abstract int getChangingConfigurations();public boolean canApplyTheme(){return false;}}
}''',
'android/graphics/drawable/Fake.java':'''package android.graphics.drawable;import android.content.res.Resources;import android.graphics.Canvas;
public class Fake extends Drawable{public final Object pixels;private final int density,w,h;public Fake(Object p,int d,int w,int h){pixels=p;density=d;this.w=w;this.h=h;}
 public void draw(Canvas c){c.last=this;}public int getIntrinsicWidth(){return Math.round(w*density/160f);}public int getIntrinsicHeight(){return Math.round(h*density/160f);}
 public ConstantState getConstantState(){return new ConstantState(){public Drawable newDrawable(){return new Fake(pixels,density,w,h);}public Drawable newDrawable(Resources r){return new Fake(pixels,r.density,w,h);}public int getChangingConfigurations(){return 0;}};}
}''',
'android/content/res/Resources.java':'''package android.content.res;import android.graphics.drawable.*;public class Resources{
 public static class Theme{}public int density=320,depth,maxDepth,decodes;private java.util.Map<Integer,Object> pixels=new java.util.HashMap<>();
 public Drawable getDrawableForDensity(int id,int dpi,Theme theme){depth++;maxDepth=Math.max(maxDepth,depth);Drawable icon=app.flexygram.icons.ExactIcons.create(this,id,dpi,theme);
 if(icon==null){Object data=pixels.get(id);if(data==null){data=new Object();pixels.put(id,data);decodes++;}boolean rect=id==org.telegram.messenger.R.drawable.fg_ios_original_chat_input_text_iconattachment;
 icon=new Fake(data,dpi==0?density:dpi,rect?30:32,rect?20:32);}depth--;return icon;}
}''',
    }
