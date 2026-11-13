"""Resource release regression using the actual owner cleanup method; no APK required."""
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_blur_clear_drops_optional_snapshot_without_recycling_recorded_images(tmp_path):
    source=(JAVA/'app/flexygram/bubbles/SignatureWallpaperBlur.java').read_text()
    clear=method(source,'private void clear()')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 Object source=new Object(),snapshotSource=new Object(),staticSnapshot=new Object();
 boolean supported=true,ready=true;int releases,invalidations;
 boolean isReady(){return ready;}void release(){releases++;ready=false;}
 void invalidateVisual(){invalidations++;}
 CLEAR
 public static void main(String[]args){Probe p=new Probe();p.clear();
 if(p.source!=null||p.snapshotSource!=null||p.staticSnapshot!=null||p.supported||p.releases!=1||p.invalidations!=1)throw new AssertionError();
 p.clear();if(p.releases!=2||p.invalidations!=1)throw new AssertionError();
 }}'''.replace('CLEAR',clear)})
    assert '.recycle(' not in clear


def test_preview_material_changes_repaint_without_rebuilding_text_layout(tmp_path):
    source=(JAVA/'app/flexygram/bubbles/BubblePreviewView.java').read_text()
    body=method(source,'public void settingsChanged()').replace('org.telegram.messenger.BuildConfig.CONNECTED_ALPHA','BuildConfig.CONNECTED_ALPHA')
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class Paint {float spacing=12;void set(Paint p){spacing=p.spacing;}void setTextSize(float s){spacing=s;}float getFontSpacing(){return spacing;}}
 static class Theme{static Paint chat_timePaint=new Paint();static int key_chat_outSentCheckRead=1,key_windowBackgroundGray=2;static int getColor(int k){return k;}}
 static class AndroidUtilities{static float dpf2(float n){return n;}}
 static class BubbleConfig{static boolean small;static boolean smallTimestamps(){return small;}static boolean adaptive(){return true;}}
 static class ServiceBubbleSurface{static int textColor(Object o){return 3;}}
 static class BuildConfig{static boolean CONNECTED_ALPHA;}
 static class R{static class drawable{static final int flexy_check_ios27=1,msg_check_s=2,flexy_halfcheck_ios27=3,msg_halfcheck=4;}}
 static class Drawable{void setTint(int n){}Drawable mutate(){return this;}}
 static class Resources{int loads;Drawable getDrawable(int id){loads++;return new Drawable();}}
 boolean signatureTicks;Resources resources=new Resources();Resources getResources(){return resources;}
 static class Owner{void prepare(Object w,boolean m,int c){}}
 Paint time=new Paint();int measuredWidth=300,checkColor,layouts,draws;
 Drawable check=new Drawable(),halfCheck=new Drawable();Owner blurOwner;Object wallpaper;boolean wallpaperMotion;
 void requestLayout(){layouts++;}void invalidate(){draws++;}
 BODY
 public static void main(String[]args){Probe p=new Probe();for(int i=0;i<1000;i++)p.settingsChanged();
 if(p.layouts!=0||p.draws!=1000||p.measuredWidth!=300||p.resources.loads!=0)throw new AssertionError();
 BuildConfig.CONNECTED_ALPHA=true;p.settingsChanged();if(p.resources.loads!=2||p.layouts!=0)throw new AssertionError();
 p.settingsChanged();if(p.resources.loads!=2)throw new AssertionError();
 BubbleConfig.small=true;p.settingsChanged();if(p.layouts!=1||p.measuredWidth!=-1)throw new AssertionError();
 p.measuredWidth=300;p.settingsChanged();if(p.layouts!=1)throw new AssertionError();
 BubbleConfig.small=false;p.settingsChanged();if(p.layouts!=2)throw new AssertionError();
 }}'''.replace('BODY',body)})
