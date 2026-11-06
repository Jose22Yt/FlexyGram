import importlib.util

def write(dest,root):
    spec=importlib.util.spec_from_file_location('bubble_host',root/'tools/connected_alpha/bubble_visual/stubs.py')
    host=importlib.util.module_from_spec(spec);spec.loader.exec_module(host)
    stubs=dict(host.STUBS)
    stubs['org/telegram/ui/ActionBar/Theme.java']=stubs['org/telegram/ui/ActionBar/Theme.java'].replace(
        'public static final int key_chat_inBubble=1;',
        'public static final int key_chat_serviceBackground=120,key_chat_serviceBackgroundSelected=121; public static final int key_chat_inBubble=1;').replace(
        'public static int getColor(int k){',
        'public static int getColor(int k){if(k==120)return dark?0xff223344:0xffaabbcc;if(k==121)return dark?0xff334455:0xff99aabb;')
    stubs['org/telegram/ui/ActionBar/Theme.java']=stubs['org/telegram/ui/ActionBar/Theme.java'].replace(
        'public class Theme {', """public class Theme {
 public static final String key_paint_chatActionBackground="normal",key_paint_chatActionBackgroundSelected="selected",key_paint_chatActionBackgroundDarken="darken",key_paint_chatActionText="ink";
 public static final android.graphics.Paint normal=new android.graphics.Paint(3),selected=new android.graphics.Paint(3),darken=new android.graphics.Paint(3),ink=new android.graphics.Paint(3);
 public static void applyServiceShaderMatrix(int w,int h,float x,float y){}
 public static boolean hasGradientService(){return false;}
 public static android.graphics.Paint getThemePaint(String key,ResourcesProvider p){return key.equals("normal")?normal:key.equals("selected")?selected:key.equals("darken")?darken:ink;}
 """).replace('default int getCurrentColor', 'default void applyServiceShaderMatrix(int w,int h,float x,float y){} default boolean hasGradientService(){return false;} default int getCurrentColor')
    for name,source in stubs.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
    java=root/'TMessagesProj/src/main/java'
    for name in ['org/telegram/ui/ActionBar/MessageDrawable.java','org/telegram/ui/Components/blur3/utils/NinePatchBuilder.java',
                 'app/flexygram/bubbles/BubbleConfig.java','app/flexygram/bubbles/BubbleStyle.java',
                 'app/flexygram/bubbles/SignatureWallpaperBlur.java','app/flexygram/bubbles/ServiceBubbleSurface.java',
                 'app/flexygram/bubbles/BubbleOutline.java','app/flexygram/bubbles/BubbleFusion.java',
                 'app/flexygram/bubbles/SignatureBorderPath.java']:
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);source=(java/name).read_text()
        if name.endswith('SignatureBorderPath.java'):
            source=source.replace('public final class SignatureBorderPath {','public final class SignatureBorderPath { public static long testRebuilds;').replace('result.rewind();','testRebuilds++;result.rewind();')
        p.write_text(source)
