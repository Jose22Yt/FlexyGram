/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.bubbles.interaction;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.widget.Toast;
import java.io.*;
import java.lang.ref.WeakReference;
import java.util.concurrent.atomic.AtomicInteger;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.ApplicationLoader;
import org.telegram.messenger.LocaleController;
import org.telegram.messenger.R;
import org.telegram.messenger.Utilities;
import org.telegram.ui.ActionBar.BaseFragment;

/** User-selected SAF export only, bounded to one validated sticker; no storage permission. */
public final class BubbleStickerExport {
    public static final int REQUEST = 14833;
    private final WeakReference<BaseFragment> fragment;
    private final AtomicInteger generation=new AtomicInteger();
    private byte[] pending;
    private boolean choosing;
    public BubbleStickerExport(BaseFragment fragment){this.fragment=new WeakReference<>(fragment);}
    public void save(File file) {
        if(choosing)return;
        choosing=true;
        int ticket=generation.incrementAndGet();
        Utilities.globalQueue.postRunnable(()->{
            byte[] bytes=null;
            try (InputStream in=new FileInputStream(file); ByteArrayOutputStream out=new ByteArrayOutputStream()) {
                byte[] block=new byte[8192];int n;
                while((n=in.read(block))!=-1){if(out.size()+n>BubbleStickerSpec.MAX_BYTES)throw new IOException("Size");out.write(block,0,n);}
                byte[] value=out.toByteArray();if(!BubbleStickerSpec.isWebp(value))throw new IOException("Format");bytes=value;
            } catch(IOException|RuntimeException failure) { /* localized below; no content/path log */ }
            byte[] copy=bytes;
            AndroidUtilities.runOnUIThread(()->{
                if(ticket!=generation.get())return;
                BaseFragment host=fragment.get();
                if(host==null||host.getParentActivity()==null){cancel();return;}
                if(copy==null){choosing=false;notice(R.string.FlexyContextStickerSaveFailed);return;}
                pending=copy;
                Intent create=new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                        .setType(BubbleStickerSpec.MIME).putExtra(Intent.EXTRA_TITLE,"FlexyGram-Bubble-Sticker.webp");
                try{host.startActivityForResult(create,REQUEST);}
                catch(RuntimeException unavailable){pending=null;choosing=false;notice(R.string.FlexyContextStickerSaveFailed);}
            });
        });
    }
    public void result(int resultCode,Intent data) {
        byte[] bytes=pending;pending=null;choosing=false;
        if(resultCode!=Activity.RESULT_OK||bytes==null)return;
        Uri uri=data==null?null:data.getData();
        if(uri==null||!"content".equals(uri.getScheme())){notice(R.string.FlexyContextStickerSaveFailed);return;}
        Utilities.globalQueue.postRunnable(()->{
            boolean okay=false;
            try(OutputStream out=ApplicationLoader.applicationContext.getContentResolver().openOutputStream(uri,"w")){
                if(out==null)throw new IOException("Destination");out.write(bytes);out.flush();okay=true;
            }catch(IOException|RuntimeException failure){ /* Never log content or private paths. */ }
            boolean saved=okay;AndroidUtilities.runOnUIThread(()->notice(saved?R.string.FlexyContextStickerSaved:R.string.FlexyContextStickerSaveFailed));
        });
    }
    public void cancel(){generation.incrementAndGet();pending=null;choosing=false;}
    private void notice(int key){if(fragment.get()!=null&&fragment.get().getParentActivity()!=null)Toast.makeText(ApplicationLoader.applicationContext,LocaleController.getString(key),Toast.LENGTH_SHORT).show();}
}
