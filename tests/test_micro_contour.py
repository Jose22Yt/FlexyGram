"""Execute the new contour and width transitions; these are JVM probes, not an APK."""
from pathlib import Path
from test_render_work_reuse import probe,JAVA
from test_composer_layout import method
ROOT=Path(__file__).resolve().parents[1]
B=JAVA/'org/telegram/ui/Components/blur3'


def test_legacy_enum_values_round_trip_and_new_mode_is_appended(tmp_path):
    files={
        'org/telegram/ui/Components/blur3/GlassOutlineStyle.java':(B/'GlassOutlineStyle.java').read_text(),
        'com/exteragram/messenger/GlassOutlineStyle.java':(JAVA/'com/exteragram/messenger/GlassOutlineStyle.java').read_text(),
        'app/flexygram/effects/GlareMode.java':(JAVA/'app/flexygram/effects/GlareMode.java').read_text(),
        'app/exteraless/appearance/AppearanceConfig.java':'package app.exteraless.appearance;public class AppearanceConfig{public static int value;public static int glassOutlineStyle(){return value;}}',
        'Probe.java':'''import app.flexygram.effects.GlareMode;import org.telegram.ui.Components.blur3.GlassOutlineStyle;import app.exteraless.appearance.AppearanceConfig;
public class Probe{public static void main(String[]args){
 for(int stored=0;stored<4;stored++){if(GlareMode.toStored(GlareMode.fromStored(stored))!=stored)throw new AssertionError();AppearanceConfig.value=stored;if(GlassOutlineStyle.current().ordinal()!=stored||com.exteragram.messenger.GlassOutlineStyle.values()[stored].ordinal()!=stored)throw new AssertionError();}
 if(GlareMode.toStored(GlareMode.DEFAULT)!=0||GlareMode.toStored(GlareMode.SOLID)!=1||GlareMode.toStored(GlareMode.DISABLED)!=2||GlareMode.toStored(GlareMode.MICRO)!=3)throw new AssertionError("saved values reinterpreted");
 for(int bad:new int[]{-1,4,100}){AppearanceConfig.value=bad;if(GlassOutlineStyle.current()!=GlassOutlineStyle.GLARE||GlareMode.fromStored(bad)!=GlareMode.DEFAULT)throw new AssertionError("unsafe fallback");}
 }}'''}
    probe(tmp_path,files,[])


def test_micro_outline_is_single_thin_dark_stroke_and_restores_paint_on_failure(tmp_path):
    files={
        'org/telegram/ui/Components/blur3/StaticOutlineStroke.java':(B/'StaticOutlineStroke.java').read_text(),
        'org/telegram/ui/Components/blur3/MicroContourStroke.java':(B/'MicroContourStroke.java').read_text(),
        'org/telegram/ui/Components/blur3/GlareStrokeWidth.java':(B/'GlareStrokeWidth.java').read_text(),
        'org/telegram/ui/Components/blur3/GlassOutlineStyle.java':'package org.telegram.ui.Components.blur3;public enum GlassOutlineStyle{GLARE,SOLID,HIDDEN,MICRO}',
        'org/telegram/messenger/AndroidUtilities.java':'package org.telegram.messenger;public class AndroidUtilities{public static float density=1;public static float dpf2(float v){return v*density;}}',
        'android/graphics/Shader.java':'package android.graphics;public class Shader{}',
        'android/graphics/RectF.java':'package android.graphics;public class RectF{public void set(float a,float b,float c,float d){}}',
        'android/graphics/Path.java':'package android.graphics;public class Path{public enum Direction{CW}public void rewind(){}public void addRoundRect(RectF r,float[] radii,Direction d){for(float x:radii)if(x<0)throw new AssertionError("negative radius");}}',
        'android/graphics/Paint.java':'''package android.graphics;public class Paint{public enum Style{STROKE,FILL}public Style style=Style.FILL;public float width=7;public int color=0xffabcdef;public Shader shader=new Shader();public Style getStyle(){return style;}public void setStyle(Style s){style=s;}public float getStrokeWidth(){return width;}public void setStrokeWidth(float w){width=w;}public Shader getShader(){return shader;}public void setShader(Shader s){shader=s;}public int getColor(){return color;}public void setColor(int c){color=c;}}''',
        'android/graphics/Canvas.java':'''package android.graphics;public class Canvas{public int calls,color;public float width;public boolean fail;private void capture(Paint p){calls++;color=p.color;width=p.width;if(p.style!=Paint.Style.STROKE||p.shader!=null)throw new AssertionError("wrong paint");if(fail)throw new IllegalStateException("canvas");}public void drawRoundRect(float a,float b,float c,float d,float e,float f,Paint p){capture(p);}public void drawPath(Path path,Paint p){capture(p);}}''',
        'Probe.java':'''import android.graphics.*;import org.telegram.ui.Components.blur3.*;import org.telegram.messenger.AndroidUtilities;
public class Probe{static void check(boolean v){if(!v)throw new AssertionError();}public static void main(String[]args){
 for(float density:new float[]{1,2,3,4})for(boolean array:new boolean[]{false,true})for(boolean fail:new boolean[]{false,true}){
 AndroidUtilities.density=density;Canvas c=new Canvas();c.fail=fail;Paint p=new Paint();int color=p.color;Shader shader=p.shader;
 try{if(array)StaticOutlineStroke.drawOverride(c,0,0,80,40,new float[]{10,10,5,5,2,2,0,0},true,p,GlassOutlineStyle.MICRO);else StaticOutlineStroke.drawOverride(c,0,0,80,40,10,true,p,GlassOutlineStyle.MICRO);check(!fail);}catch(IllegalStateException e){check(fail);}
 check(c.calls==1&&c.color==MicroContourStroke.COLOR&&c.width==Math.max(1,density*.35f));check(p.color==color&&p.width==7&&p.shader==shader&&p.style==Paint.Style.FILL);
 int old=c.calls;StaticOutlineStroke.drawOverride(c,0,0,80,40,10,false,p,GlassOutlineStyle.MICRO);check(c.calls==old);
 }
 Canvas c=new Canvas();Paint p=new Paint();p.color=0x080000ff;StaticOutlineStroke.drawOverride(c,0,0,20,20,10,true,p,GlassOutlineStyle.MICRO);check(c.color==0x08000000&&p.color==0x080000ff);
 check(!StaticOutlineStroke.drawOverride(c,0,0,20,20,10,true,p,GlassOutlineStyle.GLARE));
 }}'''}
    probe(tmp_path,files,[])


