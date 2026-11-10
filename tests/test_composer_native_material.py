"""Native composer material is drawn once, as in the header. No GPU/FPS claim."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_composer_native_islands_do_not_overpaint_the_native_material(tmp_path):
    source = (JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    draw = method(source, 'private void drawFlexyNativeGlassIslands(')
    compact = method(source, 'private void drawCompactGlass(')
    probe(tmp_path, {'Probe.java': '''public class Probe {
        static class RectF {float left,top,right,bottom;
            RectF(){}RectF(float l,float t,float r,float b){left=l;top=t;right=r;bottom=b;}
            void offset(float x,float y){left+=x;right+=x;top+=y;bottom+=y;}
            void setEmpty(){left=top=right=bottom=0;}
        }
        // The compositor may only invoke the native drawables. A manual Canvas
        // paint here would require a second material layer and fail this compile.
        static class Canvas {int calls;int[] material=new int[4];}
        static class BlurredBackgroundDrawable {
            int alpha=255,material,radiusChanges,draws;float radius;int l,t,r,b,index;
            BlurredBackgroundDrawable(int index){this.index=index;}
            void setRadius(float r){radius=r;radiusChanges++;}void setAlpha(int a){alpha=a;}int getAlpha(){return alpha;}
            void setBounds(int l,int t,int r,int b){this.l=l;this.t=t;this.r=r;this.b=b;}
            void draw(Canvas c){draws++;c.calls++;c.material[index]=material;}
        }
        static class Composer {boolean voice,send;
            boolean getFlexyVoiceBounds(RectF out){out.left=240;out.top=2;out.right=280;out.bottom=42;return voice;}
            boolean getFlexySendBounds(RectF out){out.left=240;out.top=2;out.right=280;out.bottom=42;return send;}
        }
        final Composer flexyComposer=new Composer();
        final BlurredBackgroundDrawable blurredBackgroundDrawable=new BlurredBackgroundDrawable(0);
        final BlurredBackgroundDrawable[] compactGlass={new BlurredBackgroundDrawable(0),new BlurredBackgroundDrawable(1),new BlurredBackgroundDrawable(2),new BlurredBackgroundDrawable(3)};
        final boolean[] compactGlassDrawn=new boolean[4];final float[] compactGlassRadius={-1,-1,-1,-1};
        RectF flexyPill=new RectF(52,2,230,42),flexyAttach=new RectF(2,2,42,42),flexyVoice=new RectF(),flexySend=new RectF(),flexyLastPill=new RectF();
        boolean flexySendDrawn,flexyVoiceDrawn,flexyNativeGlassDrawn;
        COMPACT
        DRAW
        static void check(boolean v){if(!v)throw new AssertionError();}
        public static void main(String[] args){
            for(boolean voice:new boolean[]{false,true})for(boolean send:new boolean[]{false,true})for(boolean attach:new boolean[]{false,true})
                for(int material:new int[]{0x8cffffff,0xc1303236,0xd8303236,0xff223344})for(int alpha:new int[]{0,128,255}){
                    Probe p=new Probe();p.flexyComposer.voice=voice;p.flexyComposer.send=send;p.blurredBackgroundDrawable.alpha=alpha;
                    for(BlurredBackgroundDrawable d:p.compactGlass)d.material=material;
                    Canvas c=new Canvas();p.drawFlexyNativeGlassIslands(c,5,10,20,attach);
                    check(c.calls==1+(voice?1:0)+(send?1:0)+(attach?1:0));
                    check(p.flexyNativeGlassDrawn&&p.flexyVoiceDrawn==voice&&p.flexySendDrawn==send);
                    for(int i=0;i<4;i++)if(p.compactGlassDrawn[i])check(c.material[i]==material&&p.compactGlass[i].alpha==alpha);
                    check(p.compactGlass[0].l==52&&p.compactGlass[0].r==230);
                    if(voice)check(p.compactGlass[2].l==245&&p.compactGlass[2].t==12);
                    Canvas next=new Canvas();for(int j=0;j<10000;j++)p.drawFlexyNativeGlassIslands(next,5,10,20,attach);
                    for(int i=0;i<4;i++)if(p.compactGlassDrawn[i])check(p.compactGlass[i].radiusChanges==1);
                }
        }
    }'''.replace('COMPACT',compact).replace('DRAW',draw)})


def test_composer_keeps_native_policy_and_solid_fallback():
    source = (JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    draw = method(source, 'private void drawFlexyCompactBackground(')
    assert 'canvas.isHardwareAccelerated()' in draw
    assert 'flexyComposer.flexyNativeGlassIslandsAvailable()' in draw
    assert draw.index('drawFlexyNativeGlassIslands(') < draw.index('if (flexyPearlGlass')
    assert 'ComposerStyle.surface(' in draw
    assert 'drawFlexyComposerTint' not in source
    policy = method(source, 'public void updateNativeLiquidGlassPolicy(')
    assert 'for (BlurredBackgroundDrawable drawable : compactGlass)' in policy
    assert 'flexyComposer.invalidateNativeGlassColors()' in policy
