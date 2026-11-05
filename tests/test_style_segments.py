"""Execute segment clipping geometry and guard vertical full-width gallery wiring."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_grouped_segment_preserves_thin_frame_and_clips_wallpaper(tmp_path):
    source=(JAVA/'app/flexygram/settings/signature/StylePreviewCard.java').read_text()
    methods='\n'.join(method(source,s) for s in ['public void setSegmentEdges(', 'private void updateClip()'])
    probe(tmp_path,{'Probe.java':'''public class Probe {
 boolean first,last;float density=1;int width=360,height=68;
 float[] corners=new float[8];Frame frame=new Frame();Rect clipBounds=new Rect();Path clip=new Path();
 static class Rect {float l,t,r,b;void set(float l,float t,float r,float b){this.l=l;this.t=t;this.r=r;this.b=b;}}
 static class Frame {float[] radii;void setCornerRadii(float[] f){radii=f.clone();}}
 static class Path {static class Direction{static Object CW;}float[] radii;void rewind(){}void addRoundRect(Rect r,float[] f,Object d){radii=f.clone();}}
 int dp(int n){return Math.round(n*density);}int getWidth(){return width;}int getHeight(){return height;}void invalidate(){}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();
 for(float density:new float[]{1,1.5f,2,3})for(boolean first:new boolean[]{false,true})for(boolean last:new boolean[]{false,true}){
 p.density=density;p.setSegmentEdges(first,last);
 check(p.frame.radii[0]==p.dp(first?28:6)&&p.frame.radii[7]==p.dp(last?28:6));
 check(p.clip.radii[0]==p.dp(first?26:4)&&p.clip.radii[7]==p.dp(last?26:4));
 check(p.clipBounds.l==p.dp(2)&&p.clipBounds.r==p.width-p.dp(2));
 }
 p.width=p.height=0;p.updateClip();check(p.clipBounds.l==p.clipBounds.r&&p.clipBounds.t==p.clipBounds.b);
 }
}'''.replace('METHODS',methods)})


def test_gallery_is_vertical_full_width_with_native_selection_and_wallpaper_updates():
    gallery=(JAVA/'app/flexygram/settings/signature/ConversationStyleSettingsActivity.java').read_text()
    card=(JAVA/'app/flexygram/settings/signature/StylePreviewCard.java').read_text()
    assert 'HorizontalScrollView' not in gallery and 'scrollTo(' not in gallery
    assert 'strip.setOrientation(VERTICAL)' in gallery
    assert 'LayoutParams params=new LayoutParams(-1,-2)' in gallery
    assert 'setSegmentEdges(i==0,i==styles.length-1)' in gallery
    assert 'HeaderConfig.style(styles[index])' in gallery and 'FlexyComposerConfig.setStyle(styles[index])' in gallery
    assert 'TextView' not in card and 'setPadding(dp(2),dp(2),dp(2),dp(2))' in card
    assert 'info.setContentDescription(name)' in card and 'info.setChecked(isSelected())' in card
    for path in ['header/HeaderPreviewView.java','composer/FlexyComposerSettingsActivity.java']:
        preview=(JAVA/'app/flexygram'/path).read_text()
        assert 'NotificationCenter.didSetNewWallpapper' in preview
        assert 'wallpaperPreview.refresh()' in preview and 'wallpaperPreview.close()' in preview
