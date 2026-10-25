/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;

import static org.telegram.messenger.LocaleController.getString;
import android.animation.*;
import android.app.Activity;
import android.content.*;
import android.content.res.AssetFileDescriptor;
import android.database.Cursor;
import android.net.Uri;
import android.os.*;
import android.provider.OpenableColumns;
import android.view.View;
import android.widget.Toast;
import app.flexygram.studio.core.*;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.BaseFragment;
import org.telegram.ui.LaunchActivity;
import org.telegram.ui.Cells.ChatMessageCell;
import org.telegram.ui.Cells.SharedDocumentCell;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.*;
import java.util.concurrent.Future;

/** Native document interception only; plugin/Python code is neither called nor reused. */
public final class FlexyStyleInstallHelper {
    private static final WeakHashMap<BaseFragment,Request> pending=new WeakHashMap<>();
    private static Uri externalUri;
    private static WeakReference<Activity> externalOwner;
    private FlexyStyleInstallHelper(){}
    public static boolean recognized(String name){return BuildConfig.CONNECTED_ALPHA&&StudioSchema.filename(name);}
    public static boolean isStudioIntent(Intent intent) {
        if(!BuildConfig.CONNECTED_ALPHA||intent==null||!Intent.ACTION_VIEW.equals(intent.getAction()))return false;
        Uri uri=intent.getData();if(uri==null||uri.getAuthority()==null||!"content".equals(uri.getScheme()))return false;
        return StudioSchema.MIME.equals(intent.getType())||recognized(uri.getLastPathSegment());
    }
    public static void acceptExternal(Activity activity,Uri uri){externalOwner=new WeakReference<>(activity);externalUri=uri;}
    public static void cancelExternal(Activity activity){if(externalOwner!=null&&externalOwner.get()==activity){externalOwner=null;externalUri=null;}}
    public static void resumeExternal(Activity activity) {
        if(externalOwner==null||externalOwner.get()!=activity||externalUri==null)return;
        BaseFragment fragment=LaunchActivity.getSafeLastFragment();
        if(fragment==null||fragment.getParentActivity()!=activity||fragment.getFragmentView()==null)return;
        if(!UserConfig.getInstance(UserConfig.selectedAccount).isClientActivated()) {
            externalUri=null;externalOwner=null;error(fragment,R.string.FlexyStudioLoginFirst);return;
        }
        Uri uri=externalUri;externalUri=null;externalOwner=null;openUri(fragment,uri);
    }
    public static boolean handleMessageTap(BaseFragment fragment,MessageObject message,View source) {
        if(message==null||!recognized(message.getDocumentName()))return false;
        if(message.isSending()||message.isSendError())return false;
        if(message.isSensitive()&&message.hasMediaSpoilers()&&!message.needDrawBluredPreview()&&!message.isMediaSpoilersRevealed)return false;
        if(fragment==null||fragment.getParentActivity()==null)return true;
        Request old=pending.get(fragment);
        if(old!=null&&old.messageId==message.getId()&&old.dialogId==message.getDialogId()) {
            if(old.waiting) {FileLoader.getInstance(message.currentAccount).cancelLoadFile(message.getDocument());cancel(fragment);update(source);} else old.show();
            return true;
        }
        cancel(fragment);
        if(message.getDocument()==null||message.getDocument().size>StudioSchema.MAX_BYTES){error(fragment,R.string.FlexyStudioInvalid);return true;}
        Request request=new Request(fragment,source);request.messageId=message.getId();request.dialogId=message.getDialogId();request.account=message.currentAccount;request.filename=message.getDocumentName();
        final var document=message.getDocument();request.cancelDownload=()->FileLoader.getInstance(request.account).cancelLoadFile(document);
        request.file=FileLoader.getInstance(request.account).getPathToMessage(message.messageOwner);
        if ((request.file==null||!request.file.isFile())&&message.messageOwner.attachPath!=null&&!message.messageOwner.attachPath.isEmpty()) {
            File attached=new File(message.messageOwner.attachPath);if(attached.isFile())request.file=attached;
        }
        pending.put(fragment,request);request.pulse();
        if(request.file!=null&&request.file.isFile())request.read();
        else {
            request.waiting=true;ApplicationLoader.applicationHandler.postDelayed(request.timeout,30000);request.tag=DownloadController.getInstance(request.account).generateObserverTag();
            DownloadController.getInstance(request.account).addLoadingFileObserver(FileLoader.getAttachFileName(message.getDocument()),message,request);
            message.putInDownloadsStore=true;
            FileLoader.getInstance(request.account).loadFile(message.getDocument(),message,FileLoader.PRIORITY_LOW,0);update(source);
        }
        return true;
    }
    private static void update(View source) {
        if(source instanceof ChatMessageCell)((ChatMessageCell)source).updateButtonState(false,true,false);
        if(source instanceof SharedDocumentCell)((SharedDocumentCell)source).updateFileExistIcon(true);
    }
    public static void openUri(BaseFragment fragment,Uri uri) {
        if(uri==null||uri.getAuthority()==null||!"content".equals(uri.getScheme())){error(fragment,R.string.FlexyStudioInvalid);return;}
        cancel(fragment);Request request=new Request(fragment,fragment.getFragmentView());request.uri=uri;pending.put(fragment,request);request.read();
    }
    public static void resume(BaseFragment fragment) {Request request=pending.get(fragment);if(request!=null)request.show();}
    public static void cancel(BaseFragment fragment){Request request=pending.remove(fragment);if(request!=null)request.cancel();}
    public static void error(BaseFragment fragment,int string){
        Context context=fragment!=null&&fragment.getParentActivity()!=null?fragment.getParentActivity():ApplicationLoader.applicationContext;
        Toast.makeText(context,getString(string),Toast.LENGTH_LONG).show();
    }
    private static final class Request implements DownloadController.FileDownloadProgressListener,View.OnAttachStateChangeListener {
        final WeakReference<BaseFragment> owner;
        final WeakReference<View> source;
        final CancellationSignal signal=new CancellationSignal();
        volatile boolean canceled;
        volatile AssetFileDescriptor descriptor;
        Future<?> work;
        File file;Uri uri;String filename;int account,tag=-1,bytes,messageId;long dialogId;boolean waiting,showing;
        StudioCodec.Preset preset;Animator pulse;Runnable cancelDownload;
        final Runnable timeout;
        Request(BaseFragment fragment,View view){owner=new WeakReference<>(fragment);source=new WeakReference<>(view);timeout=()->{BaseFragment current=owner.get();if(current!=null&&!canceled){cancel();pending.remove(current);error(current,R.string.FlexyStudioReadError);}};if(view!=null)view.addOnAttachStateChangeListener(this);}
        void pulse() {
            View view=source.get();if(view==null||!SharedConfig.animationsEnabled()||(Build.VERSION.SDK_INT>=26&&!ValueAnimator.areAnimatorsEnabled())||view.getScaleX()!=1f||view.getScaleY()!=1f)return;
            pulse=ObjectAnimator.ofPropertyValuesHolder(view,PropertyValuesHolder.ofFloat(View.SCALE_X,1f,.98f,1f),PropertyValuesHolder.ofFloat(View.SCALE_Y,1f,.98f,1f));pulse.setDuration(120);pulse.start();
        }
        void read() {
            if(canceled)return;waiting=false;if(tag>=0)DownloadController.getInstance(account).removeLoadingFileObserver(this);
            ApplicationLoader.applicationHandler.postDelayed(timeout,30000);
            try{work=FlexyStudioIO.execute(()->{
                StudioCodec.Preset result=null;String realName=filename;int count=0;String unsupported=null;
                try {
                    InputStream input;
                    if(uri!=null) {
                        if(AndroidUtilities.isInternalUri(uri)&&!uri.getAuthority().equals(ApplicationLoader.getApplicationId()+".flexystudio"))throw new IOException("internal");
                        ContentResolver resolver=ApplicationLoader.applicationContext.getContentResolver();
                        try(Cursor cursor=resolver.query(uri,new String[]{OpenableColumns.DISPLAY_NAME,OpenableColumns.SIZE},null,null,null,signal)) {
                            if(cursor!=null&&cursor.moveToFirst()) {
                                int name=cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME);if(name>=0)realName=cursor.getString(name);
                                int size=cursor.getColumnIndex(OpenableColumns.SIZE);if(size>=0&&!cursor.isNull(size)&&cursor.getLong(size)>StudioSchema.MAX_BYTES)throw new IOException("size");
                            }
                        }
                        if(!StudioSchema.filename(realName))throw new IOException("name");
                        descriptor=resolver.openAssetFileDescriptor(uri,"r",signal);if(descriptor==null)throw new IOException("stream");input=descriptor.createInputStream();
                    } else {if(file==null)throw new IOException("file");input=new FileInputStream(file);}
                    try(InputStream in=input){byte[] data=StudioCodec.readLimited(in);count=data.length;if(canceled)throw new IOException("canceled");result=StudioCodec.decode(data,BuildConfig.VERSION_CODE);}
                }catch(StudioSchema.Unsupported incompatible){unsupported=incompatible.identifier;}catch(Exception invalid){}finally{closeDescriptor();}
                StudioCodec.Preset ready=result;String actual=realName;int size=count;String incompatible=unsupported;
                AndroidUtilities.runOnUIThread(()->{
                    ApplicationLoader.applicationHandler.removeCallbacks(timeout);if(canceled)return;
                    BaseFragment fragment=owner.get();if(fragment==null){cancel();return;}
                    if(ready==null){pending.remove(fragment);cancel();if(incompatible!=null)Toast.makeText(fragment.getParentActivity(),LocaleController.formatString("FlexyStudioUnsupported",R.string.FlexyStudioUnsupported,incompatible),Toast.LENGTH_LONG).show();else error(fragment,R.string.FlexyStudioInvalid);return;}
                    preset=ready;filename=actual;bytes=size;show();
                });
            });}catch(java.util.concurrent.RejectedExecutionException busy){BaseFragment f=owner.get();if(f!=null){pending.remove(f);error(f,R.string.FlexyStudioBusy);}cancel();}
        }
        void show() {
            BaseFragment fragment=owner.get();
            if(canceled||preset==null||showing||fragment==null||fragment.getParentActivity()==null||fragment.isPaused()||fragment.getFragmentView()==null||!fragment.getFragmentView().isAttachedToWindow())return;
            FlexyStudioSheet sheet=new FlexyStudioSheet(fragment,preset,filename,bytes);
            if(fragment.showDialog(sheet,false,d->{pending.remove(fragment);cancel();})!=null){showing=true;if(pulse!=null){pulse.cancel();View v=source.get();if(v!=null){v.setScaleX(1f);v.setScaleY(1f);}}}
        }
        private void closeDescriptor(){AssetFileDescriptor fd=descriptor;descriptor=null;if(fd!=null)try{fd.close();}catch(IOException ignored){}}
        void cancel(){if(canceled)return;canceled=true;try{signal.cancel();}catch(RuntimeException ignored){}closeDescriptor();FlexyStudioIO.cancel(work);ApplicationLoader.applicationHandler.removeCallbacks(timeout);if(tag>=0)DownloadController.getInstance(account).removeLoadingFileObserver(this);View view=source.get();if(view!=null){view.removeOnAttachStateChangeListener(this);if(pulse!=null){pulse.cancel();view.setScaleX(1f);view.setScaleY(1f);}}preset=null;}
        public void onViewAttachedToWindow(View v){}
        public void onViewDetachedFromWindow(View v){BaseFragment fragment=owner.get();if(fragment!=null)pending.remove(fragment);cancel();}
        public void onFailedDownload(String name,boolean userCanceled){if(canceled)return;BaseFragment fragment=owner.get();if(fragment!=null)pending.remove(fragment);cancel();if(!userCanceled&&fragment!=null)error(fragment,R.string.FlexyStudioReadError);}
        public void onSuccessDownload(String name){read();}
        public void onProgressDownload(String name,long downloaded,long total){if(!canceled&&(downloaded>StudioSchema.MAX_BYTES||total>StudioSchema.MAX_BYTES)){if(cancelDownload!=null)cancelDownload.run();onFailedDownload(name,false);}}
        public void onProgressUpload(String name,long uploaded,long total,boolean encrypted){}
        public int getObserverTag(){return tag;}
    }
}
