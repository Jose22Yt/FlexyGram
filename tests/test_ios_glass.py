"""Production material ownership and Skia shader probes; not a device frame-time claim."""
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from test_composer_layout import method
from test_render_work_reuse import JAVA, ROOT, probe


def hosts():
    return {
        'android/content/Context.java': '''package android.content;public class Context {
public static final int MODE_PRIVATE=0;public final SharedPreferences prefs=new SharedPreferences();
public SharedPreferences getSharedPreferences(String name,int mode){if(!name.equals("flexy_ios_glass"))throw new AssertionError();return prefs;}}''',
        'android/content/SharedPreferences.java': '''package android.content;import java.util.*;public class SharedPreferences {
public interface OnSharedPreferenceChangeListener{void onSharedPreferenceChanged(SharedPreferences p,String key);}
public final Map<String,Object> values=new HashMap<>();OnSharedPreferenceChangeListener listener;
public boolean getBoolean(String k,boolean d){return (Boolean)values.getOrDefault(k,d);}
public int getInt(String k,int d){return (Integer)values.getOrDefault(k,d);}
public void registerOnSharedPreferenceChangeListener(OnSharedPreferenceChangeListener l){listener=l;}
public Editor edit(){return new Editor();}public class Editor{Map<String,Object> updates=new HashMap<>();
public Editor putBoolean(String k,boolean v){updates.put(k,v);return this;}public Editor putInt(String k,int v){updates.put(k,v);return this;}
public void apply(){values.putAll(updates);for(String k:updates.keySet())if(listener!=null)listener.onSharedPreferenceChanged(SharedPreferences.this,k);}}}''',
        'android/os/Build.java':'package android.os;public class Build{public static class VERSION{public static int SDK_INT=33;}}',
        'android/graphics/drawable/Drawable.java':'package android.graphics.drawable;public class Drawable{public int invalidations;public void invalidateSelf(){invalidations++;}}',
        'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawable.java':'package org.telegram.ui.Components.blur3.drawable;public class BlurredBackgroundDrawable extends android.graphics.drawable.Drawable{public int colors;public void updateColors(){colors++;}}',
        'org/telegram/messenger/ApplicationLoader.java':'package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=new android.content.Context();}',
        'org/telegram/messenger/AndroidUtilities.java':'''package org.telegram.messenger;public class AndroidUtilities{public static final java.util.ArrayDeque<Runnable> queue=new java.util.ArrayDeque<>();public static void runOnUIThread(Runnable r){queue.add(r);}public static void drain(){while(!queue.isEmpty())queue.remove().run();}}''',
        'org/telegram/messenger/LiteMode.java':'package org.telegram.messenger;public class LiteMode{public static boolean saving;public static boolean isPowerSaverApplied(){return saving;}}',
    }


ACTUAL = [JAVA/'app/flexygram/glass/IosGlassConfig.java', JAVA/'app/flexygram/performance/CoalescedTask.java']


