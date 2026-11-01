/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import static org.telegram.messenger.LocaleController.getString;
import android.app.Activity;
import android.content.*;
import android.database.Cursor;
import android.net.Uri;
import android.os.Bundle;
import android.provider.OpenableColumns;
import android.view.*;
import android.widget.LinearLayout;
import app.flexygram.settings.*;
import app.flexygram.studio.core.*;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Cells.CheckBoxCell;
import org.telegram.ui.Components.RecyclerListView;
import androidx.recyclerview.widget.RecyclerView;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.*;
import java.util.concurrent.Future;

/** Exactly three functional rows. SAF and Android sharing do not need storage permission. */
public final class FlexyStudioActivity extends SignatureMatteSettingsActivity {
    private static final int NAV=110, SAVE=0x4651, OPEN=0x4652;
    private int header,export,importRow,share,shadow,tools,files,help,toolsShadow;
    private byte[] pendingExport;
    private boolean busy;
    private Future<?> work;
    private int generation;
    @Override protected String getActionBarTitle(){return getString(R.string.FlexyStudioTitle);}
    @Override protected void updateRows(){super.updateRows();header=addRow();export=addRow("flexystudioExport");importRow=addRow("flexystudioImport");share=addRow("flexystudioShare");shadow=addRow();tools=files=help=toolsShadow=-1;}
    @Override public View createView(Context context){View v=super.createView(context);actionBar.centerTitle();listView.setSections(AndroidUtilities.dp(16),AndroidUtilities.dp(20),true);listView.setItemAnimator(null);return v;}
    @Override protected BaseListAdapter createAdapter(Context context){return new Adapter(context);}
    @Override protected void onItemClick(View view,int position,float x,float y) {
        if(position==files){app.flexygram.files.FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled());if(view instanceof org.telegram.ui.Cells.TextCheckCell)((org.telegram.ui.Cells.TextCheckCell)view).setTextAndValueAndCheck(getString(R.string.FlexyFilesEnable),getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),true,true,false);return;}
        if(position==help){showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle("FlexyFiles").setMessage(getString(R.string.FlexyFilesHelp)).setPositiveButton(getString(R.string.OK),null).create());return;}
        if(busy)return;
        if(position==importRow){Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{StudioSchema.MIME,"application/octet-stream","application/json"});startActivityForResult(intent,OPEN);}
        else if(position==export||position==share)generate(position==share,Collections.emptySet());
    }
    private void generate(boolean sharing,Set<String> selected) {
        busy=true;int token=++generation;WeakReference<FlexyStudioActivity> weak=new WeakReference<>(this);
        try{work=FlexyStudioIO.execute(()->{
            byte[] encoded=null;boolean empty=false;
            try{encoded=StudioCodec.encode(StudioCodec.export("MiFlexyGram.flexyGram",FlexyStudioStore.snapshot(),selected));}
            catch(IllegalArgumentException invalid){empty="empty".equals(invalid.getMessage());}
            catch(Exception ignored){}
            byte[] data=encoded;boolean noChanges=empty;
            AndroidUtilities.runOnUIThread(()->{
                FlexyStudioActivity owner=weak.get();if(owner==null||owner.generation!=token||owner.getParentActivity()==null)return;
                owner.busy=false;
                if(noChanges){owner.chooseSections(sharing);return;}
                if(data==null){FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioReadError);return;}
                if(sharing)owner.share(data);else {owner.pendingExport=data;Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(StudioSchema.MIME).putExtra(Intent.EXTRA_TITLE,"MiFlexyGram.flexyGram");owner.startActivityForResult(intent,SAVE);}
            });
        });}catch(java.util.concurrent.RejectedExecutionException rejected){busy=false;FlexyStyleInstallHelper.error(this,R.string.FlexyStudioBusy);}
    }
    private void chooseSections(boolean sharing) {
        if(getParentActivity()==null)return;String[] ids=StudioSchema.sections().toArray(new String[0]);
        LinearLayout content=new LinearLayout(getParentActivity());content.setOrientation(LinearLayout.VERTICAL);List<CheckBoxCell> cells=new ArrayList<>();
        for(String id:ids){CheckBoxCell cell=new CheckBoxCell(getParentActivity(),1,getResourceProvider());cell.setText(getString(FlexyStudioText.section(id)),"",false,true);cell.setMultiline(true);cell.setOnClickListener(v->cell.setChecked(!cell.isChecked(),true));cells.add(cell);content.addView(cell);}
        showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(getString(R.string.FlexyStudioNoChanges)).setMessage(getString(R.string.FlexyStudioChooseSections)).setView(content)
            .setPositiveButton(getString(R.string.Continue),(d,w)->{Set<String> chosen=new HashSet<>();for(int i=0;i<ids.length;i++)if(cells.get(i).isChecked())chosen.add(ids[i]);if(chosen.isEmpty())FlexyStyleInstallHelper.error(this,R.string.FlexyStudioNothingSelected);else generate(sharing,chosen);})
            .setNegativeButton(getString(R.string.Cancel),null).create());
    }
    private void share(byte[] data) {
        busy=true;int token=++generation;WeakReference<FlexyStudioActivity> weak=new WeakReference<>(this);Context context=ApplicationLoader.applicationContext;
        try{work=FlexyStudioIO.execute(()->{
            File file=null;try{file=FlexyStudioFiles.share(context,data);}catch(Exception ignored){}File ready=file;
            AndroidUtilities.runOnUIThread(()->{FlexyStudioActivity owner=weak.get();if(owner==null||owner.generation!=token||owner.getParentActivity()==null)return;owner.busy=false;
                if(ready==null){FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioWriteError);return;}
                try{owner.startActivityForResult(Intent.createChooser(FlexyStudioFiles.shareIntent(context,ready),getString(R.string.FlexyStudioShare)),0x4653);}catch(Exception unavailable){FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioWriteError);}
            });
        });}catch(java.util.concurrent.RejectedExecutionException rejected){busy=false;FlexyStyleInstallHelper.error(this,R.string.FlexyStudioBusy);}
    }
    @Override public void onActivityResultFragment(int code,int result,Intent data) {
        super.onActivityResultFragment(code,result,data);if(result!=Activity.RESULT_OK||data==null||data.getData()==null){if(code==SAVE)pendingExport=null;return;}
        if(code==OPEN){FlexyStyleInstallHelper.openUri(this,data.getData());return;}
        if(code!=SAVE||pendingExport==null)return;
        byte[] bytes=pendingExport;pendingExport=null;Uri uri=data.getData();WeakReference<FlexyStudioActivity> weak=new WeakReference<>(this);int token=++generation;busy=true;
        try{work=FlexyStudioIO.execute(()->{
            boolean ok=false;
            try {
                ContentResolver resolver=ApplicationLoader.applicationContext.getContentResolver();String name=null;
                if(!"content".equals(uri.getScheme()))throw new IOException("uri");
                try(Cursor cursor=resolver.query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)) {if(cursor!=null&&cursor.moveToFirst())name=cursor.getString(0);}
                if(!StudioSchema.filename(name))throw new IOException("extension");
                try(OutputStream out=resolver.openOutputStream(uri,"w")){if(out==null)throw new IOException("stream");out.write(bytes);out.flush();}ok=true;
            }catch(Exception ignored){}
            boolean saved=ok;AndroidUtilities.runOnUIThread(()->{FlexyStudioActivity owner=weak.get();if(owner==null||owner.generation!=token||owner.getParentActivity()==null)return;owner.busy=false;FlexyStyleInstallHelper.error(owner,saved?R.string.FlexyStudioSaved:R.string.FlexyStudioWriteError);});
        });}catch(java.util.concurrent.RejectedExecutionException rejected){busy=false;FlexyStyleInstallHelper.error(this,R.string.FlexyStudioBusy);}
    }
    @Override public void onResume(){super.onResume();FlexyStyleInstallHelper.resume(this);}
    @Override public void onTransitionAnimationEnd(boolean open,boolean backward){super.onTransitionAnimationEnd(open,backward);FlexyStyleInstallHelper.resume(this);}
    @Override public void onFragmentDestroy(){generation++;FlexyStudioIO.cancel(work);FlexyStyleInstallHelper.cancel(this);pendingExport=null;super.onFragmentDestroy();}
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);if(pendingExport!=null)args.putByteArray("flexystudioExport",pendingExport);}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);byte[] saved=args.getByteArray("flexystudioExport");if(saved!=null&&saved.length<=StudioSchema.MAX_BYTES)pendingExport=saved;}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context){super(context);}
        @Override public int getItemViewType(int position){return position==header||position==tools?TYPE_HEADER:position==shadow||position==toolsShadow?TYPE_SHADOW:position==files?TYPE_CHECK:NAV;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){if(type==NAV)return new RecyclerListView.Holder(new app.flexygram.settings.signature.Settings2Cell(parent.getContext(),resourcesProvider));return super.onCreateViewHolder(parent,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==header||position==tools)((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText(getString(position==header?R.string.FlexyStudioConfiguration:R.string.FlexyFilesTools));
            else if(position==files)((org.telegram.ui.Cells.TextCheckCell)holder.itemView).setTextAndValueAndCheck(getString(R.string.FlexyFilesEnable),getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),true,true,false);
            else if(position==help)((SignatureNavigationCell)holder.itemView).bind(getString(R.string.FlexyFilesHow),R.drawable.msg_info,false);
            else if(position!=shadow&&position!=toolsShadow)((app.flexygram.settings.signature.Settings2Cell)holder.itemView).bind(getString(position==export?R.string.FlexyStudioExport:position==importRow?R.string.FlexyStudioImport:R.string.FlexyStudioShare),"",position==share?R.drawable.settings3_stack:R.drawable.settings3_document,0,position!=share);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return holder.getItemViewType()==NAV||holder.getItemViewType()==TYPE_CHECK;}
    }
}
