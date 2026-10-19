"""Local descriptor model: shared position, independent ownership, short reads.
The superclass deliberately dereferences destination like AOSP before any discard.
This is not Binder/ART execution; real Android remains a beta gate.
"""
SOURCES = {
'android/annotation/SuppressLint.java': 'package android.annotation; public @interface SuppressLint {String[] value();}',
'org/telegram/messenger/DiagnosticPolicy.java': 'package org.telegram.messenger; public class DiagnosticPolicy {public static boolean isIsolated(){return true;}}',
'android/app/backup/BackupDataInput.java': 'package android.app.backup; public class BackupDataInput {}',
'android/app/backup/FullBackupDataOutput.java': 'package android.app.backup; public class FullBackupDataOutput {}',
'android/app/backup/FullRestoreDataInput.java': '''package android.app.backup; import android.os.ParcelFileDescriptor; public class FullRestoreDataInput {ParcelFileDescriptor data;long size;public FullRestoreDataInput(ParcelFileDescriptor d,long s){data=d;size=s;} public ParcelFileDescriptor getData(){return data;}public long getSize(){return size;}}''',
'android/app/backup/BackupAgentHelper.java': '''package android.app.backup; import android.os.*;import java.io.*; public class BackupAgentHelper {public static int parentCalls;public void onCreate(){} public void onRestore(BackupDataInput d,int v,ParcelFileDescriptor s){}public void onRestore(BackupDataInput d,long v,ParcelFileDescriptor s){onRestore(d,(int)v,s);} public void onFullBackup(FullBackupDataOutput d){} public void onRestoreFile(FullRestoreDataInput input)throws IOException{throw new AssertionError("New framework writer reached");} public void onRestoreFile(ParcelFileDescriptor data,long size,File destination,int type,long mode,long mtime)throws IOException {destination.getCanonicalPath();parentCalls++;throw new AssertionError("Framework file writer reached");}}''',
'android/os/ParcelFileDescriptor.java': r'''package android.os;
import java.io.*;import java.util.*;
public class ParcelFileDescriptor implements Closeable {
static final Map<FileDescriptor,ParcelFileDescriptor> owners=new IdentityHashMap<>();
public static int duplicates,duplicateCloses; public boolean closed;public final State state;final FileDescriptor fd=new FileDescriptor(); final boolean copy;
public static class State {public byte[] bytes;public int position,readLimit=3;public boolean failRead,zeroRead;State(byte[] b){bytes=b;}}
public ParcelFileDescriptor(byte[] bytes){this(new State(bytes),false);}
private ParcelFileDescriptor(State s,boolean duplicate){state=s;copy=duplicate;owners.put(fd,this);}
public FileDescriptor getFileDescriptor()throws IOException{if(closed)throw new IOException("closed original");return fd;}
public static ParcelFileDescriptor dup(FileDescriptor fd)throws IOException{ParcelFileDescriptor owner=owners.get(fd);if(owner==null||owner.closed)throw new IOException("invalid descriptor");duplicates++;return new ParcelFileDescriptor(owner.state,true);}
public void close(){if(!closed&&copy)duplicateCloses++;closed=true;}
public static class AutoCloseInputStream extends InputStream {
final ParcelFileDescriptor owner;public AutoCloseInputStream(ParcelFileDescriptor p){owner=p;}
public int read()throws IOException{byte[] b=new byte[1];int n=read(b,0,1);return n<0?-1:b[0]&255;}
public int read(byte[] b,int offset,int length)throws IOException{if(owner.closed)throw new IOException("closed duplicate");State s=owner.state;if(s.failRead)throw new IOException("synthetic I/O failure");if(s.zeroRead)return 0;if(s.position==s.bytes.length)return -1;int n=Math.min(length,Math.min(s.readLimit,s.bytes.length-s.position));System.arraycopy(s.bytes,s.position,b,offset,n);s.position+=n;return n;}
public void close(){owner.close();}
}
}
''',
'Main.java': r'''import java.io.*;import java.nio.file.*;import java.util.*;import org.telegram.messenger.*;import android.app.backup.*;import android.os.*;
public class Main {
static void ok(boolean b){if(!b)throw new AssertionError();}
static ParcelFileDescriptor data(String s){return new ParcelFileDescriptor(s.getBytes(java.nio.charset.StandardCharsets.UTF_8));}
interface Attempt{void run()throws Exception;}
static void rejected(Attempt action,Class<?> kind)throws Exception{try{action.run();throw new AssertionError("must reject malformed entity");}catch(IOException e){ok(kind.isInstance(e));}}
public static void main(String[] args)throws Exception{
BackupAgent agent=new BackupAgent();Path root=Path.of(args[0]);Files.createDirectories(root);
Path tokenFile=root.resolve("saved_tokens.xml"),sessionFile=root.resolve("tgnet.dat");
Files.writeString(tokenFile,"SYNTHETIC_TOKEN_UNCHANGED");Files.writeString(sessionFile,"SYNTHETIC_AUTH_KEY_UNCHANGED");
Map<String,String> prefs=new HashMap<>();prefs.put("saved_tokens","SYNTHETIC_TOKEN_UNCHANGED");prefs.put("fontSize","18");Map<String,String> before=new HashMap<>(prefs);
byte[] tokensBefore=Files.readAllBytes(tokenFile),sessionBefore=Files.readAllBytes(sessionFile);
// Exact entity boundary and following entity; the framework descriptor stays usable.
ParcelFileDescriptor p=data("FIRSTNEXT");agent.onRestoreFile(p,5,tokenFile.toFile(),1,0600,99);ok(p.state.position==5&&!p.closed);p.getFileDescriptor();
agent.onRestoreFile(p,4,sessionFile.toFile(),1,0600,99);ok(p.state.position==9&&!p.closed);
// Multi-buffer payload and legal partial reads; destination is ignored, including null.
byte[] large=new byte[20005];Arrays.fill(large,(byte)7);ParcelFileDescriptor big=new ParcelFileDescriptor(large);big.state.readLimit=1024;
agent.onRestoreFile(big,20000,null,1,0,0);ok(big.state.position==20000&&!big.closed);
// Directories/empty files have no payload and never duplicate/read/close the original.
int copies=ParcelFileDescriptor.duplicates;ParcelFileDescriptor empty=data("NEXT");Path directory=root.resolve("must-not-create");
agent.onRestoreFile(empty,0,directory.toFile(),2,0,0);agent.onRestoreFile(empty,0,tokenFile.toFile(),1,0,0);ok(empty.state.position==0&&!empty.closed&&ParcelFileDescriptor.duplicates==copies&&!Files.exists(directory));
// API 36.1+ callback uses its own discard path, not a presumed parent adapter.
ParcelFileDescriptor modern=data("MODERNTAIL");agent.onRestoreFile(new FullRestoreDataInput(modern,6));ok(modern.state.position==6&&!modern.closed);
// Malformed size/missing data: fail before touching descriptors.
rejected(()->agent.onRestoreFile(empty,-1,null,1,0,0),IOException.class);ok(empty.state.position==0);
rejected(()->agent.onRestoreFile(null,1,null,1,0,0),IOException.class);rejected(()->agent.onRestoreFile((FullRestoreDataInput)null),IOException.class);
// Truncation/read errors close only our duplicate and never write credentials.
ParcelFileDescriptor shortData=data("abc");rejected(()->agent.onRestoreFile(shortData,10,null,1,0,0),EOFException.class);ok(shortData.state.position==3&&!shortData.closed);
ParcelFileDescriptor broken=data("abc");broken.state.failRead=true;rejected(()->agent.onRestoreFile(broken,2,null,1,0,0),IOException.class);ok(broken.state.position==0&&!broken.closed);
ParcelFileDescriptor stalled=data("abc");stalled.state.zeroRead=true;rejected(()->agent.onRestoreFile(stalled,2,null,1,0,0),IOException.class);ok(!stalled.closed);
// int and inherited long key/value callbacks plus full backup have no side effects.
agent.onCreate();agent.onRestore(null,1,null);agent.onRestore(null,4294967297L,null);agent.onFullBackup(null);agent.requestBackup();
ok(prefs.equals(before));ok(Arrays.equals(tokensBefore,Files.readAllBytes(tokenFile)));ok(Arrays.equals(sessionBefore,Files.readAllBytes(sessionFile)));
try(java.util.stream.Stream<Path> files=Files.list(root)){ok(files.count()==2);}
ok(BackupAgentHelper.parentCalls==0);ok(ParcelFileDescriptor.duplicates==ParcelFileDescriptor.duplicateCloses);
System.out.println("PASS: bounded entity discard; next entity retained; original descriptors open; duplicates closed; synthetic files/preferences/tokens unchanged; legacy and 36.1+ callbacks");
}
}'''
}