def test_material_takes_ownership_without_mutating_legacy_flags_and_restores_them(tmp_path):
    files=hosts()
    files['Probe.java']='''import app.flexygram.glass.IosGlassConfig;import org.telegram.messenger.*;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){
  check(!IosGlassConfig.enabled()&&IosGlassConfig.selected(15)&&!IosGlassConfig.active(1));
  for(boolean old:new boolean[]{false,true})check(IosGlassConfig.backdrop(1,old)==old);
  IosGlassConfig.setEnabled(true);
  for(int target:new int[]{1,2,4,8}){check(IosGlassConfig.active(target));check(IosGlassConfig.backdrop(target,false));}
  check(!IosGlassConfig.active(0)&&!IosGlassConfig.requested(16));
  IosGlassConfig.setSelected(4,false);check(!IosGlassConfig.active(4)&&IosGlassConfig.backdrop(4,true));
  check(IosGlassConfig.active(2)&&IosGlassConfig.chatBackdrop(false));
  IosGlassConfig.setSelected(8,false);check(IosGlassConfig.homeBackdrop(false));
  IosGlassConfig.setSelected(1,false);check(!IosGlassConfig.homeBackdrop(false)&&IosGlassConfig.chatBackdrop(false));
  IosGlassConfig.setSelected(1,true);
  LiteMode.saving=true;check(!IosGlassConfig.anyActive()&&!IosGlassConfig.backdrop(1,true));
  LiteMode.saving=false;check(IosGlassConfig.active(1));
  android.os.Build.VERSION.SDK_INT=32;check(!IosGlassConfig.anyActive()&&IosGlassConfig.backdrop(1,true));
  android.os.Build.VERSION.SDK_INT=33;IosGlassConfig.setEnabled(false);
  for(int target:new int[]{1,2,4,8})for(boolean old:new boolean[]{false,true})check(IosGlassConfig.backdrop(target,old)==old);
  check(ApplicationLoader.applicationContext.prefs.values.keySet().equals(java.util.Set.of("enabled","surfaces")));
  var drawable=new org.telegram.ui.Components.blur3.drawable.BlurredBackgroundDrawable();IosGlassConfig.track(drawable);IosGlassConfig.track(drawable);
  AndroidUtilities.drain();int before=drawable.colors;
  for(int i=0;i<1000;i++)IosGlassConfig.setEnabled(i%2==0);
  check(AndroidUtilities.queue.size()==1);AndroidUtilities.drain();check(drawable.colors==before+1&&AndroidUtilities.queue.isEmpty());
 }
}'''
    probe(tmp_path, files, ACTUAL)


