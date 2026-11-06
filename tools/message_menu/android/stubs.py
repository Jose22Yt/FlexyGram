"""Production menu/settings/config/physics, with explicit Telegram navigation/theme hosts only."""
import json,re
from pathlib import Path
from xml.etree import ElementTree as E

def write(dest,root):
 def put(name,source):
  path=dest/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
 java=root/'TMessagesProj/src/main/java'
 names=['BubbleActionPanelView','BubbleMenuConfig','BubbleMenuIcon','BubbleMenuGallery','BubbleInteractionSettings','BubbleInteractionSettingsActivity','BubbleTapMotion','SelectedBubbleMotion','DampedSpringCurve','ContextPreviewPlacement','ContextPreviewViewport','MessageMenuViewport']
 sources=[]
 for name in names:
  source=(java/'app/flexygram/bubbles/interaction'/(name+'.java')).read_text();sources.append(source);put('app/flexygram/bubbles/interaction/'+name+'.java',source)
 for path in ['app/flexygram/animation/FastMotionTiming.java','app/exteraless/player/Spring.java']:
  source=(java/path).read_text();sources.append(source);put(path,source)
 keys=sorted(set(re.findall(r'R.string.(\w+)', '\n'.join(sources))))
 values={}
 for path in (root/'TMessagesProj/src/main/res/values').glob('*.xml'):
  for item in E.parse(path).getroot():
   if item.tag=='string':values[item.attrib['name']]=''.join(item.itertext())
 missing=set(keys)-values.keys()
 if missing:raise AssertionError('Missing production string resources: '+str(missing))
 iconmap=json.loads((root/'tools/cupertino/mapping.json').read_text())
 put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+k+'='+str(i+1)+';'for i,k in enumerate(keys))+'}public static class drawable{'+''.join('public static final int '+k+'='+str(i+1)+';'for i,k in enumerate(sorted(iconmap)))+'}}')
 import shutil
 for name in ['CupertinoIcons','CupertinoGlyphDrawable','CupertinoIconMap','CupertinoSupplement','IconPressFeedback','IconPressCurve']:
  put('app/flexygram/icons/'+name+'.java',(java/'app/flexygram/icons'/(name+'.java')).read_text())
 put('app/exteraless/icons/BaseIconPacks.java','package app.exteraless.icons;public class BaseIconPacks{public static final int BASE_DEFAULT=0,BASE_CUPERTINO=3;public static int getSelected(){return 0;}}')
 shutil.copyfile(root/'TMessagesProj/src/main/assets/cupertino/CupertinoIcons.ttf',dest.parents[2]/'CupertinoIcons.ttf')
 put('org/telegram/messenger/LocaleController.java','package org.telegram.messenger;public class LocaleController{public static boolean isRTL;public static String getString(int id){switch(id){'+''.join('case '+str(i+1)+':return '+json.dumps(values[k],ensure_ascii=True)+';'for i,k in enumerate(keys))+'default:throw new IllegalArgumentException();}}}')
 theme_keys=sorted(set(re.findall(r'Theme.(key_\w+)','\n'.join(sources))))
 put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;public class Theme{public interface ResourcesProvider{}public static boolean dark;
 KEYS public static int getColor(int key){return getColor(key,null);}public static int getColor(int key,ResourcesProvider provider){
 if(key==key_text_RedRegular)return 0xffdc2626;if(key==key_windowBackgroundWhiteBlueText)return 0xff258ce6;
 if(key==key_actionBarDefaultSubmenuBackground)return dark?0xff263240:0xffffffff;
 if(key==key_windowBackgroundGray)return dark?0xff15202c:0xffeff0f4;
 if(key==key_divider)return dark?0xff465260:0xffd8dce2;
 return dark?0xfff1f4f7:0xff182220;}}
 '''.replace('KEYS',''.join('public static final int '+k+'='+str(i+1)+';'for i,k in enumerate(theme_keys))))
 put('org/telegram/messenger/SharedConfig.java','package org.telegram.messenger;public class SharedConfig{public static boolean animationsEnabled(){return true;}}')
 put('org/telegram/messenger/AndroidUtilities.java','package org.telegram.messenger;public class AndroidUtilities{public static boolean isAccessibilityScreenReaderEnabled(){return false;}public static android.graphics.Typeface bold(){return android.graphics.Typeface.create("sans-serif-medium",0);}}')
 put('androidx/recyclerview/widget/RecyclerView.java','package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public android.view.View itemView;public int position;public ViewHolder(android.view.View view){itemView=view;}}}')
 put('org/telegram/ui/Components/RecyclerListView.java','package org.telegram.ui.Components;public class RecyclerListView{public static class Holder extends androidx.recyclerview.widget.RecyclerView.ViewHolder{public Holder(android.view.View v){super(v);}}}')
 put('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.widget.TextView{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String text,String value,boolean divider){setText(text+" "+value);}}')
 put('org/telegram/ui/Cells/TextInfoPrivacyCell.java','package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.widget.TextView{public TextInfoPrivacyCell(android.content.Context c){super(c);}}')
 put('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;import android.content.*;public class AlertDialog{public static class Builder{
 private final android.app.AlertDialog.Builder builder;public Builder(Context c,Theme.ResourcesProvider p){builder=new android.app.AlertDialog.Builder(c);}
 public Builder setTitle(String text){builder.setTitle(text);return this;}public Builder setView(android.view.View v){builder.setView(v);return this;}
 public Builder setItems(String[] items,DialogInterface.OnClickListener listener){builder.setItems(items,listener);return this;}
 public Builder setPositiveButton(String text,DialogInterface.OnClickListener listener){builder.setPositiveButton(text,listener);return this;}
 public Builder setNegativeButton(String text,DialogInterface.OnClickListener listener){builder.setNegativeButton(text,listener);return this;}
 public Builder setNeutralButton(String text,DialogInterface.OnClickListener listener){builder.setNeutralButton(text,listener);return this;}
 public android.app.AlertDialog create(){return builder.create();}}}''')
 put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;import android.view.*;import android.content.*;import android.widget.*;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.ActionBar.Theme;
 public abstract class SignatureMatteSettingsActivity{public static android.app.Activity activity;public android.app.AlertDialog dialog;protected Theme.ResourcesProvider resourcesProvider;
 protected static final int TYPE_SETTINGS=1,TYPE_INFO_PRIVACY=2;protected int rows;protected BaseListAdapter listAdapter;protected LinearLayout listView;
 protected void updateRows(){rows=0;}protected int addRow(){return rows++;}protected int addRow(String key){return addRow();}
 protected abstract String getActionBarTitle();protected abstract BaseListAdapter createAdapter(Context c);protected abstract void onItemClick(View v,int p,float x,float y);
 public View createView(Context c){updateRows();listView=new LinearLayout(c);listView.setOrientation(1);listAdapter=createAdapter(c);render();return listView;}
 private void render(){listView.removeAllViews();for(int i=0;i<rows;i++){RecyclerView.ViewHolder h=listAdapter.onCreateViewHolder(listView,listAdapter.getItemViewType(i));h.position=i;listAdapter.onBindViewHolder(h,i,false);listView.addView(h.itemView,new LinearLayout.LayoutParams(-1,-2));}}
 public void click(int p){onItemClick(null,p,0,0);}public android.app.Activity getParentActivity(){return activity;}public Theme.ResourcesProvider getResourceProvider(){return resourcesProvider;}
 protected int getThemedColor(int key){return Theme.getColor(key);}protected int settingsRowPosition(RecyclerView.ViewHolder h){return h.position;}public void onResume(){}
 protected void showDialog(android.app.AlertDialog value){dialog=value;dialog.show();}
 protected class BaseListAdapter{public void notifyDataSetChanged(){render();}public void notifyItemChanged(int p){render();}public int getItemViewType(int p){return TYPE_SETTINGS;}
 public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){return new org.telegram.ui.Components.RecyclerListView.Holder(type==TYPE_INFO_PRIVACY?new org.telegram.ui.Cells.TextInfoPrivacyCell(parent.getContext()):new org.telegram.ui.Cells.TextSettingsCell(parent.getContext()));}
 public void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial){}public boolean isEnabled(RecyclerView.ViewHolder h){return true;}}
 protected class MatteListAdapter extends BaseListAdapter{public MatteListAdapter(Context c){}}}
 ''')

 # Compile actual async scrim processing with explicit transport/worker hosts.
 text=(java/'org/telegram/ui/Components/ScrimOptions.java').read_text()
 def extract(anchor):
  a=text.index(anchor);b=text.index('{',a)+1;depth=1
  while depth:depth+=(text[b]=='{')-(text[b]=='}');b+=1
  return text[a:b]
 methods=extract('public static void makeGlobalBlurBitmaps(Utilities.Callback2<Bitmap, Bitmap> bitmaps, boolean async)')
 put('org/telegram/messenger/FileLog.java','package org.telegram.messenger;public class FileLog{public static void e(Throwable t){}}')
 code='''import android.graphics.*;public class AsyncScrimProbe {
 public static class Queue{public java.util.ArrayDeque<Runnable> tasks=new java.util.ArrayDeque<>();public void postRunnable(Runnable r){tasks.add(r);}public void drain(){while(!tasks.isEmpty())tasks.remove().run();}}
 public static class Utilities{public interface Callback2<A,B>{void run(A a,B b);}public static final Queue themeQueue=new Queue();}
 public static class Theme{public static boolean isCurrentThemeDark(){return false;}}
 public static class AndroidUtilities{
  public interface Callback{void run(Bitmap b);}public static Queue ui=new Queue();public static Bitmap original;public static boolean requestedAsync;
  public static void makeGlobalBlurBitmap(Callback cb,float downscale,int amount,Object v,Object exclude,boolean async){requestedAsync=async;original=Bitmap.createBitmap(16,16,Bitmap.Config.ARGB_8888);original.eraseColor(Color.RED);if(async)Utilities.themeQueue.postRunnable(()->cb.run(original));else cb.run(original);}
  public static void runOnUIThread(Runnable r){ui.postRunnable(r);}public static void adjustSaturationColorMatrix(ColorMatrix m,float d){m.setSaturation(1+d);}
  public static void adjustBrightnessColorMatrix(ColorMatrix m,float d){}
  public static Bitmap applyColorMatrix(Bitmap bitmap,ColorMatrix matrix){Bitmap out=Bitmap.createBitmap(16,16,Bitmap.Config.ARGB_8888);Paint p=new Paint();p.setColorFilter(new ColorMatrixColorFilter(matrix));new Canvas(out).drawBitmap(bitmap,0,0,p);return out;}
 }
 METHODS
}'''.replace('METHODS',methods)
 put('AsyncScrimProbe.java',code)

 text=(java/'org/telegram/messenger/AndroidUtilities.java').read_text()
 start=text.index('public static void makeGlobalBlurBitmap(Utilities.Callback<Bitmap> onBitmapDone, float downscale, int amount, View forView, List<View> exclude, boolean asyncBlur)')
 pos=text.index('{',start)+1;depth=1
 while depth:depth+=(text[pos]=='{')-(text[pos]=='}');pos+=1
 capture=text[start:pos]
 put('NativeCaptureProbe.java','''import android.graphics.*;import android.view.*;import java.util.*;import androidx.core.graphics.ColorUtils;
