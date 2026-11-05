"""Execute the real load lambdas; decoding completes before the UI callback."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_editor_load_decodes_text_in_worker_preserving_binary_and_encoding(tmp_path):
    source=(JAVA/'app/flexygram/files/FlexyFileEditorActivity.java').read_text()
    content=source[source.index('    private static final class LoadedContent'):source.index('    private void load()')]
    load=method(source,'private void load()')
    probe(tmp_path,{'Probe.java':'''import java.io.*;import java.nio.charset.*;import app.flexygram.files.core.SelectedDocument;
public class Probe {
 CONTENT
 static class View {static int GONE=8;}
 static class Editor {String text;boolean enabled;int visibility;void setText(String s){text=s;}void setEnabled(boolean b){enabled=b;}void setVisibility(int v){visibility=v;}}
 static class Status {String text;void setText(String s){text=s;}}
 static class AndroidUtilities {static String formatFileSize(int n){return ""+n;}}
 static class R {static class string{static int FlexyFilesBinary;}}
 static String getString(int id){return "Binary";}
 File source;String entry;SelectedDocument document;byte[] binary;SelectedDocument.Text text;
 boolean ready,internal,highlight,draft,image;Editor editor=new Editor();Status status=new Status();
 String filename(){return "test";}void highlightParagraph(){highlight=true;}void recoverDraft(){draft=true;}void image(){image=true;}
 interface Job {Object run()throws Exception;}interface Result {void ready(Probe owner,Object value);}
 void job(Job job,Result result){try{java.util.concurrent.atomic.AtomicReference<Object> done=new java.util.concurrent.atomic.AtomicReference<>();
 java.util.concurrent.atomic.AtomicReference<Throwable> error=new java.util.concurrent.atomic.AtomicReference<>();
 Thread worker=new Thread(()->{try{done.set(job.run());}catch(Throwable e){error.set(e);}});worker.start();worker.join();
 if(error.get()!=null)throw new AssertionError(error.get());
 LoadedContent loaded=(LoadedContent)done.get();check(!ready&&loaded.bytes!=null);
 if(loaded.text!=null)check(!loaded.text.value.isEmpty());result.ready(this,loaded);
 }catch(Exception e){throw new AssertionError(e);}}
 LOAD
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args)throws Exception {
 String value="Hola á\\r\\nSegunda línea";
 byte[][] cases={value.getBytes(StandardCharsets.UTF_8), ("\\ufeff"+value).getBytes(StandardCharsets.UTF_16LE),new byte[]{0,1,2},new byte[]{(byte)0xff},new byte[SelectedDocument.MAX_TEXT+1]};
 for(int i=0;i<cases.length;i++){
 File file=File.createTempFile("flexy-decode-",".txt");
 try{java.nio.file.Files.write(file.toPath(),cases[i]);Probe p=new Probe();p.source=file;p.load();
 check(p.ready&&java.util.Arrays.equals(p.binary,cases[i]));
 if(i<2){check(value.equals(p.editor.text)&&p.text.newline.equals("CRLF")&&p.editor.enabled&&p.highlight&&p.draft&&!p.image);check(java.util.Arrays.equals(p.text.encode(value),cases[i]));}
 else check(p.text==null&&p.editor.visibility==View.GONE&&p.image&&!p.highlight&&!p.draft);
 p.document.close();
 }finally{file.delete();}
 }
 }
}'''.replace('CONTENT',content).replace('LOAD',load)},[JAVA/'app/flexygram/files/core/SelectedDocument.java'])
