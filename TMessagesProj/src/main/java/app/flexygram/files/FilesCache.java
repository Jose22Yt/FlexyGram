/* SPDX-License-Identifier: GPL-3.0-or-later */
package app.flexygram.files;
import java.io.*;
import java.util.*;
import java.security.*;
import org.telegram.messenger.ApplicationLoader;
/** Only invoked from an active worker. Bounded private outputs; no filesystem walk outside this namespace. */
final class FilesCache {
    static File root(){return new File(ApplicationLoader.applicationContext.getCacheDir(),"flexyfiles");}
    static File output(String name)throws IOException {
        File root=root();if(!root.isDirectory()&&!root.mkdirs())throw new IOException("cache");
        File[] old=root.listFiles(File::isDirectory);if(old!=null){Arrays.sort(old,Comparator.comparingLong(File::lastModified).reversed());long total=0;for(int i=0;i<old.length;i++){File[] contents=old[i].listFiles(File::isFile);if(contents!=null)for(File f:contents)total+=f.length();if(i>=7||total>128L*1024*1024||System.currentTimeMillis()-old[i].lastModified()>86400000L){if(contents!=null)for(File f:contents)f.delete();old[i].delete();}}}
        String safe=name.replaceAll("[^\\p{L}\\p{N}._ -]","_");if(safe.length()>100)safe=safe.substring(safe.length()-100);
        File dir=new File(root,UUID.randomUUID().toString());if(!dir.mkdir())throw new IOException("cache");return new File(dir,safe.isEmpty()?"edited.txt":safe);
    }
    static File draft(File file,String entry)throws Exception {
        File root=new File(ApplicationLoader.applicationContext.getFilesDir(),"flexyfiles-drafts");if(!root.isDirectory()&&!root.mkdirs())throw new IOException("draft");
        byte[] digest=MessageDigest.getInstance("SHA-256").digest((file.getCanonicalPath()+"\n"+file.length()+"\n"+file.lastModified()+"\n"+entry).getBytes(java.nio.charset.StandardCharsets.UTF_8));StringBuilder key=new StringBuilder();for(byte b:digest)key.append(String.format(Locale.ROOT,"%02x",b&255));
        return new File(root,key+".draft");
    }
    static void draftWrite(File target,byte[] data)throws IOException {
        if(data.length>app.flexygram.files.core.SelectedDocument.MAX_TEXT)throw new IOException("limit");
        File[] files=target.getParentFile().listFiles();if(files!=null){Arrays.sort(files,Comparator.comparingLong(File::lastModified).reversed());for(int i=3;i<files.length;i++)if(!files[i].equals(target))files[i].delete();}
        File tmp=new File(target+".tmp");try(FileOutputStream out=new FileOutputStream(tmp)){out.write(data);out.getFD().sync();}catch(IOException e){tmp.delete();throw e;}
        if(!tmp.renameTo(target)){tmp.delete();throw new IOException("rename");}
    }
}