def test_native_node_has_one_profile_and_no_shader_allocation_until_drawing(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    sync=method(source,'private void syncMaterialProfile()')
    setter=method(source,'public void setLiquidGlassEffectAllowed(boolean allowed)')
    files=hosts()
    files['android/graphics/RenderNode.java']='package android.graphics;public class RenderNode{public Object effect;public void setRenderEffect(Object e){effect=e;}}'
    files['org/telegram/ui/Components/blur3/LiquidGlassEffect.java']='''package org.telegram.ui.Components.blur3;public class LiquidGlassEffect{
public static int nativeCreates,iosCreates;public static boolean fail;public boolean ios;
public LiquidGlassEffect(android.graphics.RenderNode n){nativeCreates++;n.setRenderEffect(this);}
public LiquidGlassEffect(android.graphics.RenderNode n,boolean ios){iosCreates++;if(fail)throw new IllegalArgumentException("unsupported driver");this.ios=ios;n.setRenderEffect(this);}}'''
    files['org/telegram/messenger/FileLog.java']='package org.telegram.messenger;public class FileLog{public static void e(Throwable t){}}'
    files['Probe.java']='''import android.graphics.RenderNode;import android.os.Build;import org.telegram.ui.Components.blur3.LiquidGlassEffect;
import app.flexygram.glass.IosGlassConfig;import org.telegram.messenger.LiteMode;
public class Probe{
 boolean nativeLiquidGlassAllowed;int materialProfile=-1,iosGlassSurface=1;static boolean iosShaderUnavailable;
 LiquidGlassEffect liquidGlassEffect;RenderNode renderNodeFill=new RenderNode();int redraws;
 void updateColors(){}void invalidateDisplayList(){}void invalidateSelf(){redraws++;}
 SETTER SYNC
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();
  p.setLiquidGlassEffectAllowed(true);check(LiquidGlassEffect.nativeCreates==0);
  IosGlassConfig.setEnabled(true);p.syncMaterialProfile();check(p.materialProfile==2&&LiquidGlassEffect.iosCreates==1&&LiquidGlassEffect.nativeCreates==0);
  for(int i=0;i<10000;i++){p.syncMaterialProfile();p.setLiquidGlassEffectAllowed(i%2==0);}
  check(LiquidGlassEffect.iosCreates==1&&p.renderNodeFill.effect==p.liquidGlassEffect);
  IosGlassConfig.setEnabled(false);p.syncMaterialProfile();check(p.materialProfile==0&&p.renderNodeFill.effect==null);
  p.setLiquidGlassEffectAllowed(true);p.syncMaterialProfile();check(p.materialProfile==1&&LiquidGlassEffect.nativeCreates==1);
  IosGlassConfig.setEnabled(true);p.syncMaterialProfile();check(p.materialProfile==2&&LiquidGlassEffect.iosCreates==2);
  LiteMode.saving=true;p.syncMaterialProfile();check(p.materialProfile==0&&p.renderNodeFill.effect==null);
  LiteMode.saving=false;LiquidGlassEffect.fail=true;p.syncMaterialProfile();check(iosShaderUnavailable&&p.renderNodeFill.effect==null);
  int attempts=LiquidGlassEffect.iosCreates;for(int i=0;i<10000;i++)p.syncMaterialProfile();check(LiquidGlassEffect.iosCreates==attempts);
  Probe other=new Probe();other.syncMaterialProfile();check(other.renderNodeFill.effect==null&&LiquidGlassEffect.iosCreates==attempts);
 }
}'''.replace('SETTER',setter).replace('SYNC',sync)
    probe(tmp_path,files,ACTUAL)


def test_settings_route_scope_tags_localizations_and_backup_are_connected():
    resources=ROOT/'TMessagesProj/src/main/res'
    names=[]
    for folder in ('values','values-es'):
        entries=ET.parse(resources/folder/'flexy_ios_glass.xml').getroot().findall('string')
        names.append({x.attrib['name']for x in entries})
        assert all(x.text for x in entries)
    assert names[0]==names[1] and len(names[0])==8
    expected={
        'org/telegram/ui/MainTabsActivity.java':'IosGlassConfig.HOME',
        'org/telegram/ui/ActionBar/ActionBar.java':'IosGlassConfig.HEADER',
        'org/telegram/ui/Components/chat/ChatInputViewsContainer.java':'IosGlassConfig.COMPOSER',
        'org/telegram/ui/Components/FilterTabsView.java':'IosGlassConfig.FOLDERS',
    }
    for path,scope in expected.items():
        source=(JAVA/path).read_text()
        assert 'setIosGlassSurface' in source and scope in source
    settings=(JAVA/'app/flexygram/settings/signature/Settings3LinksSection.java').read_text()
    assert 'case "ios_glass":f=new app.flexygram.glass.IosGlassSettingsActivity();' in settings
    catalog=(JAVA/'app/flexygram/studio/StudioClientCatalog.java').read_text()
    assert 'bool("flexy_ios_glass","enabled",false)' in catalog
    assert 'range("flexy_ios_glass","surfaces",0,15)' in catalog
    renderer=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    assert 'materialProfile == 2 ? dp(8)' in renderer
    assert 'if (liquidGlassEffect != null) syncMaterialProfile();' in renderer


def test_actual_skia_shader_compiles_refracts_edges_and_is_stable_without_animation():
    skia=pytest.importorskip('skia',reason='Optional Skia runtime shader verification')
    np=pytest.importorskip('numpy')
    effect=skia.RuntimeEffect.MakeForShader((ROOT/'TMessagesProj/src/main/res/raw/flexy_ios_glass_shader.agsl').read_text())
    background=skia.RuntimeEffect.MakeForShader('half4 main(float2 p){return half4(p.x/256.0,p.y/80.0,0.25,1.0);}')
    child=skia.RuntimeShaderBuilder(background).makeShader()
    def render(strength, width=256, height=80, dark=False, solid=None):
        builder=skia.RuntimeShaderBuilder(effect)
        uniforms={'resolution':[float(width),float(height)],'center':[width/2,height/2], 'size':[width/2,height/2],
                  'radius':[height/2]*4,'thickness':8.0,'refract_index':1.6,'refract_intensity':strength,
                  'foreground_color_premultiplied':[0.08,0.08,0.08,0.08], 'appearance_dark':1.0 if dark else 0.0}
        for key,value in uniforms.items():builder.setUniform(key,value)
        builder.setChild('img',child if solid is None else skia.Shaders.Color(solid))
        surface=skia.Surface(width,height);canvas=surface.getCanvas();canvas.clear(skia.ColorTRANSPARENT)
        canvas.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeWH(width,height),height/2,height/2),True)
        canvas.drawPaint(skia.Paint(Shader=builder.makeShader()))
        return surface.makeImageSnapshot().toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
    plain=render(0.0);glass=render(0.85)
    assert np.array_equal(plain[30:50,80:175],glass[30:50,80:175])
    assert np.any(plain[:6,80:175,:3]!=glass[:6,80:175,:3])
    assert glass[0,0,3]==0 and glass[40,128,3]==255
    for _ in range(3):assert np.array_equal(glass,render(0.85))
    assert render(0.85,1,1).shape==(1,1,4)

    dark=render(0.85,dark=True,solid=skia.ColorWHITE)
    light=render(0.85,solid=skia.ColorBLACK)
    assert dark[40,128,:3].max() <= 113  # White foreground retains >4.5:1 contrast in the content area.
    assert light[40,128,:3].min() >= 172


