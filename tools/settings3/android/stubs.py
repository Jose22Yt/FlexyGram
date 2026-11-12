"""Reuse Settings2's explicitly isolated hosts. AndroidX RecyclerView is the actual AAR.
Only root/cell/registry/policy and the new composite adapter are production under test.
Direct category controller and legacy Telegram controllers remain host doubles here.
"""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('settings2_hosts',ROOT/'tools/settings2/android/stubs.py')
old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
resources=old.resources

def write(dest,root):
 old.write(dest,root)
 def emit(path,s):
  p=dest/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
 emit('app/flexygram/home/SmartPreviewsSettingsActivity.java','package app.flexygram.home;public class SmartPreviewsSettingsActivity extends tw.nekomimi.nekogram.settings.BaseNekoSettingsActivity{protected String getActionBarTitle(){return "Smart Previews";}protected BaseListAdapter createAdapter(android.content.Context c){return new BaseListAdapter(c){};}protected void onItemClick(android.view.View v,int p,float x,float y){}}')
 emit('org/telegram/messenger/BuildVars.java','package org.telegram.messenger;public class BuildVars{public static String BUILD_VERSION_STRING="ISOLATED HOST";}')
 emit('app/flexygram/inlineconverter/InlineConversionSettingsSection.java','package app.flexygram.inlineconverter;public class InlineConversionSettingsSection extends app.exteraless.settings.OpenExteraGeneralActivity{}')
 emit('app/flexygram/memberlens/MemberLensSettingsSection.java','package app.flexygram.memberlens;public class MemberLensSettingsSection extends app.exteraless.settings.OpenExteraGeneralActivity{}')
 emit('app/flexygram/effects/GlareSettingsSection.java','package app.flexygram.effects;public class GlareSettingsSection extends app.exteraless.settings.OpenExteraGeneralActivity{}')
 (dest/'androidx/recyclerview/widget/RecyclerView.java').unlink()
 emit('app/flexygram/settings/signature/SignatureDirectSettingsActivity.java','package app.flexygram.settings.signature;public class SignatureDirectSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public final String category;public SignatureDirectSettingsActivity(String s){category=s;}public SignatureDirectSettingsActivity(String s,String page){category=s;}}')
 (dest/'app/flexygram/settings/signature/Settings3LinksSection.java').unlink()
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java';s=p.read_text().replace('public abstract class BaseNekoSettingsActivity extends BaseFragment{','public abstract class BaseNekoSettingsActivity extends BaseFragment{public void setSettings3Position(java.util.function.IntUnaryOperator mapper){}public String getSignatureSettingsRoute(){return null;}')
 s=s.replace('RecyclerView.ViewHolder h=listAdapter.onCreateViewHolder(listView,type);h.position=i;h.type=type;','RecyclerView.ViewHolder h=listAdapter.createViewHolder(listView,type);')
 s=s.replace('new TextView(mContext)','new org.telegram.ui.Cells.TextSettingsCell(mContext)')
 s=s.replace('protected abstract class BaseListAdapter{','protected abstract class BaseListAdapter extends RecyclerListView.SelectionAdapter{public int getItemCount(){return rowCount;}public void onBindViewHolder(RecyclerView.ViewHolder h,int p){onBindViewHolder(h,p,false);}')
 s=s.replace('public void notifyDataSetChanged(){if(listView!=null)render();}public void notifyItemChanged(int p){notifyDataSetChanged();}','')
 p.write_text(s)
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoXSettingsActivity.java';s=p.read_text().replace('public String source,route;','public String source,route;public String getSignatureSettingsRoute(){return route;}public void setSettings3Position(java.util.function.IntUnaryOperator mapper){}');p.write_text(s)
 p=dest/'org/telegram/ui/Components/RecyclerListView.java';s=p.read_text().replace('public void setItemAnimator(Object a){}','public void setItemAnimator(Object a){}public void setItemViewCacheSize(int size){}').replace('public static final int TAG_NOT_SECTION=12;','public static final int TAG_NOT_SECTION=12;public abstract static class SelectionAdapter extends RecyclerView.Adapter<RecyclerView.ViewHolder>{public abstract boolean isEnabled(RecyclerView.ViewHolder h);}')
 p.write_text(s)
 emit('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.widget.TextView{public TextSettingsCell(android.content.Context c){super(c);}public void setText(String s,boolean d){setText(s);}}')
 # Native icon background is copied unchanged; Telegram controller/theme plumbing remains isolated.
 text=(root/'TMessagesProj/src/main/java/org/telegram/ui/SettingsActivity.java').read_text()
 start=text.index('        public static class Background extends Drawable')
 brace=text.index('{',start);end=brace+1;depth=1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 emit('org/telegram/ui/SettingsActivity.java','package org.telegram.ui;import android.graphics.*;import android.graphics.drawable.Drawable;import androidx.annotation.*;import org.telegram.messenger.AndroidUtilities;import org.telegram.ui.Components.blur3.GlassOutlineStyle;import static org.telegram.messenger.AndroidUtilities.dp;public class SettingsActivity{public static class SettingCell{'+text[start:end]+'}}')
 emit('org/telegram/ui/Components/blur3/GlassOutlineStyle.java','package org.telegram.ui.Components.blur3;public enum GlassOutlineStyle{GLARE,SOLID,HIDDEN;public interface Listener{void onGlassOutlineStyleChanged();}public static void addListener(Listener l){}public static GlassOutlineStyle current(){return GLARE;}}')
 emit('app/exteraless/settings/utils/SettingsIcons.java','package app.exteraless.settings.utils;public class SettingsIcons{public static int resolve(android.content.Context c,int i){return i;}}')
 emit('org/telegram/ui/ActionBar/ThemeDescription.java','package org.telegram.ui.ActionBar;public class ThemeDescription{public static final int FLAG_TEXTCOLOR=4;public ThemeDescription(android.view.View v,int f,Class[] c,android.graphics.Paint p,android.graphics.drawable.Drawable[] d,Object delegate,int key){}}')
 p=dest/'org/telegram/ui/ActionBar/BaseFragment.java';s=p.read_text().replace('public static android.app.Activity activity;','public static android.app.Activity activity;public java.util.ArrayList<ThemeDescription> getThemeDescriptions(){return new java.util.ArrayList<>();}');p.write_text(s)
 p=dest/'org/telegram/messenger/AndroidUtilities.java';s=p.read_text().replace('public static int dp','public static android.graphics.RectF rectTmp=new android.graphics.RectF();public static int dp');p.write_text(s)
 p=dest/'org/telegram/ui/ActionBar/Theme.java';s=p.read_text().replace('key_divider=6;','key_divider=6,key_listSelector=7,key_windowBackgroundWhiteBlueHeader=8,key_windowBackgroundWhiteBlueText=9;').replace('case 1->','case 7->0x223d9eff;case 8,9->dark?0xff79bdff:0xff1684c4;case 1->');p.write_text(s)
 p=dest/'org/telegram/ui/Components/RecyclerListView.java';s=p.read_text().replace('public void setItemAnimator(Object a){}','public void disableSections(){}public void setItemAnimator(Object a){}');p.write_text(s)
 # Real preference backends; preview renderers are explicit doubles in gallery interaction tests.
 emit('org/telegram/messenger/ApplicationLoader.java','package org.telegram.messenger;public class ApplicationLoader{public static android.content.Context applicationContext=org.telegram.ui.ActionBar.BaseFragment.activity.getApplicationContext();}')
 emit('org/telegram/messenger/BuildConfig.java','package org.telegram.messenger;public class BuildConfig{public static final boolean CONNECTED_ALPHA=false;}')
 emit('app/exteraless/appearance/AppearanceConfig.java','package app.exteraless.appearance;public class AppearanceConfig{public static android.content.SharedPreferences getPreferences(){return org.telegram.ui.ActionBar.BaseFragment.activity.getSharedPreferences("isolated_appearance",0);}}')
 for name in ['HeaderConfig']:
  emit('app/flexygram/header/'+name+'.java',(root/'TMessagesProj/src/main/java/app/flexygram/header'/(name+'.java')).read_text())
 for name in ['FlexyComposerConfig','ComposerStyle','ComposerGeometry']:
  emit('app/flexygram/composer/'+name+'.java',(root/'TMessagesProj/src/main/java/app/flexygram/composer'/(name+'.java')).read_text())
 emit('app/flexygram/header/HeaderPreviewView.java','package app.flexygram.header;public class HeaderPreviewView extends android.view.View{public HeaderPreviewView(android.content.Context c,int style){super(c);}protected void onMeasure(int w,int h){setMeasuredDimension(MeasureSpec.getSize(w),96);}}')
 emit('app/flexygram/composer/FlexyComposerSettingsActivity.java','package app.flexygram.composer;public class FlexyComposerSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public android.view.View createStylePreview(android.content.Context c,int style){return new app.flexygram.header.HeaderPreviewView(c,style);}}')

 # Keep production per-row card backgrounds; the host supplies only list layout.
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java';s=p.read_text().replace('if(h.itemView instanceof app.flexygram.settings.signature.Settings2Cell){','if(h.itemView instanceof app.flexygram.settings.signature.Settings2Cell && h.itemView.getBackground()==null){');p.write_text(s)

 # Compile the real base adapter background hook: the previous double bypassed it and hid a root-card regression.
 for name in ['SettingsCardStyle','SettingsSectionTypes','SettingsCardBackground']:
  emit('app/flexygram/settings/signature/'+name+'.java',(root/'TMessagesProj/src/main/java/app/flexygram/settings/signature'/(name+'.java')).read_text())
 text=(root/'TMessagesProj/src/main/java/tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java').read_text()
 start=text.index('        protected void applySectionBackground(');brace=text.index('{',start);end=brace+1;depth=1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 hook=text[start:end]
 # Run the production inset callback too: omitting it hid the root margin reset.
 start=text.index('    public void onInsets(');brace=text.index('{',start);end=brace+1;depth=1
 while depth:
  depth+=(text[end]=='{')-(text[end]=='}');end+=1
 insets=text[start:end]
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java';s=p.read_text()
 s=s.replace('onBindViewHolder(h,i,false);','onBindViewHolder(h,i);')
 s=s.replace('onBindViewHolder(h,p,false);}', 'onBindViewHolder(h,p,false);applySectionBackground(h,p);}')
 s=s.replace('protected abstract class BaseListAdapter extends RecyclerListView.SelectionAdapter{', insets+'\nprotected abstract class BaseListAdapter extends RecyclerListView.SelectionAdapter{'+hook)
 p.write_text(s)
 p=dest/'org/telegram/ui/Cells/TextSettingsCell.java';s=p.read_text().replace('extends android.widget.TextView{','extends android.widget.TextView{public boolean needDivider;');p.write_text(s)
 p=dest/'org/telegram/ui/Cells/TextCheckCell.java';s=p.read_text().replace('extends android.widget.TextView{','extends android.widget.TextView{public void setDivider(boolean d){}');p.write_text(s)
 # UniversalAdapter hosts are isolated; production SettingsCardLists and painter are compiled unchanged.
 p=dest/'tw/nekomimi/nekogram/settings/BaseNekoSettingsActivity.java';s=p.read_text().replace('@NonNull','@androidx.annotation.NonNull');p.write_text(s)
 p=dest/'org/telegram/ui/ActionBar/Theme.java';s=p.read_text().replace('public class Theme{','public class Theme{public static int multAlpha(int c,float a){return(c&0xffffff)|((int)((c>>>24)*a)<<24);}');p.write_text(s)
 p=dest/'org/telegram/messenger/R.java';s=p.read_text().replace('public final class R {','public final class R {public static class id{public static final int transparent_tag=0x7f0a0001;}').replace('public class R{','public class R{public static class id{public static final int transparent_tag=0x7f0a0001;}');p.write_text(s)
 p=dest/'org/telegram/ui/Components/RecyclerListView.java';s=p.read_text().replace('public static final int TAG_NOT_SECTION=12;','public static final int TAG_NOT_SECTION=12,NO_POSITION=-1;');p.write_text(s)
 emit('org/telegram/ui/Components/UItem.java','package org.telegram.ui.Components;public class UItem{public boolean transparent;}')
 emit('org/telegram/ui/Components/UniversalAdapter.java','package org.telegram.ui.Components;public class UniversalAdapter{public static boolean isShadow(int t){return t==1;}public static boolean isHeader(int t){return t==4;}public boolean applyBackground=true;public UItem item;public UItem getItem(int p){return item;}public void setApplyBackground(boolean b){applyBackground=b;}}')
 emit('org/telegram/ui/Components/UniversalRecyclerView.java','''package org.telegram.ui.Components;
 public class UniversalRecyclerView extends RecyclerListView {
  public UniversalAdapter adapter=new UniversalAdapter();public boolean forced;public java.util.function.Predicate<android.view.View> content;public java.util.function.IntPredicate type;public int inset;public float radius;
  public interface Painter{void draw(android.graphics.Canvas c,android.graphics.RectF r,Float t,Float b,Float a);}
  public UniversalRecyclerView(android.content.Context c){super(c);}
  public void setForceSegmentedSettingsCards(boolean b){forced=b;}
  public androidx.recyclerview.widget.RecyclerView.ViewHolder getChildViewHolder(android.view.View v){return (androidx.recyclerview.widget.RecyclerView.ViewHolder)v.getTag();}
  public void setSections(java.util.function.Predicate<android.view.View> p,java.util.function.IntPredicate t,int pad,float r,Painter paint,boolean top){content=p;type=t;inset=pad;radius=r;}
 }''')
 # The real settings list subclass is compiled too; only the large native recycler host is isolated.
 emit('app/exteraless/appearance/SectionCardRecyclerView.java',(root/'TMessagesProj/src/main/java/app/exteraless/appearance/SectionCardRecyclerView.java').read_text())
 emit('org/telegram/ui/Components/BlurredRecyclerView.java','''package org.telegram.ui.Components;
 public class BlurredRecyclerView extends RecyclerListView {
  public boolean forced;public java.util.function.Predicate<android.view.View> content;public java.util.function.IntPredicate type;
  private androidx.recyclerview.widget.RecyclerView.Adapter adapter;
  public interface Painter{void draw(android.graphics.Canvas c,android.graphics.RectF r,Float t,Float b,Float a);}
  public BlurredRecyclerView(android.content.Context c){super(c);}
  public void setForceSegmentedSettingsCards(boolean b){forced=b;}
  public androidx.recyclerview.widget.RecyclerView.Adapter getAdapter(){return adapter;}
  public void setAdapter(androidx.recyclerview.widget.RecyclerView.Adapter a){adapter=a;}
  public void setSections(int p,float r,boolean top){}
  public void setSections(java.util.function.Predicate<android.view.View> p,java.util.function.IntPredicate t,int pad,float r,Painter paint,boolean top){content=p;type=t;}
  public void drawBackgroundRect(android.graphics.Canvas c,android.graphics.RectF r,float t,float b,float a){}
 }''')
 for name in ['TextInfoPrivacyCell','ShadowSectionCell','GraySectionCell','HeaderCell']:
  emit('org/telegram/ui/Cells/'+name+'.java','package org.telegram.ui.Cells;public class '+name+' extends android.widget.TextView{public '+name+'(android.content.Context c){super(c);}}')
 # Match the real float radius overload, otherwise Java selects a nonexistent int overload in this host.
 p=dest/'org/telegram/ui/Components/RecyclerListView.java';s=p.read_text().replace('setSections(int a,int b,boolean c)','setSections(int a,float b,boolean c)');p.write_text(s)
 # Bring the isolated base host up to date with the existing conversation layout editor API.
 p=dest/'org/telegram/ui/ActionBar/Theme.java';s=p.read_text().replace('public class Theme{','public class Theme{public interface Colorable{void updateColors();}');p.write_text(s)
 emit('app/flexygram/settings/FlexySignatureSlider.java','package app.flexygram.settings;public class FlexySignatureSlider extends android.widget.SeekBar{public FlexySignatureSlider(android.content.Context c){super(c);}public void updateColors(){}}')
 p=dest/'org/telegram/ui/ActionBar/AlertDialog.java';s=p.read_text().replace('public Builder setTitle','public Builder setItems(CharSequence[] s,android.content.DialogInterface.OnClickListener l){return this;}public Builder setTitle');p.write_text(s)
 p=dest/'org/telegram/messenger/LocaleController.java';s=p.read_text().replace('public static boolean isRTL;','public static boolean isRTL;public static String formatString(int id,Object...args){return String.format(getString(id),args);}');p.write_text(s)
 p=dest/'app/flexygram/settings/SignatureMatteSettingsActivity.java';s=p.read_text().replace('protected abstract class MatteListAdapter','protected static final int TYPE_INFO_PRIVACY=7;protected int addHeader(String key){return addRow(key);}protected int settingsRowPosition(androidx.recyclerview.widget.RecyclerView.ViewHolder h){return h.getAdapterPosition();}protected abstract class MatteListAdapter').replace('protected MatteListAdapter(android.content.Context c){super(c);}', 'protected MatteListAdapter(android.content.Context c){super(c);}public androidx.recyclerview.widget.RecyclerView.ViewHolder onCreateViewHolder(android.view.ViewGroup parent,int type){if(type==TYPE_INFO_PRIVACY)return new org.telegram.ui.Components.RecyclerListView.Holder(new org.telegram.ui.Cells.TextInfoPrivacyCell(parent.getContext()));return super.onCreateViewHolder(parent,type);}')
 p.write_text(s)
 p=dest/'org/telegram/ui/Cells/TextSettingsCell.java';s=p.read_text().replace('public boolean needDivider;','public boolean needDivider;public void setTextAndValue(String t,String v,boolean d){setText(t);}public void setEnabled(boolean enabled,Object unused){setEnabled(enabled);}');p.write_text(s)
