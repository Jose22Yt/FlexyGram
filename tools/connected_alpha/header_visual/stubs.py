"""Actual new controller and actual avatar measure/layout methods in a declared native fixture.
Not the whole ChatAvatarContainer, ActionBar, ChatActivity or Telegram navigation engine.
"""
import importlib.util,re
from pathlib import Path

def body(source,anchor):
 a=source.index(anchor);p=source.index('{',a)+1;n=1
 while n:n+=(source[p]=='{')-(source[p]=='}');p+=1
 return source[a:p]

def write_stubs(source,root):
 spec=importlib.util.spec_from_file_location('header_music_services',root/'tools/connected_alpha/music_visual/stubs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.write_stubs(source,root)
 def put(path,text):p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
 folder=root/'TMessagesProj/src/main/java/app/flexygram/header'
 for name in ['HeaderConfig','HeaderGeometry','HeaderSurface','SignatureChatHeader','HeaderPreviewView']:put('app/flexygram/header/'+name+'.java',(folder/(name+'.java')).read_text())
 for p in (folder/'fusion').glob('*.java'):put('app/flexygram/header/fusion/'+p.name,p.read_text())
 actual=(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/ChatAvatarContainer.java').read_text()
 avatar_methods='\n'.join(body(actual,a)for a in ['public void setSignatureHeader(', 'private boolean signatureActive(', 'private boolean signatureFusionActive(', 'private boolean signatureFusionHasPhoto(', 'private void prepareFusionControls(', 'public boolean signatureCallAvailable(', 'public float signaturePreferredTitleWidth(', 'private void measureSignature(', 'private void layoutSignature(', 'protected boolean drawChild(', 'public boolean dispatchTouchEvent(', 'public boolean onTouchEvent(MotionEvent ev)']).replace('@NonNull ','')
 code='\n'.join((folder/(n+'.java')).read_text()for n in ['HeaderConfig','HeaderSurface','SignatureChatHeader','HeaderPreviewView'])
 code+='\n'+avatar_methods+'\nTheme.key_actionBarDefaultSubtitle'
 assert actual.index('addView(avatarImageView)')<actual.index('addView(titleTextView)')<actual.index('addView(subtitleTextView)')
 r=source/'org/telegram/messenger/R.java';s=r.read_text();missing=set(re.findall(r'R.string.(\w+)',code))-set(re.findall(r'int (\w+)=',s));s=s.replace('class string {','class string {'+''.join('public static final int '+n+'='+str(1000+i)+';'for i,n in enumerate(sorted(missing))));s=s.replace('public class R {','public class R {public static class drawable {public static int ic_ab_back,ic_ab_other,msg_callback;}');r.write_text(s)
 t=source/'org/telegram/ui/ActionBar/Theme.java';s=t.read_text();keys=set(re.findall(r'Theme.(key_\w+)',code))-set(re.findall(r'int (key_\w+)=',s));s=s.replace('public static boolean dark;', ''.join('public static final int '+n+'='+str(2000+i)+';'for i,n in enumerate(sorted(keys)))+'public static boolean dark;');s=s.replace('public static int getColor(int k,ResourcesProvider r){','public static int getColor(int k){return getColor(k,null);}public static int getColor(int k,ResourcesProvider r){if(k==key_actionBarDefaultTitle)return dark?0xffeeeeee:0xff152c3e;if(k==key_actionBarDefaultSubtitle)return dark?0xffb0bac5:0xff5b6875;if(k==key_divider)return dark?0xff899099:0xff9babb9;');s=s.replace('public static int getColor(int k){','public static android.graphics.drawable.Drawable createSimpleSelectorRoundRectDrawable(float r,int fill,int selected){android.graphics.drawable.GradientDrawable d=new android.graphics.drawable.GradientDrawable();d.setColor(fill);d.setCornerRadius(r);return d;}public static int getColor(int k){');s=s.replace('public static boolean dark;', 'public static final android.graphics.Paint PAINT_CLEAR=new android.graphics.Paint();public static boolean dark;');t.write_text(s)
 a=source/'org/telegram/messenger/AndroidUtilities.java';s=a.read_text().replace('public class AndroidUtilities {','public class AndroidUtilities {public static final android.graphics.RectF rectTmp=new android.graphics.RectF();private static final android.os.Handler handler=new android.os.Handler(android.os.Looper.getMainLooper());public static void cancelRunOnUIThread(Runnable r){handler.removeCallbacks(r);}public static void runOnUIThread(Runnable r,long delay){handler.postDelayed(r,delay);}') ;a.write_text(s)
 l=source/'org/telegram/messenger/LocaleController.java';s=l.read_text().replace('public class LocaleController {','public class LocaleController {public static boolean isRTL;public static String formatString(int id,Object... args){return "Unread: "+args[0];}');s=s.replace('public static String getString(int id){','public static String getString(int id){if(id==R.string.FlexyHeaderPreviewName)return "Alex";if(id==R.string.Online)return "online";');l.write_text(s)
 put('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader {public static android.content.Context applicationContext;}')
 put('app/exteraless/appearance/AppearanceConfig.java','package app.exteraless.appearance;public class AppearanceConfig {public static android.content.SharedPreferences getPreferences(){return org.telegram.messenger.ApplicationLoader.applicationContext.getSharedPreferences("appearance",0);}}')
 put('org/telegram/ui/ActionBar/ActionBar.java','''package org.telegram.ui.ActionBar;
import android.content.Context;import android.graphics.Canvas;import android.widget.*;import android.view.*;import app.flexygram.header.*;
public class ActionBar extends FrameLayout{
 public boolean drawSignatureNativeGlass(android.graphics.Canvas c,app.flexygram.header.SignatureChatHeader h){return false;}

 public final UnreadImageView backButtonImageView;public boolean search,selection;public int backs;private SignatureChatHeader header;
 public static int getCurrentActionBarHeight(){return 56;}public static class UnreadImageView extends ImageView{public UnreadImageView(Context c){super(c);}public void setUnread(int count){}}
 public ActionBar(Context c){super(c);backButtonImageView=new UnreadImageView(c);backButtonImageView.setOnClickListener(v->backs++);addView(backButtonImageView);}
 public void setSignatureHeader(SignatureChatHeader h){header=h;}public boolean isSearchFieldVisible(){return search;}public boolean isActionModeShowed(){return selection;}
 @Override protected void onMeasure(int ws,int hs){int w=MeasureSpec.getSize(ws),h=header!=null&&header.enabled()?header.measure(w,24,56):56;setMeasuredDimension(w,h+24);for(int i=0;i<getChildCount();i++){View v=getChildAt(i);if(v.getVisibility()!=GONE)v.measure(MeasureSpec.makeMeasureSpec(w,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(h+24,MeasureSpec.EXACTLY));}backButtonImageView.measure(MeasureSpec.makeMeasureSpec(54,MeasureSpec.EXACTLY),MeasureSpec.makeMeasureSpec(h,MeasureSpec.EXACTLY));if(header!=null)header.measureControls();}
 @Override protected void onLayout(boolean ch,int l,int t,int r,int b){for(int i=0;i<getChildCount();i++)getChildAt(i).layout(0,0,getChildAt(i).getMeasuredWidth(),getChildAt(i).getMeasuredHeight());backButtonImageView.layout(0,24,54,80);if(header!=null)header.layoutControls();}
 @Override protected void dispatchDraw(Canvas c){if(header!=null&&header.active())header.draw(c);super.dispatchDraw(c);}
}''')
 methods=avatar_methods
 put('org/telegram/ui/Components/ChatAvatarContainer.java','''package org.telegram.ui.Components;
import static org.telegram.messenger.AndroidUtilities.dp;import static org.telegram.messenger.AndroidUtilities.dpf2;import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;import android.graphics.Canvas;import android.view.*;import android.widget.*;import org.telegram.messenger.*;import org.telegram.ui.ActionBar.Theme;import org.telegram.ui.ActionBar.ActionBar;
public class ChatAvatarContainer extends FrameLayout{
 private app.flexygram.header.SignatureChatHeader signatureHeader;private ImageView signatureMore,signatureCall;
 private app.flexygram.header.fusion.SignatureFusionAvatarMask signaturePhotoMask;private android.graphics.Path signaturePhotoClip;
 public int profiles,menus,calls;public boolean callable,searchingAllowed,glassMode,pressed;
 static class Bounce {void setPressed(boolean p){}float getScale(float n){return 1;}}private final Bounce bounce=new Bounce();
 private final Runnable onLongClick=()->{};private boolean canSearch(){return searchingAllowed;}private boolean isCentered(){return false;}private void openProfile(boolean avatar){profiles++;}
 public boolean ignoreTouches;
 protected boolean isSignatureCallAvailable(){return callable;}protected void onSignatureCallClick(){calls++;}

 public static class Simple extends TextView{Simple(Context c){super(c);setIncludeFontPadding(false);setSingleLine(true);setEllipsize(android.text.TextUtils.TruncateAt.END);}public void setTextSizePx(int v){setTextSize(android.util.TypedValue.COMPLEX_UNIT_PX,v);}}
 public static class Photo extends ImageView{
  public int radius;
  public static class Receiver {
   public boolean photo=true;
   public Object getImageLocation(){return photo ? this : null;}
   public Object getMediaLocation(){return null;}
   public Object getThumbLocation(){return null;}
   public boolean hasNotThumb(){return photo;}
  }
  public final Receiver receiver=new Receiver();
  Photo(Context c){super(c);}public Receiver getImageReceiver(){return receiver;}
  public void setRoundRadius(int r){radius=r;}@Override protected void onDraw(Canvas c){android.graphics.Paint p=new android.graphics.Paint(3);p.setColor(0xff2288cc);if(radius==0)c.drawRect(0,0,getWidth(),getHeight(),p);else c.drawCircle(getWidth()/2f,getHeight()/2f,getWidth()/2f,p);}}
 private final Simple titleTextView,subtitleTextView;private final Photo avatarImageView;private Simple animatedSubtitleTextView;private View timeItem,communityItem,starBgItem,starFgItem;
 public ChatAvatarContainer(Context c){super(c);titleTextView=new Simple(c);titleTextView.setText("A long contact name");titleTextView.setPadding(0,dp(6),0,dp(12));subtitleTextView=new Simple(c);subtitleTextView.setText("online");avatarImageView=new Photo(c);titleTextView.setTextColor(getThemedColor(Theme.key_actionBarDefaultTitle));subtitleTextView.setTextColor(getThemedColor(Theme.key_actionBarDefaultSubtitle));addView(avatarImageView);addView(titleTextView);addView(subtitleTextView);setOnClickListener(v->profiles++);avatarImageView.setOnClickListener(v->{if(signatureFusionActive())profiles++;else menus++;});}
 private View getSubtitleTextView(){return subtitleTextView;}private int getThemedColor(int key){return Theme.getColor(key,null);}protected void onSignatureOptionsClick(){menus++;}
 @Override protected void onMeasure(int w,int h){if(signatureActive()){measureSignature(w,h);return;}if(signatureCall!=null)signatureCall.setVisibility(GONE);if(signatureMore!=null)signatureMore.setVisibility(GONE);super.onMeasure(w,h);}
 @Override protected void dispatchDraw(Canvas canvas){super.dispatchDraw(canvas);if(signatureFusionActive())signatureHeader.drawForeground(canvas);}
 @Override protected void onLayout(boolean c,int l,int t,int r,int b){if(signatureActive())layoutSignature();else super.onLayout(c,l,t,r,b);}
'''+methods+'\n}')