public class NativeCaptureProbe{
 public static boolean makingGlobalBlurBitmap;public static List<View> views;
 public static List<View> allGlobalViews(){return views;}
 public static class FileLog{public static void e(Throwable t){throw new AssertionError(t);}}
 public static class Utilities{public interface Callback<T>{void run(T t);}public static AsyncScrimProbe.Queue themeQueue=new AsyncScrimProbe.Queue();public static int blurs;public static void stackBlurBitmap(Bitmap b,int r){blurs++;}}
 public static class Theme{public static int key_windowBackgroundWhite;public static int getColor(int k){return Color.WHITE;}}
 public static class AndroidUtilities{public static Point displaySize=new Point(120,240);public static int statusBarHeight,navigationBarHeight;public static AsyncScrimProbe.Queue ui=new AsyncScrimProbe.Queue();public static void runOnUIThread(Runnable r){ui.postRunnable(r);}}
 public static class PipRoundVideoView{public static class PipFrameLayout extends android.widget.FrameLayout{public PipFrameLayout(android.content.Context c){super(c);}}}
 CAPTURE
}'''.replace('CAPTURE',capture))

 # Execute the full production backdrop pass with native View/Canvas composition.
 chat=(java/'org/telegram/ui/ChatActivity.java').read_text()
 a=chat.index('            final int messageScrimSave = canvas.save();')
 b=chat.index('            if (scrimViewReaction != null && scrimViewReactionAnimated)',a)
 block=chat[a:b]+'canvas.restoreToCount(messageScrimSave);'
 put('ComposerOverlayProbe.java', '''import android.content.*;import android.graphics.*;import android.view.*;import android.widget.*;
 public class ComposerOverlayProbe extends FrameLayout {
 Object selectedBubbleMotionMessage=new Object(),scrimViewReaction,scrimView;Paint scrimBlurBitmapPaint=new Paint(),scrimPaint=new Paint();float scrimViewProgress=1,scrimPaintAlpha=.2f,scrimViewAlpha=1;
 Bitmap scrimBlurBitmap=Bitmap.createBitmap(100,120,Bitmap.Config.ARGB_8888);Matrix scrimBlurMatrix=new Matrix();BitmapShader scrimBlurBitmapShader;
 View chatInputViewsContainer,header;
 public ComposerOverlayProbe(Context c){super(c);chatInputViewsContainer=new View(c);chatInputViewsContainer.setBackgroundColor(Color.CYAN);addView(chatInputViewsContainer,new FrameLayout.LayoutParams(100,24,Gravity.BOTTOM));
 header=new View(c);header.setBackgroundColor(Color.CYAN);addView(header,new FrameLayout.LayoutParams(100,24,Gravity.TOP));
 scrimBlurBitmap.eraseColor(Color.YELLOW);scrimBlurBitmapShader=new BitmapShader(scrimBlurBitmap,Shader.TileMode.CLAMP,Shader.TileMode.CLAMP);scrimBlurBitmapPaint.setShader(scrimBlurBitmapShader);}
 public void redraw(Canvas canvas){super.dispatchDraw(canvas);BLOCK}
 }'''.replace('BLOCK',block))

 # Actual common preview transform: tiles, group background, caption and time share one matrix.
 a=chat.index('    private void transformSelectedMessagePreview(Canvas canvas)')
 b=chat.index('{',a)+1;depth=1
 while depth:depth+=(chat[b]=='{')-(chat[b]=='}');b+=1
 transform=chat[a:b].replace('private void','public void')
 a=chat.index('    private void selectedMessageBounds(ChatMessageCell anchor, RectF bounds)')
 b=chat.index('{',a)+1;depth=1
 while depth:depth+=(chat[b]=='{')-(chat[b]=='}');b+=1
 bounds=chat[a:b].replace('private void','public void')
 put('AlbumTransformProbe.java','''import android.graphics.*;import android.view.*;import android.content.*;
 public class AlbumTransformProbe {
 public final RectF selectedBubblePreviewBounds=new RectF();public float selectedBubblePreviewWindowTop,selectedBubblePreviewWindowBottom,selectedBubbleOffsetY,selectedBubblePreviewScale=1;
 public View contentView;public android.widget.FrameLayout chatListView;
 public static class MessageObject{public static class GroupedMessages{}}
 public static class ChatMessageCell extends View{
 public final RectF background=new RectF();public MessageObject.GroupedMessages album;
 public ChatMessageCell(Context c){super(c);}public MessageObject.GroupedMessages getCurrentMessagesGroup(){return album;}
 public int getBackgroundDrawableLeft(){return (int)background.left;}public int getBackgroundDrawableTop(){return (int)background.top;}
 public int getBackgroundDrawableRight(){return (int)background.right;}public int getBackgroundDrawableBottom(){return (int)background.bottom;}}
 public final Motion selectedBubbleMotion=new Motion();
 public static class Motion{public float phase=1;public float progress(){return phase;}public float spatialOffset(float value,int extra){return value*phase;}public float scaleX(){return 1;}public float scaleY(){return 1;}}
 public static float lerp(float a,float b,float t){return a+(b-a)*t;}public static int dp(int v){return v;}
 public AlbumTransformProbe(Context c){contentView=new View(c);contentView.layout(0,0,320,700);chatListView=new android.widget.FrameLayout(c);chatListView.layout(0,20,320,700);}
 TRANSFORM
 BOUNDS
 }'''.replace('TRANSFORM',transform).replace('BOUNDS',bounds))

 # Actual cell alpha-layer clipping, with native Canvas and explicit row bounds.
 cell=(java/'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
 a=cell.index('        if (alphaInternal != 1.0f) {');b=cell.index('{',a)+1;depth=1
 while depth:depth+=(cell[b]=='{')-(cell[b]=='}');b+=1
 put('SelectedAlphaProbe.java', '''import android.graphics.*;import android.graphics.drawable.*;
 public class SelectedAlphaProbe {
 boolean fullyDraw;float alphaInternal=.5f;int parentHeight=400,drawSideButton;float y=-200;
 static class Message {boolean isOutOwner(){return false;}}Message currentMessageObject=new Message();int dp(int n){return n;}
 RectF rect=new RectF();Drawable currentBackgroundDrawable=new ColorDrawable(Color.GREEN);
 public SelectedAlphaProbe(){currentBackgroundDrawable.setBounds(0,0,120,800);}
 int getMeasuredWidth(){return 120;}int getMeasuredHeight(){return 800;}float getY(){return y;}
 void render(Canvas canvas){int save=canvas.getSaveCount();BLOCK
 Paint paint=new Paint();paint.setColor(Color.GREEN);canvas.drawRect(0,0,120,800,paint);canvas.restoreToCount(save);}
 }'''.replace('BLOCK',cell[a:b]))