def test_only_conversation_header_opts_into_the_material_not_shared_action_bars(tmp_path):
    source=(JAVA/'org/telegram/ui/ActionBar/ActionBar.java').read_text()
    two=method(source,'public void setupGlass(BlurredBackgroundDrawableViewFactory factory, BlurredBackgroundColorProvider colorProvider)')
    three=method(source,'public void setupGlass(BlurredBackgroundDrawableViewFactory factory,\n                           BlurredBackgroundColorProvider colorProvider,\n                           boolean isForum)')
    tagged=method(source,'public void setupGlass(BlurredBackgroundDrawableViewFactory factory,\n                           BlurredBackgroundColorProvider colorProvider,\n                           boolean isForum, int surface)')
    assert 'signatureGlassSurface = surface;' in tagged
    assert source.count('.setIosGlassSurface(signatureGlassSurface)')==5
    assert '.setIosGlassSurface(app.flexygram.glass.IosGlassConfig.HEADER)' not in source
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    assert 'ChatObject.isForum(currentChat), app.flexygram.glass.IosGlassConfig.HEADER);' in chat
    probe(tmp_path,{'Probe.java':'''public class Probe{
 static class BlurredBackgroundDrawableViewFactory{}static class BlurredBackgroundColorProvider{}
 int scope=-1,calls;boolean forum;
 TWO THREE
 public void setupGlass(BlurredBackgroundDrawableViewFactory f,BlurredBackgroundColorProvider p,boolean forum,int scope){this.scope=scope;this.forum=forum;calls++;}
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();var f=new BlurredBackgroundDrawableViewFactory();var colors=new BlurredBackgroundColorProvider();
  p.setupGlass(f,colors);check(p.scope==0&&!p.forum);
  p.setupGlass(f,colors,true);check(p.scope==0&&p.forum);
  p.setupGlass(f,colors,false,4);check(p.scope==4&&!p.forum);
  p.setupGlass(f,colors,true);check(p.scope==0&&p.forum&&p.calls==4);
 }
}'''.replace('TWO',two).replace('THREE',three)})


