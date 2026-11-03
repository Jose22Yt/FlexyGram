"""Execute the current beta's channel glass routing with deterministic drawing doubles."""
import pathlib
import shutil
import subprocess
import tempfile

import pytest
from test_composer_layout import method


@pytest.mark.skipif(not shutil.which('javac') or not shutil.which('java'), reason='JDK required')
def test_channel_uses_contact_native_glass_without_opaque_overlay():
    root = pathlib.Path(__file__).resolve().parents[1]
    source = (root/'TMessagesProj/src/main/java/org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    draw = method(source, 'private void drawSignatureChannelBackground(Canvas canvas)')
    draw = draw.replace('org.telegram.messenger.LiteMode', 'LiteMode').replace('org.telegram.messenger.SharedConfig', 'SharedConfig')
    harness = '''
import java.util.*;
public class ChannelGlassRegression {
    static class Rect {}
    static class RectF {
        float left,top,right,bottom;
        void set(RectF r){left=r.left;top=r.top;right=r.right;bottom=r.bottom;}
        void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}
        boolean isEmpty(){return right<=left||bottom<=top;}
        void union(RectF r){left=Math.min(left,r.left);right=Math.max(right,r.right);top=Math.min(top,r.top);bottom=Math.max(bottom,r.bottom);}
        void inset(float x,float y){left+=x;right-=x;top+=y;bottom-=y;}
        void round(Rect r){}
    }
    static class Path {enum Direction{CW}void rewind(){}void addRoundRect(RectF r,float x,float y,Direction d){}}
    static class Paint {
        enum Style{STROKE}int alpha=255;
        void setColor(int c){alpha=(c>>>24);}int getAlpha(){return alpha;}
        void setAlpha(int a){alpha=a;}void setStyle(Style s){}void setStrokeWidth(float w){}
    }
    static class Canvas {
        boolean hardware=true;List<String> draws=new ArrayList<>();
        boolean isHardwareAccelerated(){return hardware;}
        void save(){}void restore(){}void clipPath(Path p){}
        void drawRoundRect(RectF r,float x,float y,Paint paint){draws.add("fill");}
    }
    static class Color {static int WHITE=-1;}
    static class ColorUtils {static double calculateLuminance(int c){return 1;}static int setAlphaComponent(int c,int a){return (c&0xffffff)|(a<<24);}}
    static class AndroidUtilities {static float density=1;}
    static class LiteMode {static final int FLAG_CHAT_BLUR=1;static boolean enabled=true;static boolean isEnabled(int flag){return enabled;}}
    static class SharedConfig {static boolean enabled=true;static boolean chatBlurEnabled(){return enabled;}}
    static class app {
        static class exteraless {static class appearance {static class FlexyGlassConfig {static boolean enabled(){return false;}}}}
        static class flexygram {static class composer {static class ComposerStyle {static int surface(boolean dark,boolean glass){return -1;}}}}
    }
    static class Drawable {int getAlpha(){return 255;}void setBounds(Rect r){}void draw(Canvas c){c.draws.add("legacy");}}
    static class View {float getX(){return 0;}float getY(){return 0;}}
    static class Channels extends View {
        boolean left=true,right=true;
        void getSignatureBounds(RectF m,RectF l,RectF r){m.left=60;m.right=440;m.bottom=44;l.right=left?44:0;l.bottom=44;r.left=456;r.right=right?500:456;r.bottom=44;}
        int getSignatureVisualInset(){return 0;}int getSignatureSurfaceColor(){return -1;}float getSignatureAlpha(){return 1;}
    }
    final RectF signatureChannelMiddle=new RectF(),signatureChannelLeft=new RectF(),signatureChannelRight=new RectF();
    final RectF signatureChannelLastMiddle=new RectF(),signatureChannelLastLeft=new RectF(),signatureChannelLastRight=new RectF();
    final Path signatureChannelMask=new Path();final RectF tmpRectF=new RectF();final Rect tmpRect=new Rect();
    final Paint flexySurface=new Paint(),flexyPearl=new Paint();
    final Drawable blurredBackgroundDrawable=new Drawable();Drawable[] compactGlass={new Drawable()};
    final Channels flexyChannels=new Channels();final View inputIslandBubbleContainer=new View();boolean flexyPearlGlass;
    int dp(float n){return Math.round(n);}
    void drawCompactGlass(Canvas canvas,int index,RectF r,float radius){canvas.draws.add("native"+index);}
    DRAW
    static void require(boolean ok,String message){if(!ok)throw new AssertionError(message);}
    public static void main(String[] args){
        ChannelGlassRegression c=new ChannelGlassRegression();Canvas canvas=new Canvas();
        c.drawSignatureChannelBackground(canvas);
        require(canvas.draws.equals(List.of("native0","native1","native2")),"all channel capsules must use native blur/border with no opaque fill");
        c.flexyChannels.left=false;Canvas noLeft=new Canvas();c.drawSignatureChannelBackground(noLeft);
        require(noLeft.draws.equals(List.of("native0","native2")),"hidden actions must not leave a background");
        LiteMode.enabled=false;Canvas disabled=new Canvas();c.drawSignatureChannelBackground(disabled);
        require(!disabled.draws.contains("native0")&&disabled.draws.contains("fill"),"respect disabled blur setting");
        LiteMode.enabled=true;Canvas software=new Canvas();software.hardware=false;c.drawSignatureChannelBackground(software);
        require(software.draws.contains("fill")&&!software.draws.contains("native0"),"software rendering keeps readable fallback");
        c.compactGlass[0]=null;Canvas missing=new Canvas();c.drawSignatureChannelBackground(missing);
        require(missing.draws.contains("fill"),"safe fallback before native source is prepared");
    }
}
'''.replace('DRAW', draw)
    with tempfile.TemporaryDirectory(prefix='flexygram-beta-channel-') as directory:
        file = pathlib.Path(directory)/'ChannelGlassRegression.java';file.write_text(harness)
        result=subprocess.run(['javac','-d',directory,str(file)],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
        result=subprocess.run(['java','-cp',directory,'ChannelGlassRegression'],capture_output=True,text=True)
        assert result.returncode==0,result.stderr
