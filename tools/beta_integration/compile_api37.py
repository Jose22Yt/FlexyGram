"""API37 compilation of new production Beta views with explicit Telegram/Recycler host doubles.
This is not a full app, DEX, native library, signing or install check.
"""
from pathlib import Path
import argparse,importlib.util,re,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--sdk-root',type=Path,required=True);args=parser.parse_args()
s=importlib.util.spec_from_file_location('beta_views',ROOT/'tools/beta_integration/android/run.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='flexy-beta-api37-') as work:
    work=Path(work);m.write(work,ROOT)
    def put(name,text):
        p=work/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    java=ROOT/'TMessagesProj/src/main/java'
    for name in ['DeleteMotionSettingsDialog','MessageAnimationsActivity']:
        path='app/flexygram/bubbles/deletion/'+name+'.java';put(path,(java/path).read_text())
    put('androidx/annotation/NonNull.java','package androidx.annotation;public @interface NonNull {}')
    put('androidx/recyclerview/widget/RecyclerView.java','package androidx.recyclerview.widget;public class RecyclerView{public static class ViewHolder{public android.view.View itemView;public int getAdapterPosition(){return 0;}}}')
    put('org/telegram/ui/Cells/TextSettingsCell.java','package org.telegram.ui.Cells;public class TextSettingsCell extends android.view.View{public TextSettingsCell(android.content.Context c){super(c);}public void setTextAndValue(String a,String b,boolean c){}}')
    put('app/flexygram/settings/SignatureMatteSettingsActivity.java','''package app.flexygram.settings;
public class SignatureMatteSettingsActivity {
 protected static final int TYPE_SETTINGS=1;protected BaseListAdapter listAdapter;
 protected String getActionBarTitle(){return "";}protected void updateRows(){}protected int addRow(String key){return 0;}
 protected BaseListAdapter createAdapter(android.content.Context c){return null;}
 protected void onItemClick(android.view.View v,int p,float x,float y){}public void onResume(){}
 public android.app.Activity getParentActivity(){return null;}public void presentFragment(SignatureMatteSettingsActivity a){}
 public static class BaseListAdapter{public void notifyDataSetChanged(){}}
 public static class MatteListAdapter extends BaseListAdapter{
 public MatteListAdapter(android.content.Context c){}public int getItemViewType(int p){return 0;}
 public void onBindViewHolder(androidx.recyclerview.widget.RecyclerView.ViewHolder h,int p,boolean partial){}
 public boolean isEnabled(androidx.recyclerview.widget.RecyclerView.ViewHolder h){return true;}}
}''')
    put('org/telegram/ui/ActionBar/AlertDialog.java','''package org.telegram.ui.ActionBar;
public class AlertDialog extends android.app.AlertDialog {
 protected AlertDialog(android.content.Context c){super(c);}
 public static class Builder extends android.app.AlertDialog.Builder {
 private final android.content.Context context;public Builder(android.content.Context c){super(c);context=c;}
 @Override public Builder setTitle(CharSequence c){super.setTitle(c);return this;}
 @Override public Builder setView(android.view.View v){super.setView(v);return this;}
 @Override public Builder setPositiveButton(CharSequence c,android.content.DialogInterface.OnClickListener l){super.setPositiveButton(c,l);return this;}
 @Override public AlertDialog create(){return new AlertDialog(context);}}
}''')
    p=work/'org/telegram/ui/ActionBar/Theme.java';text=p.read_text().replace('public static int getColor(int k,ResourcesProvider p)', 'public static int key_windowBackgroundWhiteGrayText=3,key_windowBackgroundWhiteBlackText=4,key_chat_messageTextOut=5,key_chat_outBubble=6;public static int getColor(int k){return getColor(k,null);}public static int getColor(int k,ResourcesProvider p)');p.write_text(text)
    keys=set()
    for p in work.rglob('*.java'):keys.update(re.findall(r'R.string.(\w+)',p.read_text()))
    put('org/telegram/messenger/R.java','package org.telegram.messenger;public class R{public static class string{'+''.join('public static final int '+n+'='+str(i+1)+';' for i,n in enumerate(sorted(keys)))+'}}')
    subprocess.run(['javac','-cp',str(args.sdk_root/'platforms/android-37.0/android.jar'),'-d',str(work/'classes'),*map(str,work.rglob('*.java'))],check=True)
print('PASS API37: production Beta snapshot, viewport, span, selector and navigation classes; host services are doubles.')
