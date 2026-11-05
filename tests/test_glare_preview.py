"""Run real compact glare preview geometry; device pixels are not measured here."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_three_shapes_fit_compact_segment_across_densities_and_widths(tmp_path):
    source=(JAVA/'app/flexygram/effects/GlarePreviewView.java').read_text()
    size=method(source,'protected void onSizeChanged(').replace('super.onSizeChanged(w,h,ow,oh);','')
    measure=method(source,'protected void onMeasure(')
    probe(tmp_path,{'Probe.java':'''public class Probe {
 static class RectF{float l,t,r,b;void set(float a,float c,float d,float e){l=a;t=c;r=d;b=e;}}
 static class Path{static class Direction{static Object CW;}void rewind(){}void addRoundRect(RectF r,float a,float b,Object d){}}
 static class Wallpaper{void resize(int w,int h){}}
 static class MeasureSpec{static int getSize(int w){return w;}}
 static class AndroidUtilities{static float density=1;}
 RectF frame=new RectF();Path clip=new Path();Wallpaper wallpaper=new Wallpaper();
 RectF[] shapes={new RectF(),new RectF(),new RectF()};float[] radii=new float[3];int height;
 int dp(float f){return (int)Math.ceil(f*AndroidUtilities.density);}void setMeasuredDimension(int w,int h){height=h;}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();
 for(float density:new float[]{1,1.5f,2,3})for(int width:new int[]{180,240,360,600}){
 AndroidUtilities.density=density;int w=p.dp(width);p.onMeasure(w,0);check(p.height==p.dp(64));p.onSizeChanged(w,p.height,0,0);
 for(int i=0;i<3;i++){RectF r=p.shapes[i];check(r.l>=p.frame.l&&r.r<=p.frame.r&&r.t>=p.frame.t&&r.b<=p.frame.b&&p.radii[i]>0);}
 check(p.shapes[0].r<p.shapes[1].l&&p.shapes[1].r<p.shapes[2].l);
 }
 }
}'''.replace('METHODS',size+'\n'+measure)})


def test_preview_uses_existing_outline_and_wallpaper_lifecycle_without_extra_controls():
    source=(JAVA/'app/flexygram/effects/GlarePreviewView.java').read_text()
    section=(JAVA/'app/flexygram/effects/GlareSettingsSection.java').read_text()
    assert 'BlurredBackgroundDrawable.drawStroke' in source and 'GlassOutlineStyle.Listener' in source
    assert 'wallpaper.attach()' in source and 'wallpaper.close()' in source and 'wallpaper.refresh()' in source
    assert 'center.removeObserver' in source and 'isAttachedToWindow())invalidate()' in source
    assert 'previewRow=addRow()' in section and 'type!=PREVIEW&&super.isSectionContent(type)' in section
    assert 'new GlarePreviewView(parent.getContext(),resourcesProvider)' in section
    draw=method(source,'protected void onDraw(')
    for forbidden in ['new ','requestLayout','drawText','postOnAnimation','setShadowLayer']:
        assert forbidden not in draw
