/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import static org.telegram.messenger.LocaleController.getString;
import static org.telegram.messenger.AndroidUtilities.dp;
import android.app.Activity;
import android.content.*;
import android.graphics.*;
import android.net.Uri;
import android.os.Bundle;
import android.text.*;
import android.text.style.ForegroundColorSpan;
import android.view.*;
import android.webkit.*;
import android.widget.*;
import androidx.core.content.FileProvider;
import app.flexygram.files.core.*;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.*;
import java.io.*;
import java.lang.ref.WeakReference;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.regex.*;

/** Native bounded editor. All document/ZIP/SAF/format work is explicit and worker-owned. */
public final class FlexyFileEditorActivity extends BaseFragment {
    private static final int SAVE=0x464c;
    private final File source;private final String originalName,entry;private final long dialog;private final int account;
    private final FilesWork work=new FilesWork();private volatile SelectedDocument document;
    private FilesCodeView editor;private TextView status;private LinearLayout panel;private byte[] binary;private SelectedDocument.Text text;
    private final EditHistory history=new EditHistory();private boolean internal,dirty,ready;private int revision;private File output;private WebView html;
    private final Pattern syntax=Pattern.compile("\"[^\"\\r\\n]*\"|\\b(?:true|false|null|if|else|return|class|const|let|var|function|import|public|private)\\b|\\b[0-9]+(?:\\.[0-9]+)?\\b");
    private String retainedText;private int retainedStart,retainedEnd;
    private FlexyFilesDirectSend.Copy directCopy;
    /** Return to the originating FlexyFiles level after closing any editor. */
    private BaseFragment explorerOwner;
    private String explorerFolder;
    private String explorerQuery="";
    private android.os.Parcelable explorerScroll;
    private boolean explorerReturnScheduled;
    private final Runnable highlight=()->highlightParagraph();
    /** Only active paragraph is colored; never accumulate spans across thousands of lines. */
    private final ArrayList<ForegroundColorSpan> activeSyntaxHighlights=new ArrayList<>(128);
    public FlexyFileEditorActivity(File file,String name,String entry,long dialog,int account){source=file;originalName=name;this.entry=entry;this.dialog=dialog;this.account=account;}
    public FlexyFileEditorActivity(File file,String name,String entry,long dialog,int account,BaseFragment explorerOwner,String explorerFolder){
        this(file,name,entry,dialog,account);this.explorerOwner=explorerOwner;this.explorerFolder=explorerFolder==null?"":explorerFolder;
    }
    FlexyFileEditorActivity returnContext(String query,android.os.Parcelable scroll){explorerQuery=query;explorerScroll=scroll;return this;}
    /** Reopen only after Telegram reports the originating chat fully visible. No timers. */
    private void scheduleExplorerReturn(){
        if(explorerReturnScheduled||explorerOwner==null)return;
        explorerReturnScheduled=true;
        BaseFragment host=explorerOwner;String folder=explorerFolder,searchQuery=explorerQuery;android.os.Parcelable scroll=explorerScroll;
        host.whenFullyVisible(()->{
            if(host.getParentActivity()==null||!FlexyFiles.enabled())return;
            FlexyFilesSheet next=new FlexyFilesSheet(host,source,originalName,dialog,account,folder,true,searchQuery,scroll);
            if(host.showDialog(next)==null)next.dismiss();
        });
    }
    private String filename(){String name=entry==null?originalName:entry.substring(entry.lastIndexOf('/')+1);return name==null?"edited.txt":name;}
    private int color(int key){return Theme.getColor(key,getResourceProvider());}
    @Override public View createView(Context c){
        retainEditor();AndroidUtilities.cancelRunOnUIThread(highlight);work.cancel();
        if(actionBar==null)actionBar=createActionBar(c);
        actionBar.setBackButtonImage(R.drawable.ic_ab_back);actionBar.setTitle("FlexyFiles");actionBar.setAllowOverlayTitle(false);
        actionBar.setActionBarMenuOnItemClick(new ActionBar.ActionBarMenuOnItemClick(){@Override public void onItemClick(int id){if(id==-1){if(onBackPressed(true))finishFragment();}else if(id==0)showTools();else command(id);}});
        actionBar.createMenu().addItem(0,R.drawable.ic_ab_other);
        panel=new LinearLayout(c);panel.setOrientation(LinearLayout.VERTICAL);panel.setBackgroundColor(color(Theme.key_windowBackgroundWhite));status=new TextView(c);status.setTextColor(color(Theme.key_windowBackgroundWhiteGrayText2));status.setTextSize(13);status.setPadding(dp(16),dp(10),dp(16),dp(10));status.setText(getString(R.string.Loading));panel.addView(status,new LinearLayout.LayoutParams(-1,-2));
        editor=new FilesCodeView(c,color(Theme.key_windowBackgroundWhiteBlackText),color(Theme.key_windowBackgroundWhiteGrayText2));editor.setFocusableInTouchMode(true);editor.setEnabled(false);panel.addView(editor,new LinearLayout.LayoutParams(-1,0,1));
        editor.selectionChanged=()->{AndroidUtilities.cancelRunOnUIThread(highlight);AndroidUtilities.runOnUIThread(highlight,120);};
        editor.addTextChangedListener(new TextWatcher(){String before;int start;
            public void beforeTextChanged(CharSequence s,int st,int count,int after){if(!internal){start=st;before=s.subSequence(st,st+count).toString();}}
            public void onTextChanged(CharSequence s,int st,int count,int after){if(!internal){history.record(start,before,s.subSequence(st,st+after).toString());dirty=true;revision++;}}
            public void afterTextChanged(Editable e){if(!internal){AndroidUtilities.cancelRunOnUIThread(highlight);AndroidUtilities.runOnUIThread(highlight,120);}}
        });fragmentView=panel;
        if(retainedText!=null&&text!=null&&document!=null){internal=true;editor.setText(retainedText);editor.setSelection(Math.min(editor.length(),Math.max(0,retainedStart)),Math.min(editor.length(),Math.max(0,retainedEnd)));internal=false;editor.setEnabled(true);ready=true;retainedText=null;status.setText(filename()+" · "+text.encoding+" · "+text.newline);highlightParagraph();}
        else load();return fragmentView;
    }
    private void retainEditor(){if(editor!=null&&text!=null){retainedText=editor.getText().toString();retainedStart=editor.getSelectionStart();retainedEnd=editor.getSelectionEnd();}}
    @Override public void clearViews(){retainEditor();AndroidUtilities.cancelRunOnUIThread(highlight);work.cancel();destroyHtml();activeSyntaxHighlights.clear();editor=null;status=null;panel=null;super.clearViews();}
    private interface Result {void ready(FlexyFileEditorActivity owner,Object value);}
    private interface Job {Object run()throws Exception;}
    private void job(Job job,Result result){FilesWork tasks=work;int token=tasks.token()+1;WeakReference<FlexyFileEditorActivity> weak=new WeakReference<>(this);
        tasks.submit(()->{Object value=null;boolean ok=true;try{value=job.run();}catch(Exception failure){ok=false;}Object done=value;boolean success=ok;
            AndroidUtilities.runOnUIThread(()->{FlexyFileEditorActivity owner=weak.get();if(owner==null||!tasks.current(token)||owner.getParentActivity()==null||owner.status==null)return;if(success)result.ready(owner,done);else{owner.status.setText(getString(R.string.FlexyFilesError));owner.ready=owner.text!=null||owner.binary!=null;}});});
    }
    private void load(){File selected=source;String path=entry;job(()->{SelectedDocument previous=document;document=null;if(previous!=null)previous.close();SelectedDocument reader=new SelectedDocument(selected);document=reader;if(Thread.currentThread().isInterrupted()){reader.close();throw new InterruptedIOException();}return reader.read(path,SelectedDocument.MAX_ENTRY);},(owner,value)->{
        owner.binary=(byte[])value;owner.ready=true;try{owner.text=SelectedDocument.text(owner.binary);owner.internal=true;owner.editor.setText(owner.text.value);owner.editor.setEnabled(true);owner.internal=false;owner.status.setText(owner.filename()+" · "+owner.text.encoding+" · "+owner.text.newline);owner.highlightParagraph();owner.recoverDraft();}
        catch(IOException binary){owner.editor.setVisibility(View.GONE);owner.status.setText(owner.filename()+" · "+AndroidUtilities.formatFileSize(owner.binary.length)+"\n"+getString(R.string.FlexyFilesBinary));owner.image();}
    });}
    private void recoverDraft(){File f=source;String path=entry;job(()->{File draft=FilesCache.draft(f,path);if(!draft.isFile()||draft.length()>SelectedDocument.MAX_TEXT)return null;try(InputStream in=new FileInputStream(draft)){ByteArrayOutputStream data=new ByteArrayOutputStream();byte[] buffer=new byte[4096];int count;while((count=in.read(buffer))!=-1){if(Thread.currentThread().isInterrupted()||data.size()+count>SelectedDocument.MAX_TEXT)throw new IOException();data.write(buffer,0,count);}return SelectedDocument.text(data.toByteArray()).value;}},(owner,value)->{if(value==null)return;owner.showDialog(new AlertDialog.Builder(owner.getParentActivity(),owner.getResourceProvider()).setTitle(getString(R.string.FlexyFilesRecover)).setPositiveButton(getString(R.string.FlexyFilesRestore),(d,w)->{owner.replaceText((String)value);}).setNegativeButton(getString(R.string.FlexyFilesDiscard),(d,w)->owner.deleteDraft()).create());});}
    private void deleteDraft(){File f=source;String path=entry;job(()->{FilesCache.draft(f,path).delete();return null;},(o,v)->{});}
    private void image(){String lower=filename().toLowerCase(Locale.ROOT);if(!(lower.endsWith(".png")||lower.endsWith(".jpg")||lower.endsWith(".jpeg")||lower.endsWith(".webp")))return;byte[] data=binary;
        job(()->{BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;BitmapFactory.decodeByteArray(data,0,data.length,options);if(options.outWidth<=0||options.outHeight<=0||(long)options.outWidth*options.outHeight>32_000_000)throw new IOException();options.inSampleSize=1;while(options.outWidth/options.inSampleSize>1024||options.outHeight/options.inSampleSize>1024)options.inSampleSize*=2;options.inJustDecodeBounds=false;return BitmapFactory.decodeByteArray(data,0,data.length,options);},(owner,value)->{if(value!=null){ImageView image=new ImageView(owner.getParentActivity());image.setScaleType(ImageView.ScaleType.FIT_CENTER);image.setImageBitmap((Bitmap)value);owner.panel.addView(image,new LinearLayout.LayoutParams(-1,0,1));}});
    }
    /** On-demand grouped sheet, shared look and spacing with the native .flexyGram sheet. */
    private void showTools(){
        if(getParentActivity()==null||!ready)return;
        String lower=filename().toLowerCase(Locale.ROOT);
        boolean htmlFile=lower.endsWith(".html")||lower.endsWith(".htm");
        // .plugin files are handled as documents; only decoded text is editable.
        boolean pluginEditable=FlexyEditorFileTypes.canEditPlugin(filename(),text!=null);
        FlexyEditorToolsSheet sheet=new FlexyEditorToolsSheet(this,filename(),text!=null || pluginEditable,entry!=null,htmlFile,this::command);
        showDialog(sheet,d->{int selected=sheet.consumePendingAction();if(selected>=0&&getParentActivity()!=null)command(selected);});
    }
    /** Confirmed direct-to-origin-dialog native send; never silently choose a new chat. */
    private void confirmChatSend(){
        if(directCopy==null||dialog==0||getParentActivity()==null){FlexyFiles.error(this);return;}
        if(!FlexyFilesDirectSend.topicSupported(account,dialog)){
            showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle("FlexyFiles")
                .setMessage(getString(R.string.FlexyFilesTopicUnavailable)).setPositiveButton(getString(R.string.OK),null).create());return;
        }
        final FlexyFilesDirectSend.Copy copy=directCopy;
        String destination=DialogObject.getShortName(account,dialog);
        if(destination.isEmpty()){FlexyFiles.error(this);return;}
        showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider())
            .setTitle(getString(R.string.FlexyFilesSendCopyTitle))
            .setMessage(copy.name+"\n"+destination+"\n\n"+getString(R.string.FlexyFilesSendCopyMessage))
            .setPositiveButton(getString(R.string.FlexyFilesSendCopyConfirm),(d,w)->{
                try {
                    FlexyFilesDirectSend.enqueueCopy(this,copy,dialog,account,()->{
                        if(status!=null)status.setText(getString(R.string.FlexyFilesSendQueued));
                        finishFragment();
                    });
                } catch(Exception failure) {
                    if(status!=null)status.setText(getString(R.string.FlexyFilesError));
                }
            }).setNegativeButton(getString(R.string.Cancel),null).create());
    }
    private void command(int id){if(!ready||getParentActivity()==null)return;
        if(id==1||id==2){if(text==null)return;EditHistory.Change change=id==1?history.undo():history.redo();if(change!=null){internal=true;String old=id==1?change.after:change.before,next=id==1?change.before:change.after;editor.getText().replace(change.start,change.start+old.length(),next);editor.setSelection(Math.min(editor.length(),change.start+next.length()));internal=false;dirty=true;revision++;highlightParagraph();}return;}
        if(id==3||id==4||id==5||id==9||id==13){if(id==9&&(entry==null||text==null)){status.setText(getString(R.string.FlexyFilesZipOnly));return;}export(id);return;}
        if(id==6){draft(false);return;}if(text==null)return;
        if(id==7){validate();return;}if(id==8){previewHtml();return;}if(id==10||id==11){search(id==11);return;}
        if(id==12){int pos=Math.max(0,editor.getSelectionStart());editor.getText().insert(pos,"    ");}
    }
    private void replaceText(String next){if(next.length()>SelectedDocument.MAX_TEXT){status.setText(getString(R.string.FlexyFilesError));return;}editor.setText(next);editor.setSelection(Math.min(next.length(),Math.max(0,editor.getSelectionStart())));}
    private void search(boolean replace){LinearLayout form=new LinearLayout(getParentActivity());form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(20),0,dp(20),0);EditText find=new EditText(getParentActivity());find.setFocusableInTouchMode(true);find.setSingleLine(true);find.setHint(getString(R.string.Search));form.addView(find);EditText replacement=new EditText(getParentActivity());replacement.setSingleLine(true);replacement.setHint(getString(R.string.FlexyFilesReplace));if(replace)form.addView(replacement);
        AlertDialog findDialog=new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(getString(replace?R.string.FlexyFilesReplace:R.string.Search)).setView(form).setPositiveButton(getString(R.string.OK),(d,w)->{String needle=find.getText().toString();if(needle.isEmpty())return;String snapshot=editor.getText().toString(),to=replacement.getText().toString();int rev=revision,start=Math.max(0,editor.getSelectionEnd());job(()->{if(replace){int occurrences=0,p=0;while((p=snapshot.indexOf(needle,p))>=0){if(++occurrences>2048)throw new IOException();p+=needle.length();}if((long)snapshot.length()+(long)occurrences*(to.length()-needle.length())>SelectedDocument.MAX_TEXT)throw new IOException();return snapshot.replace(needle,to);}int at=snapshot.indexOf(needle,start);return at<0?snapshot.indexOf(needle):at;},(owner,value)->{if(owner.revision!=rev)return;if(replace)owner.replaceText((String)value);else{int at=(Integer)value;if(at>=0){owner.editor.requestFocus();owner.editor.setSelection(at,at+needle.length());}}});}).setNegativeButton(getString(R.string.Cancel),null).setCheckFocusable(true).create();
        findDialog.setOnDismissListener(d->{if(editor!=null)editor.requestFocus();});
        if(showDialog(findDialog,d->{if(editor!=null)editor.requestFocus();})!=null){find.post(()->{if(findDialog.isShowing()){find.requestFocus();AndroidUtilities.showKeyboard(find);}});}
    }
    private void validate(){String data=editor.getText().toString();int rev=revision;job(()->{if(data.length()>SelectedDocument.MAX_TEXT)throw new IOException();String trim=data.trim();if(trim.startsWith("{")||trim.startsWith("[")){int depth=0;boolean string=false,escape=false;for(int i=0;i<data.length();i++){char c=data.charAt(i);if(string){if(escape)escape=false;else if(c=='\\')escape=true;else if(c=='"')string=false;}else if(c=='"')string=true;else if(c=='{'||c=='['){if(++depth>64)throw new IOException();}else if(c=='}'||c==']')depth--;}
            org.json.JSONTokener tokener=new org.json.JSONTokener(data);Object json=tokener.nextValue();if(tokener.nextClean()!=0)throw new IOException();String formatted=json instanceof org.json.JSONObject?((org.json.JSONObject)json).toString(2):((org.json.JSONArray)json).toString(2);if(formatted.length()>SelectedDocument.MAX_TEXT)throw new IOException();return formatted;}
            if(trim.startsWith("<")){if(data.toUpperCase(Locale.ROOT).contains("<!DOCTYPE")||data.toUpperCase(Locale.ROOT).contains("<!ENTITY"))throw new IOException();org.xmlpull.v1.XmlPullParser parser=android.util.Xml.newPullParser();parser.setInput(new StringReader(data));int depth=0;for(int type=parser.getEventType();type!=org.xmlpull.v1.XmlPullParser.END_DOCUMENT;type=parser.next()){if(type==org.xmlpull.v1.XmlPullParser.START_TAG&&++depth>64)throw new IOException();if(type==org.xmlpull.v1.XmlPullParser.END_TAG)depth--;}return null;}throw new IOException();},(owner,value)->{if(owner.revision!=rev)return;if(value!=null)owner.replaceText((String)value);owner.status.setText(getString(R.string.FlexyFilesValid));});}
    private void previewHtml(){if(!(filename().toLowerCase(Locale.ROOT).endsWith(".html")||filename().toLowerCase(Locale.ROOT).endsWith(".htm"))){status.setText(getString(R.string.FlexyFilesHtmlOnly));return;}html=new WebView(getParentActivity());WebSettings settings=html.getSettings();settings.setJavaScriptEnabled(false);settings.setAllowFileAccess(false);settings.setAllowContentAccess(false);settings.setBlockNetworkLoads(true);settings.setDomStorageEnabled(false);settings.setGeolocationEnabled(false);settings.setCacheMode(WebSettings.LOAD_NO_CACHE);html.setWebViewClient(new WebViewClient(){@Override public boolean shouldOverrideUrlLoading(WebView view,WebResourceRequest request){return true;}@Override public WebResourceResponse shouldInterceptRequest(WebView view,WebResourceRequest request){return new WebResourceResponse("text/plain","UTF-8",new ByteArrayInputStream(new byte[0]));}});html.loadDataWithBaseURL(null,editor.getText().toString(),"text/html","UTF-8",null);
        org.telegram.ui.ActionBar.AlertDialog dialog=new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(getString(R.string.FlexyFilesHtml)).setView(html).setPositiveButton(getString(R.string.Close),null).create();dialog.setOnDismissListener(d->destroyHtml());showDialog(dialog);}
    private void destroyHtml(){if(html!=null){html.stopLoading();html.loadUrl("about:blank");html.destroy();html=null;}}
    private void export(int action){String value=text==null?null:editor.getText().toString(),name=filename();byte[] raw=binary;SelectedDocument.Text original=text;SelectedDocument reader=document;ready=false;
        job(()->{byte[] bytes=original==null?raw:original.encode(value);boolean revisedZip=action==9||(action==13&&entry!=null);File result=FilesCache.output(revisedZip?"edited-"+originalName:"edited-"+name);boolean complete=false;try(OutputStream out=new FileOutputStream(result)){if(revisedZip)reader.writeZipCopy(out,entry,bytes);else out.write(bytes);complete=true;}finally{if(!complete)result.delete();}if(action==13)directCopy=FlexyFilesDirectSend.prepare(result);return result;},(owner,result)->{owner.ready=true;owner.output=(File)result;if(action==3||action==9){Intent intent=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE).setType(action==9?"application/zip":"application/octet-stream").putExtra(Intent.EXTRA_TITLE,owner.output.getName());owner.startActivityForResult(intent,SAVE);}else if(action==13)owner.confirmChatSend();else owner.share(action==5);});}
    private void share(boolean currentChat){try{Uri uri=FileProvider.getUriForFile(getParentActivity(),ApplicationLoader.applicationContext.getPackageName()+".provider",output);Intent intent=new Intent(Intent.ACTION_SEND).setType("application/octet-stream").putExtra(Intent.EXTRA_STREAM,uri).addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);intent.setClipData(ClipData.newRawUri("FlexyFiles",uri));if(currentChat){intent.setClass(getParentActivity(),org.telegram.ui.LaunchActivity.class);intent.putExtra("currentAccount",account);if(SharedConfig.directShare&&SharedConfig.directShareHash!=null){intent.putExtra("dialogId",dialog);intent.putExtra("hash",SharedConfig.directShareHash);}intent.addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP|Intent.FLAG_ACTIVITY_SINGLE_TOP);}startActivityForResult(currentChat?intent:Intent.createChooser(intent,getString(R.string.FlexyFilesShare)),0x464d);}catch(Exception unavailable){FlexyFiles.error(this);}}
    @Override public void onActivityResultFragment(int request,int result,Intent data){super.onActivityResultFragment(request,result,data);if(request!=SAVE||result!=Activity.RESULT_OK||data==null||data.getData()==null||output==null)return;Uri uri=data.getData();if(!"content".equals(uri.getScheme()))return;File generated=output;Context app=ApplicationLoader.applicationContext;ready=false;
        job(()->{try(InputStream in=new FileInputStream(generated);OutputStream out=app.getContentResolver().openOutputStream(uri,"w")){if(out==null)throw new IOException();byte[] buffer=new byte[8192];int count;while((count=in.read(buffer))!=-1){if(Thread.currentThread().isInterrupted())throw new InterruptedIOException();out.write(buffer,0,count);}out.flush();}return null;},(owner,value)->{owner.ready=true;owner.status.setText(getString(R.string.FlexyFilesSaved));});}
    private void draft(boolean leave){if(text==null)return;String value=editor.getText().toString();File selected=source;String path=entry;int rev=revision;byte[] bytes=value.getBytes(StandardCharsets.UTF_8);job(()->{FilesCache.draftWrite(FilesCache.draft(selected,path),bytes);return null;},(owner,done)->{if(owner.revision==rev)owner.dirty=false;owner.status.setText(getString(R.string.FlexyFilesSaved));if(leave&&!owner.dirty){owner.scheduleExplorerReturn();owner.finishFragment();}});}
    @Override public boolean isSwipeBackEnabled(MotionEvent event){return !dirty&&ready&&super.isSwipeBackEnabled(event);}
    @Override public boolean onBackPressed(boolean invoked){if(!dirty){boolean allow=super.onBackPressed(invoked);if(allow&&invoked)scheduleExplorerReturn();return allow;}if(invoked)showDialog(new AlertDialog.Builder(getParentActivity(),getResourceProvider()).setTitle(getString(R.string.FlexyFilesUnsaved)).setPositiveButton(getString(R.string.FlexyFilesDraft),(d,w)->draft(true)).setNegativeButton(getString(R.string.FlexyFilesDiscard),(d,w)->{dirty=false;scheduleExplorerReturn();finishFragment();}).setNeutralButton(getString(R.string.Cancel),null).create());return false;}
    private void highlightParagraph(){if(text==null||editor==null)return;Editable data=editor.getText();for(ForegroundColorSpan span:activeSyntaxHighlights)data.removeSpan(span);activeSyntaxHighlights.clear();int cursor=Math.max(0,editor.getSelectionStart()),start=cursor,end=cursor;while(start>0&&data.charAt(start-1)!='\n'&&cursor-start<2048)start--;while(end<data.length()&&data.charAt(end)!='\n'&&end-cursor<2048)end++;String line=data.subSequence(start,end).toString();Matcher matcher=syntax.matcher(line);int count=0,color=color(Theme.key_windowBackgroundWhiteBlueText);while(matcher.find()&&count++<128){ForegroundColorSpan span=new ForegroundColorSpan(color);data.setSpan(span,start+matcher.start(),start+matcher.end(),android.text.Spanned.SPAN_EXCLUSIVE_EXCLUSIVE);activeSyntaxHighlights.add(span);}}
    @Override public void onFragmentDestroy(){if(!dirty)scheduleExplorerReturn();AndroidUtilities.cancelRunOnUIThread(highlight);work.close();destroyHtml();SelectedDocument previous=document;document=null;if(previous!=null)try{previous.close();}catch(IOException ignored){}activeSyntaxHighlights.clear();explorerOwner=null;explorerScroll=null;binary=null;text=null;directCopy=null;retainedText=null;history.clear();super.onFragmentDestroy();}
}
