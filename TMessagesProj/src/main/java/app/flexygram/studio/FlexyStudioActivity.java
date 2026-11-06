/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import static org.telegram.messenger.LocaleController.getString;
import android.app.Activity;
import android.content.*;
import android.net.Uri;
import android.os.Bundle;
import android.view.*;
import app.flexygram.settings.*;
import app.flexygram.studio.core.*;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.AlertDialog;
import org.telegram.ui.Components.RecyclerListView;
import androidx.recyclerview.widget.RecyclerView;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.concurrent.Future;

/** Configuration transfer and animation preference. SAF and sharing need no storage permission. */
public final class FlexyStudioActivity extends SignatureMatteSettingsActivity {
    private static final int NAV=110, SAVE=0x4651, OPEN=0x4652;
    private int header,export,importRow,share,shadow,tools,files,help,toolsShadow,motionHeader,fastMotion,motionShadow;
    private File pendingExport;
    private boolean busy;
    private Future<?> work;
    private int generation;
    @Override protected String getActionBarTitle(){return getString(R.string.FlexyStudioTitle);}
    @Override protected void updateRows(){super.updateRows();header=addRow();export=addRow("flexystudioExport");importRow=addRow("flexystudioImport");share=addRow("flexystudioShare");shadow=addRow();motionHeader=addRow();fastMotion=addRow("flexystudioFastMotion");motionShadow=addRow();tools=files=help=toolsShadow=-1;}
    @Override public View createView(Context context){View v=super.createView(context);actionBar.centerTitle();listView.setSections(AndroidUtilities.dp(16),AndroidUtilities.dp(20),true);listView.setItemAnimator(null);return v;}
    @Override protected BaseListAdapter createAdapter(Context context){return new Adapter(context);}
    @Override protected void onItemClick(View view,int position,float x,float y) {
        if(position==fastMotion){if(busy)return;app.flexygram.animation.FastMotionConfig.setEnabled(!app.flexygram.animation.FastMotionConfig.isEnabled());listAdapter.notifyItemChanged(position);return;}
        if(position==files){app.flexygram.files.FlexyFiles.enabled(!app.flexygram.files.FlexyFiles.enabled());if(view instanceof org.telegram.ui.Cells.TextCheckCell)((org.telegram.ui.Cells.TextCheckCell)view).setTextAndValueAndCheck(getString(R.string.FlexyFilesEnable),getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),true,true,false);return;}
        if(position==help){showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle("FlexyFiles").setMessage(getString(R.string.FlexyFilesHelp)).setPositiveButton(getString(R.string.OK),null).create());return;}
        if(busy)return;
        if(position==importRow){Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType("*/*");intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{StudioSchema.MIME,"application/octet-stream","application/json"});try { startActivityForResult(intent,OPEN); } catch(Exception unavailable) { FlexyStyleInstallHelper.error(this,R.string.FlexyStudioReadError); }}
        else if(position==export||position==share)generate(position==share);
    }
    private void generate(boolean sharing) {
        busy=true;int token=++generation;WeakReference<FlexyStudioActivity> weak=new WeakReference<>(this);
        try{work=FlexyStudioIO.execute(()->{
            byte[] encoded=null;File staged=null;
            try{StudioCodec.Preset preset=StudioCodec.create("MiFlexyGram.flexyGram",FlexyStudioStore.snapshot());FlexyStudioStore.validate(preset);encoded=StudioCodec.encode(preset);if(!sharing)staged=FlexyStudioFiles.stage(ApplicationLoader.applicationContext,encoded);}
            catch(Exception failed){encoded=null;org.telegram.messenger.FileLog.e("FlexyStudio export: "+failed.getClass().getSimpleName());}
            byte[] data=encoded;File pending=staged;
            AndroidUtilities.runOnUIThread(()->{
                FlexyStudioActivity owner=weak.get();if(owner==null||owner.generation!=token||owner.getParentActivity()==null)return;
                owner.busy=false;

                if(data==null||!sharing&&pending==null){FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioExportError);return;}
                if(sharing)owner.share(data);else {owner.pendingExport=pending;Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(StudioSchema.MIME).putExtra(Intent.EXTRA_TITLE,"MiFlexyGram.flexyGram");try { owner.busy=true; owner.startActivityForResult(intent,SAVE); } catch(Exception unavailable) { owner.busy=false; pending.delete(); owner.pendingExport=null; FlexyStyleInstallHelper.error(owner,R.string.FlexyStudioWriteError); }}
            });
        });}catch(java.util.concurrent.RejectedExecutionException rejected){busy=false;FlexyStyleInstallHelper.error(this,R.string.FlexyStudioBusy);}
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
        super.onActivityResultFragment(code,result,data);if(result!=Activity.RESULT_OK||data==null||data.getData()==null){if(code==SAVE){if(pendingExport!=null)pendingExport.delete();pendingExport=null;busy=false;}return;}
        if(code==OPEN){FlexyStyleInstallHelper.openUri(this,data.getData());return;}
        if(code!=SAVE||pendingExport==null)return;
        File source=pendingExport;pendingExport=null;Uri uri=data.getData();WeakReference<FlexyStudioActivity> weak=new WeakReference<>(this);int token=++generation;busy=true;
        try{work=FlexyStudioIO.execute(()->{
            boolean ok=false;
            try {
                ContentResolver resolver=ApplicationLoader.applicationContext.getContentResolver();
                if(!"content".equals(uri.getScheme())||source.length()<1||source.length()>StudioSchema.MAX_BYTES)throw new IOException("uri");
                try(InputStream in=new FileInputStream(source);OutputStream out=FlexyStudioFiles.openForExport(resolver,uri)) {
                    if(out==null)throw new IOException("stream");byte[] buffer=new byte[8192];int n;
                    while((n=in.read(buffer))!=-1)out.write(buffer,0,n);out.flush();
                }ok=true;
            }catch(Exception ignored){}finally{source.delete();}
            boolean saved=ok;AndroidUtilities.runOnUIThread(()->{FlexyStudioActivity owner=weak.get();if(owner==null||owner.generation!=token||owner.getParentActivity()==null)return;owner.busy=false;FlexyStyleInstallHelper.error(owner,saved?R.string.FlexyStudioSaved:R.string.FlexyStudioWriteError);});
        });}catch(java.util.concurrent.RejectedExecutionException rejected){busy=false;FlexyStyleInstallHelper.error(this,R.string.FlexyStudioBusy);}
    }
    @Override public void onResume(){super.onResume();FlexyStyleInstallHelper.resume(this);}
    @Override public void onTransitionAnimationEnd(boolean open,boolean backward){super.onTransitionAnimationEnd(open,backward);FlexyStyleInstallHelper.resume(this);}
    @Override public void onFragmentDestroy(){generation++;FlexyStudioIO.cancel(work);FlexyStyleInstallHelper.cancel(this);pendingExport=null;super.onFragmentDestroy();}
    @Override public void saveSelfArgs(Bundle args){super.saveSelfArgs(args);if(pendingExport!=null)args.putString("flexystudioExportFile",pendingExport.getName());}
    @Override public void restoreSelfArgs(Bundle args){super.restoreSelfArgs(args);pendingExport=FlexyStudioFiles.pending(ApplicationLoader.applicationContext,args.getString("flexystudioExportFile"));busy=pendingExport!=null;}
    private final class Adapter extends MatteListAdapter {
        Adapter(Context context){super(context);}
        @Override public int getItemViewType(int position){return position==header||position==tools||position==motionHeader?TYPE_HEADER:position==shadow||position==toolsShadow||position==motionShadow?TYPE_SHADOW:position==files||position==fastMotion?TYPE_CHECK:NAV;}
        @Override public RecyclerView.ViewHolder onCreateViewHolder(ViewGroup parent,int type){if(type==NAV)return new RecyclerListView.Holder(new app.flexygram.settings.signature.Settings2Cell(parent.getContext(),resourcesProvider));return super.onCreateViewHolder(parent,type);}
        @Override public void onBindViewHolder(RecyclerView.ViewHolder holder,int position,boolean partial){
            if(position==header||position==tools||position==motionHeader)((tw.nekomimi.nekogram.ui.cells.HeaderCell)holder.itemView).setText(getString(position==header?R.string.FlexyStudioConfiguration:position==motionHeader?R.string.FlexyStudioMotion:R.string.FlexyFilesTools));
            else if(position==fastMotion)((org.telegram.ui.Cells.TextCheckCell)holder.itemView).setTextAndValueAndCheck(getString(R.string.FlexyStudioFastMotion),getString(R.string.FlexyStudioFastMotionInfo),app.flexygram.animation.FastMotionConfig.isEnabled(),true,false,false);
            else if(position==files)((org.telegram.ui.Cells.TextCheckCell)holder.itemView).setTextAndValueAndCheck(getString(R.string.FlexyFilesEnable),getString(app.flexygram.files.FlexyFiles.enabled()?R.string.FlexyFilesDormant:R.string.FlexyFilesDisabled),app.flexygram.files.FlexyFiles.enabled(),true,true,false);
            else if(position==help)((SignatureNavigationCell)holder.itemView).bind(getString(R.string.FlexyFilesHow),R.drawable.msg_info,false);
            else if(position!=shadow&&position!=toolsShadow&&position!=motionShadow)((app.flexygram.settings.signature.Settings2Cell)holder.itemView).bind(getString(position==export?R.string.FlexyStudioExport:position==importRow?R.string.FlexyStudioImport:R.string.FlexyStudioShare),"",position==share?R.drawable.settings3_stack:R.drawable.settings3_document,0,position!=share);
        }
        @Override public boolean isEnabled(RecyclerView.ViewHolder holder){return holder.getItemViewType()==NAV||holder.getItemViewType()==TYPE_CHECK;}
    }
}
