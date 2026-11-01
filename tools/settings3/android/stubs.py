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
 emit('org/telegram/messenger/BuildVars.java','package org.telegram.messenger;public class BuildVars{public static String BUILD_VERSION_STRING="ISOLATED HOST";}')
 emit('app/flexygram/effects/GlareSettingsSection.java','package app.flexygram.effects;public class GlareSettingsSection extends app.exteraless.settings.OpenExteraGeneralActivity{}')
 (dest/'androidx/recyclerview/widget/RecyclerView.java').unlink()
 emit('app/flexygram/settings/signature/SignatureDirectSettingsActivity.java','package app.flexygram.settings.signature;public class SignatureDirectSettingsActivity extends org.telegram.ui.ActionBar.BaseFragment{public final String category;public SignatureDirectSettingsActivity(String s){category=s;}}')
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
