package io.github.jose22yt.flexygram.session.android;
import android.content.Context;
import android.os.Looper;
import android.util.AtomicFile;
import java.io.*;
import java.nio.channels.*;
import io.github.jose22yt.flexygram.session.*;
import io.github.jose22yt.flexygram.session.android.OperationJournal.*;

/** No-backup metadata only. AtomicFile does not lock: readers and CAS writers take FileLock. */
public final class AndroidJournalBackend implements Backend {
    private final File directory;
    private final SessionScope scope;
    public AndroidJournalBackend(Context context,ClosedRuntime runtime) {
        requireWorker();
        if(runtime==null||runtime.scope.variant!=SessionScope.Variant.REAL_ALPHA||context==null
                ||!runtime.scope.variant.applicationId.equals(context.getPackageName()))throw new IllegalArgumentException("JOURNAL_CONTEXT_MISMATCH");
        scope=runtime.scope;
        try{
            File parent=context.getNoBackupFilesDir();if(parent==null)throw new IOException();
            directory=new File(parent,"flexygram-local-auth-operations-v1");
            if((!directory.isDirectory()&&!directory.mkdir())||!directory.getCanonicalFile().equals(directory.getAbsoluteFile()))throw new IOException();
        }catch(IOException|RuntimeException failure){throw unavailable();}
    }
    public static void requireWorker(){if(Looper.myLooper()==Looper.getMainLooper())throw new IllegalStateException("AUTH_STORAGE_REQUIRES_WORKER");}
    private File file(String suffix){return new File(directory,"account-"+scope.account+suffix);}
    @Override public Record read(SessionScope requested) {
        checkScope(requested);requireWorker();
        try(RandomAccessFile lockFile=new RandomAccessFile(file(".lock"),"rw");FileLock lock=lockFile.getChannel().tryLock()){
            if(lock==null)throw new IOException();return readLocked();
        }catch(IOException|RuntimeException failure){throw unavailable();}
    }
    private Record readLocked()throws IOException {
        AtomicFile atomic=new AtomicFile(file(".metadata"));
        try(DataInputStream input=new DataInputStream(atomic.openRead())){
            if(input.available()>512||input.readInt()!=1)throw new IOException();
            String variant=input.readUTF(),appId=input.readUTF();int account=input.readInt();long revision=input.readLong();
            String operation=input.readUTF(),phase=input.readUTF();if(input.read()!=-1)throw new IOException();
            Record r=new Record(SessionScope.of(variant,appId,account),revision,operation,Phase.valueOf(phase));
            if(!scope.equals(r.scope))throw new IOException();return r;
        }catch(FileNotFoundException missing){
            if(file(".metadata").exists()||file(".metadata.bak").exists()||file(".metadata.new").exists())throw missing;
            return Record.empty(scope);
        }
    }
    @Override public boolean compareAndSet(Record expected,Record next) {
        requireWorker();if(expected==null||next==null)throw new IllegalArgumentException("JOURNAL_RECORDS_REQUIRED");
        checkScope(expected.scope);checkScope(next.scope);
        if(expected.revision==Long.MAX_VALUE||next.revision!=expected.revision+1)throw new IllegalArgumentException("JOURNAL_REVISION_MISMATCH");
        try(RandomAccessFile lockFile=new RandomAccessFile(file(".lock"),"rw");FileLock lock=lockFile.getChannel().tryLock()){
            if(lock==null)throw new IOException();if(!readLocked().equals(expected))return false;
            AtomicFile atomic=new AtomicFile(file(".metadata"));FileOutputStream stream=null;
            try{
                stream=atomic.startWrite();DataOutputStream output=new DataOutputStream(stream);
                output.writeInt(1);output.writeUTF(scope.variant.name);output.writeUTF(scope.variant.applicationId);
                output.writeInt(scope.account);output.writeLong(next.revision);output.writeUTF(next.operation);output.writeUTF(next.phase.name());
                output.flush();stream.getFD().sync();atomic.finishWrite(stream);stream=null;
                if(!readLocked().equals(next))throw new IOException();return true;
            }catch(IOException|RuntimeException failure){if(stream!=null)atomic.failWrite(stream);throw failure;}
        }catch(IOException|RuntimeException failure){throw unavailable();}
    }
    private void checkScope(SessionScope requested){if(!scope.equals(requested))throw new IllegalArgumentException("JOURNAL_ACCOUNT_MISMATCH");}
    private static IllegalStateException unavailable(){return new IllegalStateException("PRIVATE_JOURNAL_UNAVAILABLE");}
}