def test_complete_settings_screen_compiles_with_bundled_recycler_api(tmp_path):
    import re
    recycler=(JAVA/'androidx/recyclerview/widget/RecyclerView.java').read_text()
    assert re.search(r'public final int getAdapterPosition\s*\(',recycler)
    assert 'getBindingAdapterPosition(' not in recycler
    files=hosts()
    files.update({
        'android/view/View.java':'package android.view;public class View{public void setAlpha(float a){}}',
        'androidx/recyclerview/widget/RecyclerView.java':'''package androidx.recyclerview.widget;public class RecyclerView{
public static class ViewHolder{public android.view.View itemView;public int position;public ViewHolder(android.view.View v,int p){itemView=v;position=p;}public final int getAdapterPosition(){return position;}}}''',
        'org/telegram/messenger/LocaleController.java':'package org.telegram.messenger;public class LocaleController{public static String getString(int id){return "row"+id;}}',
        'org/telegram/ui/Cells/TextCheckCell.java':'package org.telegram.ui.Cells;public class TextCheckCell extends android.view.View{public boolean checked;public void setTextAndCheck(String text,boolean checked,boolean divider){this.checked=checked;}}',
        'org/telegram/ui/Cells/TextInfoPrivacyCell.java':'package org.telegram.ui.Cells;public class TextInfoPrivacyCell extends android.view.View{public void setText(String text){}}',
        'app/flexygram/settings/SignatureMatteSettingsActivity.java':'''package app.flexygram.settings;
import android.content.Context;import android.view.View;import androidx.recyclerview.widget.RecyclerView;
public abstract class SignatureMatteSettingsActivity{
 public static final int TYPE_CHECK=3,TYPE_INFO_PRIVACY=7;public int rowCount;
 public BaseListAdapter listAdapter;
 protected abstract String getActionBarTitle();protected void updateRows(){rowCount=0;}protected void addRow(String key){rowCount++;}
 protected abstract void onItemClick(View view,int position,float x,float y);protected abstract BaseListAdapter createAdapter(Context c);
 public abstract class BaseListAdapter{public abstract int getItemViewType(int p);public abstract void onBindViewHolder(RecyclerView.ViewHolder h,int p,boolean partial);public abstract boolean isEnabled(RecyclerView.ViewHolder h);public void notifyItemChanged(int p){}}
 public abstract class MatteListAdapter extends BaseListAdapter{public MatteListAdapter(Context context){}}
}''',
    })
    names=[x.attrib['name'] for x in ET.parse(ROOT/'TMessagesProj/src/main/res/values/flexy_ios_glass.xml').getroot().findall('string')]
    files['org/telegram/messenger/R.java']='package org.telegram.messenger;public class R{public static class string{'+''.join('public static int '+name+'='+str(i+1)+';'for i,name in enumerate(names))+'}}'
    files['app/flexygram/glass/Probe.java']='''package app.flexygram.glass;
import android.os.Build;import android.content.Context;import androidx.recyclerview.widget.RecyclerView;import org.telegram.ui.Cells.*;
public class Probe{static void check(boolean b){if(!b)throw new AssertionError();}public static void main(String[]args){
 IosGlassSettingsActivity screen=new IosGlassSettingsActivity();screen.updateRows();check(screen.rowCount==6);
 var adapter=screen.createAdapter(new Context());screen.listAdapter=adapter;TextCheckCell cell=new TextCheckCell();var holder=new RecyclerView.ViewHolder(cell,-1);
 check(!adapter.isEnabled(holder));holder.position=0;check(adapter.isEnabled(holder));
 screen.onItemClick(cell,0,0,0);adapter.onBindViewHolder(holder,0,false);check(cell.checked&&IosGlassConfig.enabled());
 holder.position=5;check(!adapter.isEnabled(holder));adapter.onBindViewHolder(new RecyclerView.ViewHolder(new TextInfoPrivacyCell(),5),5,false);
 Build.VERSION.SDK_INT=32;holder.position=0;check(adapter.isEnabled(holder));screen.onItemClick(cell,0,0,0);check(!IosGlassConfig.enabled()&&!adapter.isEnabled(holder));
 }}'''
    # The probe helper invokes an unqualified main class; use a launcher for this packaged screen test.
    files['Probe.java']='public class Probe{public static void main(String[]args){app.flexygram.glass.Probe.main(args);}}'
    probe(tmp_path,files,ACTUAL+[JAVA/'app/flexygram/glass/IosGlassSettingsActivity.java'])
