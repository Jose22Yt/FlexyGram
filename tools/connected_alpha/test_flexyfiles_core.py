"""Execute the real read-only selected-document engine on hostile local fixtures, not Telegram data."""
import hashlib
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'TMessagesProj/src/main/java/app/flexygram/files/core/SelectedDocument.java'


class FlexyFilesCore(unittest.TestCase):
    def test_actual_archive_limits_cancellation_copy_and_encoding_roundtrips(self):
        runner = r'''import app.flexygram.files.core.SelectedDocument;import java.io.*;import java.nio.file.*;import java.nio.charset.*;import java.util.*;
public class FilesProbe {
 interface Work {void run()throws Exception;}
 static int checks;
 static void yes(boolean b){if(!b)throw new AssertionError();checks++;}
 static void reject(Work w)throws Exception{try{w.run();throw new AssertionError("accepted hostile input");}catch(IOException expected){checks++;}}
 public static void main(String[]args)throws Exception{
  File root=new File(args[0]);
  for(String bad:new String[]{"../x","/x","a/../b","a//b","a/./b","C:/x","a\\b","\0","a/../../x"})reject(()->SelectedDocument.safePath(bad));
  yes(SelectedDocument.safePath("folder/こんにちは.txt").equals("folder/こんにちは.txt"));
  reject(()->SelectedDocument.safePath("a/".repeat(17)+"file"));
  for(String charset:new String[]{"UTF-8","UTF-16LE","UTF-16BE"}){
   byte[] content="α\r\nβ\nγ\r".getBytes(Charset.forName(charset));
   byte[] bom=charset.equals("UTF-8")?new byte[]{(byte)239,(byte)187,(byte)191}:charset.equals("UTF-16LE")?new byte[]{(byte)255,(byte)254}:new byte[]{(byte)254,(byte)255};
   byte[] bytes=new byte[bom.length+content.length];System.arraycopy(bom,0,bytes,0,bom.length);System.arraycopy(content,0,bytes,bom.length,content.length);
   var text=SelectedDocument.text(bytes);yes(text.newline.equals("MIXED"));yes(Arrays.equals(bytes,text.encode(text.value)));yes(text.value.contains("β"));
  }
  reject(()->SelectedDocument.text(new byte[]{(byte)255,(byte)255}));
  reject(()->SelectedDocument.text(new byte[]{0,1,2}));
  reject(()->SelectedDocument.text(new byte[SelectedDocument.MAX_TEXT+1]));
  try(var plain=new SelectedDocument(new File(root,"plain.txt"))){yes(!plain.isArchive());yes(SelectedDocument.text(plain.read(null,100)).value.equals("hello\r\nworld"));reject(()->plain.read("other.txt",100));reject(()->plain.read(null,2));}
  SelectedDocument closed=new SelectedDocument(new File(root,"plain.txt"));closed.close();closed.close();reject(()->closed.read(null,100));
  for(String name:new String[]{"bad.zip","traversal.zip","deep.zip","duplicate.zip","bomb.zip","index.zip","count.zip"})reject(()->{try(var bad=new SelectedDocument(new File(root,name))) {}});
  try(var crc=new SelectedDocument(new File(root,"crc.zip"))){reject(()->crc.read("crc.txt",100));}
  byte[] original=Files.readAllBytes(new File(root,"normal.zip").toPath());
  try(var zip=new SelectedDocument(new File(root,"normal.zip"))){
   yes(zip.isArchive());yes(zip.entries().size()==4);yes(new String(zip.read("dir/hello.json",100),StandardCharsets.UTF_8).equals("{\"before\":1}"));
   reject(()->zip.read("dir",100));reject(()->zip.read("unknown",100));reject(()->zip.read("dir/hello.json",2));
   try(OutputStream out=new FileOutputStream(new File(root,"edited.zip"))){zip.writeZipCopy(out,"dir/hello.json","{\"after\":2}".getBytes(StandardCharsets.UTF_8));}
   Thread.currentThread().interrupt();try{reject(()->zip.read("dir/hello.json",100));}finally{Thread.interrupted();}
  }
  yes(Arrays.equals(original,Files.readAllBytes(new File(root,"normal.zip").toPath())));
  try(var edited=new SelectedDocument(new File(root,"edited.zip"))){yes(edited.entries().size()==4);yes(new String(edited.read("dir/hello.json",100),StandardCharsets.UTF_8).equals("{\"after\":2}"));yes(Arrays.equals(edited.read("image.bin",100),new byte[]{1,2,3,4}));}
  Thread.currentThread().interrupt();try{reject(()->{try(var ignored=new SelectedDocument(new File(root,"normal.zip"))) {}});}finally{Thread.interrupted();}
  System.out.println("PASS real selected-document engine checks="+checks+"; Android/UI/device NOT_TESTED");
 }
}'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'plain.txt').write_bytes(b'hello\r\nworld')
            (root / 'bad.zip').write_bytes(b'PK\x03\x04not-an-archive')
            fixtures = {
                'normal.zip': [('dir/', b''), ('dir/hello.json', b'{"before":1}'), ('dir/empty', b''), ('image.bin', bytes([1, 2, 3, 4]))],
                'traversal.zip': [('../outside.txt', b'never extract')],
                'deep.zip': [('a/' * 17 + 'file', b'x')],
                'duplicate.zip': [('a/', b''), ('a', b'x')],
                'bomb.zip': [('zeros', b'0' * 1024 * 1024)],
                'crc.zip': [('crc.txt', b'original')],
            }
            for name, entries in fixtures.items():
                with zipfile.ZipFile(root / name, 'w', compression=zipfile.ZIP_DEFLATED if name == 'bomb.zip' else zipfile.ZIP_STORED) as archive:
                    for path, data in entries:
                        archive.writestr(path, data)
            data = bytearray((root / 'normal.zip').read_bytes())
            eocd = data.rfind(b'PK\x05\x06')
            struct.pack_into('<I', data, eocd + 12, 4 * 1024 * 1024 + 1)
            (root / 'index.zip').write_bytes(data)
            data = bytearray((root / 'normal.zip').read_bytes())
            struct.pack_into('<HH', data, eocd + 8, 65000, 65000)
            (root / 'count.zip').write_bytes(data)
            data = bytearray((root / 'crc.zip').read_bytes())
            data[30 + len('crc.txt')] ^= 1
            (root / 'crc.zip').write_bytes(data)
            original_hash = hashlib.sha256((root / 'normal.zip').read_bytes()).hexdigest()
            java = root / 'FilesProbe.java'
            java.write_text(runner)
            subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', directory, str(SOURCE), str(java)], check=True, capture_output=True)
            result = subprocess.run(['java', '-Xmx256m', '-cp', directory, 'FilesProbe', directory], check=True, capture_output=True, text=True)
            self.assertIn('PASS real selected-document engine', result.stdout)
            self.assertEqual(hashlib.sha256((root / 'normal.zip').read_bytes()).hexdigest(), original_hash)
            self.assertFalse((root.parent / 'outside.txt').exists())