def test_mode_switches_reset_cached_width_without_compounding_or_idle_rebuilds(tmp_path):
    source=(B/'drawable/BlurredBackgroundDrawable.java').read_text()
    methods=method(source,'public void setStrokeWidth(')+method(source,'private void applyOutlineWidth(')
    probe(tmp_path,{
        'org/telegram/ui/Components/blur3/MicroContourStroke.java':'package org.telegram.ui.Components.blur3;public class MicroContourStroke{public static float widthPx(){return 1;}}',
        'Probe.java':'''public class Probe{
 static class Props{float strokeWidthTop,strokeWidthBottom,strokeWidthFull;boolean microContour;int builds;void build(){builds++;}}
 Props boundProps=new Props();float baseStrokeWidthTop,baseStrokeWidthBottom;void onBoundPropsChanged(){}
 METHODS
 public static void main(String[]args){Probe p=new Probe();p.setStrokeWidth(3,2);float legacy=p.boundProps.strokeWidthFull;p.boundProps.microContour=true;p.setStrokeWidth(3,2);if(p.boundProps.strokeWidthFull!=1)throw new AssertionError();int builds=p.boundProps.builds;for(int i=0;i<1000;i++)p.setStrokeWidth(3,2);if(p.boundProps.builds!=builds)throw new AssertionError("idle rebuilds");p.boundProps.microContour=false;p.setStrokeWidth(3,2);if(p.boundProps.strokeWidthFull!=legacy)throw new AssertionError("legacy width lost");}
 }'''.replace('METHODS',methods)},[B/'GlareStrokeWidth.java'])
    assert 'ninePatchHashBuilder.add(boundProps.microContour)' in source
    assert 'if(microContour)for(int i=0;i<8;i++)tmpRadii[i]=Math.max(0,tmpRadii[i]-strokeWidthFull)' in source


def test_glass_surfaces_share_the_existing_renderer_and_backup_accepts_new_value():
    # No per-chat filters or extra overlays: the real surfaces already hold the
    # shared drawable. Folder labels/types don't affect the selected rim.
    for path in ['org/telegram/ui/ActionBar/ActionBar.java','org/telegram/ui/Components/ChatActivityEnterView.java','org/telegram/ui/Components/FilterTabsView.java','org/telegram/ui/MainTabsActivity.java']:
        assert 'BlurredBackgroundDrawable' in (JAVA/path).read_text(),path
    assert '"glassOutlineStyle", AppearanceConfig.glassOutlineStyle, 0, 3' in (JAVA/'app/exteraless/backup/EtgBackup.java').read_text()
