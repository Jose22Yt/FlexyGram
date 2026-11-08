#!/usr/bin/env python3
"""Native deletion widgets/lifecycle. Optional original-source oracle is never installed or hooked."""
import importlib.util,sys,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('delete_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
reference=None
if '--reference-dir' in sys.argv:
 i=sys.argv.index('--reference-dir');reference=Path(sys.argv[i+1]);del sys.argv[i:i+2]
def write_stubs(source,root):
 def put(path,text):
  p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 java=root/'TMessagesProj/src/main/java';base='app/flexygram/bubbles/deletion/'
 names=['DeleteMotionMath','DeleteMotionSettings','DeleteMotionOverlay','FractureMotionMath','FractureMesh','TntMotion','TntMesh','BubbleFractureRenderer','DeleteMotionPreview','DeleteMotionSettingsActivity']
 for name in names:put(base+name+'.java',(java/base/(name+'.java')).read_text())
 put('app/flexygram/settings/signature/StylePreviewCard.java',(java/'app/flexygram/settings/signature/StylePreviewCard.java').read_text())
 put('app/flexygram/preview/SignatureWallpaperPreview.java',(java/'app/flexygram/preview/SignatureWallpaperPreview.java').read_text())
 if reference:
  for name in ['BubbleFracture','FractureMesh','MotionMath','TntMesh','TntMotion']:put('com/larrat/fracture/'+name+'.java',(reference/(name+'.java')).read_text())
 text=''.join((source/base/(name+'.java')).read_text() for name in names)
 strings=sorted(set(re.findall(r'R.string.(\w+)',text)))
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+name+'='+str(i+1)+';' for i,name in enumerate(strings))+'}}')
 put('org/telegram/messenger/LocaleController.java','''package org.telegram.messenger;public class LocaleController{public static String getString(int id){
 if(id==R.string.FlexyDeleteSample)return "Mensaje de ejemplo  ✓✓";
 if(id==R.string.FlexyDeleteCrystal)return "Fractura de cristal";if(id==R.string.FlexyDeleteFall)return "Caída fluida";if(id==R.string.FlexyDeleteVortex)return "Vórtice";if(id==R.string.FlexyDeleteTnt)return "Explosión TNT";
 return "Elige un estilo";}}''')
 put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger;public class AndroidUtilities{public static boolean screenReader;public static int dp(float v){return(int)Math.ceil(v);}public static android.graphics.Typeface bold(){return android.graphics.Typeface.create("sans-serif",1);}public static boolean isAccessibilityScreenReaderEnabled(){return screenReader;}public static void runOnUIThread(Runnable r){new android.os.Handler(android.os.Looper.getMainLooper()).post(r);}}''')
 put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig{public static boolean enabled=true;public static boolean animationsEnabled(){return enabled;}}')
 put('org/telegram/messenger/NotificationCenter.java','''package org.telegram.messenger;public class NotificationCenter{
 public static final int didSetNewTheme=1,didApplyNewTheme=2,didSetNewWallpapper=3;static final NotificationCenter n=new NotificationCenter();public static NotificationCenter getGlobalInstance(){return n;}
 public interface NotificationCenterDelegate{void didReceivedNotification(int id,int account,Object...args);}public void addObserver(Object o,int id){}public void removeObserver(Object o,int id){}}''')
 put('org/telegram/messenger/Utilities.java','''package org.telegram.messenger;public class Utilities{public static final Queue globalQueue=new Queue();public static class Queue{public void cancelRunnable(Runnable r){}public void postRunnable(Runnable r){r.run();}}}''')
 put('org/telegram/messenger/MessageObject.java','package org.telegram.messenger;public class MessageObject{public boolean deleted=true,scheduledSent;}')
 put('org/telegram/ui/Cells/ChatMessageCell.java','''package org.telegram.ui.Cells;public class ChatMessageCell extends android.view.View{public boolean drawingToBitmap;public org.telegram.messenger.MessageObject message=new org.telegram.messenger.MessageObject();public Object group;public org.telegram.messenger.MessageObject getMessageObject(){return message;}public Object getCurrentMessagesGroup(){return group;}public int getBackgroundDrawableLeft(){return 0;}public int getBackgroundDrawableTop(){return 0;}public int getBackgroundDrawableRight(){return getWidth();}public int getBackgroundDrawableBottom(){return getHeight();}public ChatMessageCell(android.content.Context c){super(c);}public boolean drawBackgroundInParent(){return true;}public void drawBackgroundInternal(android.graphics.Canvas c,boolean v){if(!drawingToBitmap)throw new AssertionError("capture flag");}}''')
 keys=sorted(set(re.findall(r'Theme.(key_\w+)',text+(java/'app/flexygram/settings/signature/StylePreviewCard.java').read_text()+(java/'app/flexygram/preview/SignatureWallpaperPreview.java').read_text())))
 put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;import android.graphics.drawable.*;public class Theme{
 public interface ResourcesProvider{}public static boolean dark;public static Drawable wallpaper=new ColorDrawable(0xff43674b);
 '''+''.join('public static final int '+name+'='+str(i+1)+';' for i,name in enumerate(keys))+'''
 public static int getColor(int key){return getColor(key,null);}public static int getColor(int key,ResourcesProvider p){
 if(key==key_windowBackgroundWhiteBlueText)return 0xff2f963e;
 if(key==key_windowBackgroundWhiteBlackText||key==key_chat_messageTextOut)return dark?0xffeeeeee:0xff172019;
 if(key==key_chat_outBubble)return dark?0xff2a4b39:0xffd5f1cd;
 if(key==key_windowBackgroundWhiteGrayText)return dark?0xffaaaaaa:0xff555555;
 return dark?0xff151b17:0xfff6f8f7;}
 public static Drawable getCachedWallpaperNonBlocking(){return wallpaper;}public static void loadWallpaper(boolean force){}
}''')
 put('org/telegram/ui/ChatBackgroundDrawable.java','''package org.telegram.ui;public class ChatBackgroundDrawable extends android.graphics.drawable.ColorDrawable{public float getDimAmount(){return 0;}public android.graphics.drawable.Drawable getDrawable(boolean b){return this;}}''')
 for name,method in [('AnimatedFileDrawable','public android.graphics.Bitmap getAnimatedBitmap(){return null;}'),('MotionBackgroundDrawable','public android.graphics.Bitmap getBitmap(){return null;}public int[] getColors(){return new int[]{0xff335588,0xff889933};}')]:
  put('org/telegram/ui/Components/'+name+'.java','package org.telegram.ui.Components;public class '+name+' extends android.graphics.drawable.ColorDrawable{'+method+'}')
 put('androidx/recyclerview/widget/RecyclerView.java','''package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public final android.view.View itemView;public ViewHolder(android.view.View v){itemView=v;}}public static class LayoutParams extends android.view.ViewGroup.LayoutParams{public LayoutParams(int w,int h){super(w,h);}}}''')
 put('org/telegram/ui/Components/RecyclerListView.java','''package org.telegram.ui.Components;public class RecyclerListView extends android.widget.FrameLayout{public static final int TAG_NOT_SECTION=0x12345;public RecyclerListView(android.content.Context c){super(c);}public void disableSections(){}public void setItemAnimator(Object o){}public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder{public Holder(android.view.View v){super(v);}}}''')
 animator=(java/'org/telegram/ui/recyclerview/ChatListItemAnimator.java').read_text()
 def method(marker):
  a=animator.index(marker);b=animator.index('{',a)+1;depth=1
  while depth:depth+=(animator[b]=='{')-(animator[b]=='}');b+=1
  return animator[a:b]
 a=animator.index('        final View view = holder.itemView;',animator.index('protected void animateRemoveImpl('))
 b=animator.index('        mRemoveAnimations.add(holder);\n        if (thanos',a)
 block=animator[a:b]
 put(base+'NativeDeleteOwner.java','''package app.flexygram.bubbles.deletion;import android.view.*;import java.util.*;import org.telegram.messenger.MessageObject;import org.telegram.ui.Cells.ChatMessageCell;import androidx.recyclerview.widget.RecyclerView;
 public class NativeDeleteOwner{final ViewGroup recyclerListView;final Set<MessageObject> flexyPendingDeletes=Collections.newSetFromMap(new WeakHashMap<>());public final List<RecyclerView.ViewHolder> mRemoveAnimations=new ArrayList<>();public int starting,finished,done,fallback;
 public NativeDeleteOwner(ViewGroup host){recyclerListView=host;}public void dispatchRemoveStarting(RecyclerView.ViewHolder h){starting++;}public void dispatchRemoveFinished(RecyclerView.ViewHolder h){finished++;}public void dispatchFinishedWhenDone(){done++;}public void restoreTransitionParams(View v){v.setAlpha(1);}
 METHODS
 public void remove(RecyclerView.ViewHolder holder){BLOCK fallback++;}}
 '''.replace('METHODS',method('public void prepareFlexyDelete(')+'\n'+method('private boolean takeFlexyDelete(')).replace('BLOCK',block))
 golden=HERE/'golden.json'
 if golden.is_file():(source.parents[2]/'golden.json').write_bytes(golden.read_bytes())
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;import android.content.*;import android.view.*;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.Components.RecyclerListView;import org.telegram.ui.ActionBar.Theme;
 public abstract class SignatureMatteSettingsActivity{
 protected Theme.ResourcesProvider resourcesProvider;protected RecyclerListView listView;
 protected abstract String getActionBarTitle();protected void updateRows(){}protected int addRow(String key){return 0;}protected void onItemClick(View v,int p,float x,float y){}protected abstract BaseListAdapter createAdapter(Context c);
 public View createView(Context c){listView=new RecyclerListView(c);BaseListAdapter a=createAdapter(c);listView.addView(a.onCreateViewHolder(listView,a.getItemViewType(0)).itemView);return listView;}public void onResume(){}public void onPause(){}protected int getThemedColor(int key){return Theme.getColor(key,resourcesProvider);}
 protected abstract class BaseListAdapter{public abstract int getItemViewType(int p);protected boolean isSectionContent(int type){return false;}public abstract RecyclerView.ViewHolder onCreateViewHolder(ViewGroup p,int type);public abstract void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial);public abstract boolean isEnabled(RecyclerView.ViewHolder h);}
 protected abstract class MatteListAdapter extends BaseListAdapter{protected MatteListAdapter(Context c){}}
 }''')
if __name__=='__main__':raise SystemExit(pipeline.main(here=HERE,test_class='DeleteMotionTest',stubs_writer=write_stubs))
