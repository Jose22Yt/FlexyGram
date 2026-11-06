/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.studio;
import android.app.job.*;
import android.content.*;
import android.net.Uri;
import androidx.core.content.FileProvider;
import app.flexygram.studio.core.StudioSchema;
import java.io.*;
import java.util.*;
/** Bounded, private share cache. Only its dedicated FileProvider grants temporary read access. */
public final class FlexyStudioFiles {
    private static final long TTL=24*60*60*1000L;
    private FlexyStudioFiles(){}
    public static File share(Context context,byte[] bytes)throws IOException {
        cleanup(context,7);
        File dir=new File(context.getCacheDir(),"flexystudio/share/"+UUID.randomUUID());
        if(!dir.mkdirs())throw new IOException("cache");
        File file=new File(dir,"MiFlexyGram"+StudioSchema.EXTENSION);
        try(FileOutputStream out=new FileOutputStream(file)){out.write(bytes);}
        JobScheduler scheduler=(JobScheduler)context.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        try { if(scheduler!=null)scheduler.schedule(new JobInfo.Builder(0x465347,new ComponentName(context,FlexyStudioCleanup.class)).setMinimumLatency(TTL).setOverrideDeadline(TTL*2).build()); } catch(RuntimeException unavailable) { /* Sharing remains usable without scheduled cache expiry. */ }
        return file;
    }
    static File stage(Context context,byte[] bytes)throws IOException {
        if(bytes.length<1||bytes.length>StudioSchema.MAX_BYTES)throw new IOException("size");
        File root=new File(context.getCacheDir(),"flexystudio/pending");
        if(!root.isDirectory()&&!root.mkdirs())throw new IOException("cache");
        File[] old=root.listFiles();long now=System.currentTimeMillis();
        if(old!=null){Arrays.sort(old,Comparator.comparingLong(File::lastModified).reversed());for(int i=0;i<old.length;i++)if(i>=7||now-old[i].lastModified()>=TTL)old[i].delete();}
        File file=new File(root,UUID.randomUUID()+".pending");
        try(FileOutputStream out=new FileOutputStream(file)){out.write(bytes);}catch(IOException failed){file.delete();throw failed;}
        return file;
    }
    static File pending(Context context,String token) {
        if(token==null||!token.matches("[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\.pending"))return null;
        File file=new File(context.getCacheDir(),"flexystudio/pending/"+token);
        return file.isFile()&&file.length()>0&&file.length()<=StudioSchema.MAX_BYTES?file:null;
    }
    static void cleanup(Context context,int keep) {
        File root=new File(context.getCacheDir(),"flexystudio/share");File[] dirs=root.listFiles();if(dirs==null)return;
        Arrays.sort(dirs,Comparator.comparingLong(File::lastModified).reversed());long now=System.currentTimeMillis();
        for(int i=0;i<dirs.length;i++)if(i>=keep||now-dirs[i].lastModified()>=TTL){File[] files=dirs[i].listFiles();if(files!=null)for(File file:files)file.delete();dirs[i].delete();}
    }
    static OutputStream openForExport(ContentResolver resolver,Uri uri)throws IOException {
        try{OutputStream out=resolver.openOutputStream(uri,"wt");if(out!=null)return out;}
        catch(FileNotFoundException | IllegalArgumentException unsupportedMode){ /* Retry providers without truncate mode. */ }
        return resolver.openOutputStream(uri,"w");
    }
    public static Intent shareIntent(Context context,File file) {
        Uri uri=FileProvider.getUriForFile(context,context.getPackageName()+".flexystudio",file);
        Intent intent=new Intent(Intent.ACTION_SEND).setType(StudioSchema.MIME).putExtra(Intent.EXTRA_STREAM,uri);
        intent.setClipData(ClipData.newRawUri("FlexyStudio",uri));
        intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
        return intent;
    }
}
