/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;

import static org.telegram.messenger.LocaleController.getString;
import android.content.Context;
import java.io.File;
import java.util.Locale;
import org.telegram.messenger.*;
import org.telegram.ui.ActionBar.*;

/** Dormant entry point: menu construction reads one local preference and document metadata only. */
public final class FlexyFiles {
    public static final int MENU = 0x464c01;
    private FlexyFiles() {}
    public static boolean enabled() { return ApplicationLoader.applicationContext.getSharedPreferences("flexyfiles_local",Context.MODE_PRIVATE).getBoolean("enabled",false); }
    public static void enabled(boolean value) { ApplicationLoader.applicationContext.getSharedPreferences("flexyfiles_local",Context.MODE_PRIVATE).edit().putBoolean("enabled",value).apply(); }
    public static boolean supports(String name) {
        if (name==null) return false;
        int dot=name.lastIndexOf('.');if(dot<0)return false;
        switch(name.substring(dot+1).toLowerCase(Locale.ROOT)) {
            case "zip": case "txt": case "html": case "htm": case "css": case "js": case "json": case "xml": case "md": case "csv": case "log": case "yaml": case "yml": case "java": case "kt": case "py": case "png": case "jpg": case "jpeg": case "webp": return true;
            default:return false;
        }
    }
    public static boolean eligible(MessageObject message) {
        return enabled() && message!=null && message.getDocument()!=null && !message.isSending() && !message.isSendError()
            && !message.isSecret() && !message.isSecretMedia() && !message.messageOwner.noforwards
            && !message.needDrawBluredPreview() && supports(message.getDocumentName());
    }
    public static void open(BaseFragment owner,MessageObject message) {
        if(owner.getParentActivity()==null||!eligible(message))return;
        if(message.getDocument().size>app.flexygram.files.core.SelectedDocument.MAX_ARCHIVE){error(owner);return;}
        File file=FileLoader.getInstance(message.currentAccount).getPathToMessage(message.messageOwner);
        if((file==null||!file.isFile())&&message.messageOwner.attachPath!=null&&!message.messageOwner.attachPath.isEmpty())file=new File(message.messageOwner.attachPath);
        if(file==null||!file.isFile()) {
            owner.showDialog(new AlertDialog.Builder(owner.getParentActivity(),owner.getResourceProvider()).setTitle("FlexyFiles")
                .setMessage(getString(R.string.FlexyFilesDownloadInfo)).setPositiveButton(getString(R.string.FlexyFilesDownload),(d,w)->{
                    FileLoader.getInstance(message.currentAccount).loadFile(message.getDocument(),message,FileLoader.PRIORITY_NORMAL,0);
                    android.widget.Toast.makeText(owner.getParentActivity(),getString(R.string.FlexyFilesDownloadInfo),android.widget.Toast.LENGTH_LONG).show();
                }).setNegativeButton(getString(R.string.Cancel),null).create());return;
        }
        FlexyFilesSheet sheet=new FlexyFilesSheet(owner,file,message.getDocumentName(),message.getDialogId(),message.currentAccount);
        if(owner.showDialog(sheet)==null)sheet.dismiss();
    }
    public static void error(BaseFragment owner){if(owner.getParentActivity()!=null)android.widget.Toast.makeText(owner.getParentActivity(),getString(R.string.FlexyFilesError),android.widget.Toast.LENGTH_LONG).show();}
}
