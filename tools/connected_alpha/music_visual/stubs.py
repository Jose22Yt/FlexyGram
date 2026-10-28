"""Explicit dependency doubles; production widgets/layout/paths are copied unchanged.
No Telegram engine, network, queue service or real artwork decode runs in this probe.
"""
import re
from pathlib import Path
import shutil

PRODUCTION = ('SignatureMusicStyle','SignatureMusicPresentation','SignatureMusicBubble',
              'SignatureMusicHost','ControlsRow','MorphButton','PlayerIcon','Spring',
              'WavySeekBar','RingPlayButton','PlayerBarView','PlayerMiniView','PlayerColors','CoverImage','SignatureCoverFade','SignatureMusicActions')

def write_stubs(source, root):
    def put(path, text):
        dest=source/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(text)
    for annotation in ('NonNull','Nullable'):
        put('androidx/annotation/'+annotation+'.java', 'package androidx.annotation; public @interface '+annotation+' {}')
    player=root/'TMessagesProj/src/main/java/app/exteraless/player'
    for name in PRODUCTION:
        put('app/exteraless/player/'+name+'.java',(player/(name+'.java')).read_text())
    code='\n'.join((player/(n+'.java')).read_text() for n in PRODUCTION)
    names=sorted(set(re.findall(r'R.string.(\w+)',code)))
    put('org/telegram/messenger/R.java','package org.telegram.messenger; public class R {public static class string {'+''.join(f'public static final int {n}={i+1};' for i,n in enumerate(names))+'}}')
    keys=sorted(set(re.findall(r'Theme.(key_\w+)',code)))
    put('org/telegram/ui/ActionBar/Theme.java','''package org.telegram.ui.ActionBar;
import android.graphics.drawable.*; public class Theme {
public static boolean dark; public static final int RIPPLE_MASK_CIRCLE_20DP=1,RIPPLE_MASK_ALL=2;
'''+''.join(f'public static final int {n}={i+1};' for i,n in enumerate(keys))+'''
public interface ResourcesProvider {default int getColor(int k){return Theme.getColor(k,null);} default boolean isDark(){return dark;}}
public static int getColor(int k,ResourcesProvider r){return dark?0xff11151c:0xfff7f8fa;}
public static Drawable getSelectorDrawable(boolean v){return new ColorDrawable(0);}
public static Drawable createSelectorDrawable(int c,int mask){android.graphics.drawable.GradientDrawable shape=new android.graphics.drawable.GradientDrawable();shape.setColor(0xffffffff);if(mask==RIPPLE_MASK_CIRCLE_20DP)shape.setShape(1);return new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(c),null,shape);}
}''')
    put('org/telegram/messenger/BuildConfig.java','package org.telegram.messenger; public class BuildConfig {public static boolean CONNECTED_ALPHA=true;}')
    put('org/telegram/messenger/AndroidUtilities.java','''package org.telegram.messenger; public class AndroidUtilities {
public static int dp2(float v){return dp(v);}public static float density=1;public static int dp(float v){return (int)Math.ceil(density*v);} public static float dpf2(float v){return density*v;}
public static android.graphics.Typeface bold(){return android.graphics.Typeface.create("sans-serif",1);}
}''')
    put('org/telegram/messenger/LiteMode.java','package org.telegram.messenger; public class LiteMode {public static boolean isPowerSaverApplied(){return false;}}')
    put('org/telegram/messenger/LocaleController.java','''package org.telegram.messenger; public class LocaleController {public static String getString(int id){
if(id==R.string.FlexyMusicCompact)return "Comprimir reproductor";
if(id==R.string.FlexyMusicExpand)return "Expandir reproductor";
return "Music action";}}''')
    put('org/telegram/messenger/MessageObject.java','''package org.telegram.messenger; public class MessageObject {
public int currentAccount,audioProgressSec;public float audioProgress; public boolean music=true;public String title="Alone",artist="Marshmello";
public boolean isMusic(){return music;} public int getId(){return 10;} public String getMusicTitle(){return title;} public String getMusicAuthor(){return artist;}
public Object getDocument(){return null;}
}''')
    put('org/telegram/messenger/MediaController.java','''package org.telegram.messenger; public class MediaController {
private static final MediaController I=new MediaController(); public static MediaController getInstance(){return I;}
public MessageObject message; public boolean paused; public int pauses,plays,nexts,stops;
public MessageObject getPlayingMessageObject(){return message;} public boolean isDownloadingCurrentMessage(){return false;} public boolean isMessagePaused(){return paused;}
public void playMessage(MessageObject m){plays++;paused=false;} public void pauseMessage(MessageObject m){pauses++;paused=true;}
public void playNextMessage(){nexts++;}public void cleanupPlayer(boolean a,boolean b){stops++;message=null;}
}''')
    put('org/telegram/messenger/FileLoader.java','package org.telegram.messenger; public class FileLoader {public static String getAttachFileName(Object o){return "fixture";}}')
    events=sorted(set(re.findall(r'NotificationCenter.(\w+)',code)) - {'getGlobalInstance','getInstance','NotificationCenterDelegate'})
    put('org/telegram/messenger/NotificationCenter.java','''package org.telegram.messenger; import java.util.*;
public class NotificationCenter {public interface NotificationCenterDelegate {void didReceivedNotification(int id,int account,Object... args);}
'''+''.join(f'public static final int {n}={i+1};' for i,n in enumerate(events))+'''
private static final NotificationCenter G=new NotificationCenter();private static final NotificationCenter[] A={new NotificationCenter(),new NotificationCenter(),new NotificationCenter()};
public static NotificationCenter getGlobalInstance(){return G;}public static NotificationCenter getInstance(int a){return A[a];}
public final Set<String> registrations=new HashSet<>();
public void addObserver(NotificationCenterDelegate d,int e){if(!registrations.add(System.identityHashCode(d)+":"+e))throw new AssertionError("duplicate observer");}
public void removeObserver(NotificationCenterDelegate d,int e){registrations.remove(System.identityHashCode(d)+":"+e);}
}''')
    put('org/telegram/messenger/UserConfig.java','package org.telegram.messenger; public class UserConfig {public static final int MAX_ACCOUNT_COUNT=3;}')
    put('org/telegram/ui/ActionBar/BaseFragment.java','''package org.telegram.ui.ActionBar; public class BaseFragment {
private android.view.View root;public BaseFragment(android.view.View v){root=v;}public android.view.View getFragmentView(){return root;}}
''')
    put('org/telegram/ui/Components/CubicBezierInterpolator.java','''package org.telegram.ui.Components; public class CubicBezierInterpolator implements android.animation.TimeInterpolator {
public CubicBezierInterpolator(double a,double b,double c,double d){}public float getInterpolation(float t){return t;}}
''')
    put('org/telegram/ui/Components/LayoutHelper.java','''package org.telegram.ui.Components;
import android.widget.*;import org.telegram.messenger.AndroidUtilities;public class LayoutHelper {
public static final int MATCH_PARENT=-1,WRAP_CONTENT=-2;private static int d(float v){return v<0?(int)v:AndroidUtilities.dp(v);}
public static FrameLayout.LayoutParams createFrame(float w,float h){return createFrame(w,h,0,0,0,0,0);}
public static FrameLayout.LayoutParams createFrame(float w,float h,int g){return createFrame(w,h,g,0,0,0,0);}
public static FrameLayout.LayoutParams createFrame(float w,float h,int g,float l,float t,float r,float b){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(d(w),d(h),g);p.setMargins(d(l),d(t),d(r),d(b));return p;}
public static LinearLayout.LayoutParams createLinear(float w,float h,float l,float t,float r,float b){return createLinear(w,h,0,0,l,t,r,b);}
public static LinearLayout.LayoutParams createLinear(float w,float h){return createLinear(w,h,0,0,0,0,0,0);}
public static LinearLayout.LayoutParams createLinear(float w,float h,int g){return createLinear(w,h,0,g,0,0,0,0);}
public static LinearLayout.LayoutParams createLinear(float w,float h,float weight,float l,float t,float r,float b){return createLinear(w,h,weight,0,l,t,r,b);}
public static LinearLayout.LayoutParams createLinear(float w,float h,int g,float l,float t,float r,float b){return createLinear(w,h,0,g,l,t,r,b);}
public static LinearLayout.LayoutParams createLinear(float w,float h,float weight,int g,float l,float t,float r,float b){LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(d(w),d(h),weight);p.gravity=g;p.setMargins(d(l),d(t),d(r),d(b));return p;}
}''')
    put('org/telegram/messenger/ImageLocation.java','package org.telegram.messenger; public class ImageLocation {}')
    put('org/telegram/ui/Components/BackupImageView.java','''package org.telegram.ui.Components; public class BackupImageView extends android.view.View {
private android.graphics.Bitmap bitmap;private final android.graphics.Paint paint=new android.graphics.Paint(2);private final android.graphics.Rect target=new android.graphics.Rect();
public BackupImageView(android.content.Context c){super(c);}public void setRoundRadius(int r){}public void setImageDrawable(Object o){bitmap=null;}public void setImageBitmap(android.graphics.Bitmap b){bitmap=b;}
@Override protected void onDraw(android.graphics.Canvas c){if(bitmap!=null){target.set(0,0,getWidth(),getHeight());c.drawBitmap(bitmap,null,target,paint);}}
public void setImage(Object a,Object b,Object c,Object d,Object e,int f,int g,Object h){}
public interface Delegate {void didSet(Receiver r,boolean set,boolean thumb,boolean mem);}
public class Receiver {public void setDelegate(Delegate d){}public android.graphics.Bitmap getBitmap(){return bitmap;}public boolean hasBitmapImage(){return bitmap!=null;}}
private Receiver r=new Receiver();public Receiver getImageReceiver(){return r;}}
''')
    put('app/exteraless/player/PlayerArt.java','''package app.exteraless.player; import org.telegram.messenger.*;import android.graphics.Bitmap;
public class PlayerArt {public static String key(MessageObject m){return "fixture"+System.identityHashCode(m);}public static Bitmap fileCover(MessageObject m){return null;}
public static ImageLocation fullLocation(MessageObject m){return null;}public static ImageLocation thumbLocation(MessageObject m){return null;}
public static boolean isPlaying(MessageObject m){return true;}public interface Callback {void seed(int s);}public static void requestSeed(MessageObject m,Bitmap b,int f,Callback c){throw new AssertionError("unexpected extraction");}}
''')
    put('app/exteraless/player/Md3Player.java','''package app.exteraless.player; public class Md3Player {public static boolean miniEnabled(){return true;}public static void open(org.telegram.ui.ActionBar.BaseFragment f,PlayerMiniView v){}}''')
    put('tw/nekomimi/nekogram/helpers/MonetHelper.java','package tw.nekomimi.nekogram.helpers; public class MonetHelper {public static Integer getColorOrNull(String s){return null;}}')
    # Legacy Material utilities are not reached by Connected Alpha. Fail if palette extraction runs.
    put('com/google/android/material/color/utilities/Hct.java','package com.google.android.material.color.utilities; public class Hct {public static Hct fromInt(int c){throw new AssertionError("legacy palette entered");}}')
    methods=sorted(set(re.findall(r's\.(get\w+)\(\)',(player/'PlayerColors.java').read_text())))
    put('com/google/android/material/color/utilities/DynamicScheme.java','package com.google.android.material.color.utilities; public class DynamicScheme {'+''.join('public int '+m+'(){throw new AssertionError();}' for m in methods)+'}')
    put('com/google/android/material/color/utilities/SchemeTonalSpot.java','package com.google.android.material.color.utilities; public class SchemeTonalSpot extends DynamicScheme {public SchemeTonalSpot(Hct h,boolean d,double c){throw new AssertionError();}}')
    put('com/google/android/material/color/utilities/QuantizerCelebi.java','package com.google.android.material.color.utilities; public class QuantizerCelebi {public static java.util.Map<Integer,Integer> quantize(int[] a,int b){throw new AssertionError();}}')
    put('com/google/android/material/color/utilities/Score.java','package com.google.android.material.color.utilities; public class Score {public static java.util.List<Integer> score(java.util.Map<Integer,Integer> a,int b,int c,boolean d){throw new AssertionError();}}')
    # Actual current PlayerLayout source copied byte-for-byte into a fixture host.
    sheet=(player/'PlayerSheet.java').read_text();start=sheet.index('    private class PlayerLayout extends ViewGroup'); layout=sheet[start:sheet.rfind('\n}')]
    fixture=(Path(__file__).parent/'LayoutFixture.java.in').read_text().replace('_LAYOUT_',layout)
    put('app/exteraless/player/LayoutFixture.java',fixture)

    # Extract the real context measurement contract; other chat/translation dependencies
    # are explicit plain Views in the test, not a full Telegram chat simulation.
    context=(root/'TMessagesProj/src/main/java/org/telegram/ui/Components/FragmentContextView.java').read_text()
    def method(anchor):
        a=context.index('\n    '+anchor)+5;o=context.index('{',a);n=1;b=o+1
        while n:
            n+=(context[b]=='{')-(context[b]=='}');b+=1
        return context[a:b]
    body=method('protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec)')+'\n'+method('public int getStyleHeight()')
    put('app/exteraless/player/NativeContextMeasure.java','package app.exteraless.player; import android.content.Context; import android.widget.FrameLayout; import org.telegram.messenger.AndroidUtilities; public class NativeContextMeasure extends FrameLayout { public int currentStyle;public boolean md3Music=true;private static final int STYLE_INACTIVE_GROUP_CALL=2;public NativeContextMeasure(Context c){super(c);}void updateJoinButtonWidth(int width){}'+body+'}')
