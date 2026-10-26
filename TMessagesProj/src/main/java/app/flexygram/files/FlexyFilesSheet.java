/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import static org.telegram.messenger.AndroidUtilities.dp;
import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import android.view.*;
import android.widget.*;
import android.text.*;
import androidx.recyclerview.widget.*;
import app.flexygram.files.core.SelectedDocument;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.*;
import org.telegram.ui.Components.RecyclerListView;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.*;

/** Explicit-open native sheet. Recycling list; only selected ZIP index is read, never its full payload. */
final class FlexyFilesSheet extends BottomSheet {
    private final BaseFragment owner;private final File file;private final String name;private final long dialog;private final int account;
    private final FilesWork work=new FilesWork();private volatile SelectedDocument document;
    private List<SelectedDocument.Entry> entries=Collections.emptyList();private List<Row> rows=Collections.emptyList();private String path="";
    private final TextView breadcrumb,status;private final EditText query;private final Adapter adapter=new Adapter();private boolean closed;
    private static final class Row {final String path,label;final boolean folder;Row(String p,String l,boolean d){path=p;label=l;folder=d;}}
    FlexyFilesSheet(BaseFragment owner,File file,String name,long dialog,int account) {
        super(owner.getParentActivity(),false,owner.getResourceProvider());this.owner=owner;this.file=file;this.name=name;this.dialog=dialog;this.account=account;
        setApplyTopPadding(false);setBackgroundColor(Theme.getColor(Theme.key_windowBackgroundGray,owner.getResourceProvider()));
        Context c=getContext();LinearLayout panel=new LinearLayout(c);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(20),dp(16),dp(20),dp(12));
        TextView title=text(c,name,19);title.setMaxLines(2);title.setEllipsize(TextUtils.TruncateAt.END);panel.addView(title);
        status=text(c,getString(R.string.Loading),14);panel.addView(status);
        breadcrumb=text(c,"/",15);breadcrumb.setMaxLines(2);breadcrumb.setEllipsize(TextUtils.TruncateAt.MIDDLE);breadcrumb.setMinHeight(dp(48));breadcrumb.setGravity(Gravity.CENTER_VERTICAL);panel.addView(breadcrumb);
        breadcrumb.setOnClickListener(v->{int cut=path.lastIndexOf('/',Math.max(0,path.length()-2));path=cut<0?"":path.substring(0,cut+1);filter();});
        query=new EditText(c);query.setTextColor(color(Theme.key_windowBackgroundWhiteBlackText));query.setHintTextColor(color(Theme.key_windowBackgroundWhiteGrayText2));query.setHint(getString(R.string.Search));query.setSingleLine(true);query.setTextSize(16);query.setEnabled(false);panel.addView(query,new LinearLayout.LayoutParams(-1,dp(48)));
        RecyclerListView list=new RecyclerListView(c);list.setLayoutManager(new LinearLayoutManager(c));list.setAdapter(adapter);list.setOnItemClickListener((view,position)->{if(position<0||position>=rows.size())return;Row row=rows.get(position);if(row.folder){path=row.path;query.setText("");filter();}else{if(owner.presentFragment(new FlexyFileEditorActivity(file,name,row.path,dialog,account)))dismiss();}});
        panel.addView(list,new LinearLayout.LayoutParams(-1,Math.max(dp(120),Math.min(dp(360),AndroidUtilities.displaySize.y/2))));
        query.addTextChangedListener(new TextWatcher(){public void beforeTextChanged(CharSequence s,int st,int count,int after){}public void onTextChanged(CharSequence s,int st,int before,int count){filter();}public void afterTextChanged(Editable e){}});
        setCustomView(panel);setOnDismissListener(d->dispose());load();
    }
    private int color(int key){return Theme.getColor(key,owner.getResourceProvider());}
    private TextView text(Context c,String value,int size){TextView t=new TextView(c);t.setText(value);t.setTextSize(size);t.setTextColor(color(Theme.key_windowBackgroundWhiteBlackText));return t;}
    private void load(){WeakReference<FlexyFilesSheet> weak=new WeakReference<>(this);FilesWork tasks=work;File selected=file;int token=tasks.token()+1;
        tasks.submit(()->{SelectedDocument opened=null;try{opened=new SelectedDocument(selected);List<SelectedDocument.Entry> index=opened.entries();SelectedDocument ready=opened;
            if(!tasks.current(token)){opened.close();return;}
            AndroidUtilities.runOnUIThread(()->{FlexyFilesSheet sheet=weak.get();if(sheet==null||!tasks.current(token)){try{ready.close();}catch(IOException ignored){}return;}sheet.document=ready;sheet.entries=index;sheet.status.setText((ready.isArchive()?"ZIP":"TEXT / IMAGE")+" · "+AndroidUtilities.formatFileSize(ready.size()));sheet.query.setEnabled(true);
                if(!ready.isArchive()){if(sheet.owner.presentFragment(new FlexyFileEditorActivity(sheet.file,sheet.name,null,sheet.dialog,sheet.account)))sheet.dismiss();}else sheet.filter();});
        }catch(Exception invalid){if(opened!=null)try{opened.close();}catch(IOException ignored){}AndroidUtilities.runOnUIThread(()->{FlexyFilesSheet sheet=weak.get();if(sheet!=null&&tasks.current(token))sheet.status.setText(getString(R.string.FlexyFilesError));});}});
    }
    private void filter(){if(document==null||closed)return;String prefix=path,search=query.getText().toString().toLowerCase(Locale.ROOT);List<SelectedDocument.Entry> source=entries;WeakReference<FlexyFilesSheet> weak=new WeakReference<>(this);FilesWork tasks=work;int token=tasks.token()+1;
        tasks.submit(()->{LinkedHashMap<String,Row> found=new LinkedHashMap<>();for(SelectedDocument.Entry entry:source){if(Thread.currentThread().isInterrupted())return;if(!entry.path.startsWith(prefix))continue;String tail=entry.path.substring(prefix.length());if(tail.isEmpty())continue;
            int slash=tail.indexOf('/');boolean folder=slash>=0||entry.directory;String label=search.isEmpty()?(slash<0?tail:tail.substring(0,slash)):tail;if(!search.isEmpty()&&!tail.toLowerCase(Locale.ROOT).contains(search))continue;
            String p=search.isEmpty()?prefix+label+(folder?"/":""):entry.path+(entry.directory?"/":"");boolean d=search.isEmpty()?folder:entry.directory;found.put(p,new Row(p,(d?"▸ ":"")+label,d));}
            ArrayList<Row> result=new ArrayList<>(found.values());result.sort(Comparator.comparing((Row r)->!r.folder).thenComparing(r->r.label,String.CASE_INSENSITIVE_ORDER));AndroidUtilities.runOnUIThread(()->{FlexyFilesSheet sheet=weak.get();if(sheet==null||!tasks.current(token))return;sheet.rows=result;sheet.breadcrumb.setText("/"+prefix);sheet.adapter.notifyDataSetChanged();});});
    }
    private void dispose(){if(closed)return;closed=true;work.close();SelectedDocument old=document;document=null;if(old!=null)try{old.close();}catch(IOException ignored){}entries=Collections.emptyList();rows=Collections.emptyList();query.clearFocus();}
    @Override public void dismiss(){dispose();super.dismiss();}
    private final class Adapter extends RecyclerListView.SelectionAdapter {
        @Override public boolean isEnabled(RecyclerView.ViewHolder h){return true;}
        @Override public int getItemCount(){return rows.size();}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){TextView t=text(parent.getContext(),"",16);t.setGravity(Gravity.CENTER_VERTICAL);t.setPadding(dp(12),dp(10),dp(12),dp(10));t.setMinHeight(dp(52));t.setMaxLines(2);t.setEllipsize(TextUtils.TruncateAt.MIDDLE);t.setLayoutParams(new RecyclerView.LayoutParams(-1,-2));return new RecyclerListView.Holder(t);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder h,int position){((TextView)h.itemView).setText(rows.get(position).label);}
    }
}
