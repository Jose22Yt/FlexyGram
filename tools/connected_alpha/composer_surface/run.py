"""Production composer surface methods with real Android raster graphics; no APK."""
from pathlib import Path
import importlib.util,sys
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('surface_pipeline',HERE.parent/'music_visual/run.py')
pipeline=importlib.util.module_from_spec(spec);spec.loader.exec_module(pipeline)
def method(s,anchor):
    start=s.index(anchor);pos=s.index('{',start)+1;depth=1
    while depth:
        depth+=(s[pos]=='{')-(s[pos]=='}');pos+=1
    return s[start:pos]
def write(source,root):
    java=root/'TMessagesProj/src/main/java'
    def put(path,text):
        p=source/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    for name in ['ComposerStyle','ComposerGeometry']:
        path='app/flexygram/composer/'+name+'.java';put(path,(java/path).read_text())
    s=(java/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    methods='\n'.join(method(s,a) for a in ['private void drawFlexyComposerTint(', 'private void drawFlexyNativeGlassIslands('])
    put('SurfaceProbe.java','''import android.graphics.*;
public class SurfaceProbe {
 static class AndroidUtilities{static float density=1;}
 static class Theme{static int key_chat_messagePanelBackground;}
 static class ColorUtils{static int setAlphaComponent(int c,int a){return(c&0xffffff)|(a<<24);}}
 static class Composer{int color=Color.WHITE;boolean voice=true,send;boolean backdrop;
  int getThemedColor(int k){return color;}boolean getFlexyVoiceBounds(RectF r){r.set(240,2,280,42);return voice;}
  boolean getFlexySendBounds(RectF r){r.set(240,2,280,42);return send;}
  void setFlexyNativeGlassBackdropDrawn(boolean b){backdrop=b;}}
 static class Background{int alpha=255;int getAlpha(){return alpha;}}
 final Composer flexyComposer=new Composer();final Background blurredBackgroundDrawable=new Background();
 final Paint flexySurface=new Paint(3);final RectF tmpRectF=new RectF(),flexyPill=new RectF(52,2,230,42),flexyAttach=new RectF(2,2,42,42),flexyVoice=new RectF(),flexySend=new RectF(),flexyLastPill=new RectF();
 boolean flexySendDrawn,flexyVoiceDrawn;int sourceDraws;boolean emptySource=true;
 void drawCompactGlass(Canvas c,int i,RectF b,float r){sourceDraws++;if(!emptySource){Paint p=new Paint();p.setColor(0xffdddddd);c.drawRoundRect(b,r,r,p);}}
 METHODS
 public void draw(Canvas c){drawFlexyNativeGlassIslands(c,0,0,20,true);}
}'''.replace('METHODS',methods))
if __name__=='__main__':
    if '--output-dir' not in sys.argv:sys.argv+=['--output-dir',str(HERE.parents[2]/'build/connected-alpha-composer-surface')]
    raise SystemExit(pipeline.main(here=HERE,test_class='ComposerSurfaceTest',stubs_writer=write))
