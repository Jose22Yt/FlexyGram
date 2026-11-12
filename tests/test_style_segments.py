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


def test_gallery_has_one_live_preview_and_compact_native_style_choices():
    gallery=(JAVA/'app/flexygram/settings/signature/ConversationStyleSettingsActivity.java').read_text()
    picker=(JAVA/'app/flexygram/settings/signature/CompactStylePicker.java').read_text()
    assert 'HorizontalScrollView' not in gallery and 'scrollTo(' not in gallery
    assert 'new CompactStylePicker(context,resourcesProvider,livePreview,2)' in gallery
    assert 'HeaderConfig.style(style)' in gallery and 'FlexyComposerConfig.setStyle(style)' in gallery
    assert 'new HeaderPreviewView(context,style,true)' in gallery and 'createStyleMiniature(context,style)' in gallery
    assert 'info.setChecked(isSelected())' in picker and 'label.setText(name)' in picker
    assert 'fontScale' in picker and 'LocaleController.isRTL' in picker
    for path in ['header/HeaderPreviewView.java','composer/FlexyComposerSettingsActivity.java']:
        preview=(JAVA/'app/flexygram'/path).read_text()
        assert 'if(miniature)return;' in preview
        assert 'NotificationCenter.didSetNewWallpapper' in preview
        assert 'wallpaperPreview.refresh()' in preview and 'wallpaperPreview.close()' in preview
