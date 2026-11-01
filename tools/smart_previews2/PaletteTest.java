import app.flexygram.home.*;
public final class PaletteTest {
 static void yes(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args){
  int[] c=new int[3],other=new int[3];java.util.Random r=new java.util.Random(9127);
  int[] kinds={6,7,1,12,2,4},colors={0xff15803d,0xff7c3aed,0xff2563eb,0xffbe185d,0xffc2410c,0xff0369a1};
  for(int i=0;i<kinds.length;i++){SignatureSmartPreviewPalette.resolveColors(kinds[i],4,0xff000000,0xffffffff,c);yes(c[0]==colors[i]);}
  for(int k:new int[]{12,13,14}){SignatureSmartPreviewPalette.resolveColors(k,4,0,0,c);yes(c[0]==0xffbe185d);}
  for(int k:new int[]{1,10,11,15,26,27,28}){SignatureSmartPreviewPalette.resolveColors(k,4,0,0,c);yes(c[0]==0xff2563eb);}
  for(int n=0;n<300;n++){
   int accent=r.nextInt()|0xff000000,surface=r.nextInt()|0xff000000;
   for(int k=0;k<=32;k++){
    for(int mode:new int[]{0,2,4}){SignatureSmartPreviewPalette.resolveColors(k,mode,accent,surface,c);yes(SignatureSmartPreviewPalette.contrast(c[0],c[1])>=4.5);yes(c[0]>>>24==255);}
    SignatureSmartPreviewPalette.resolveColors(k,2,accent,surface,c);OriginalPalette.resolveColors(k,2,accent,surface,other);yes(java.util.Arrays.equals(c,other));
    SignatureSmartPreviewPalette.resolveColors(k,0,accent,surface,c);SignatureSmartPreviewPalette.resolveColors(1,0,accent,surface,other);yes(java.util.Arrays.equals(c,other));
   }
  }
  yes(SignatureSmartPreviewPalette.normalizeMode(1)==0);yes(SignatureSmartPreviewPalette.normalizeMode(2)==2);yes(SignatureSmartPreviewPalette.normalizeMode(3)==3);yes(SignatureSmartPreviewPalette.normalizeMode(4)==4);
  yes(SignatureMiniPillClassifier.documentType("archive.RAR",null)==13);
  SignatureSmartPreviewPalette.resolveColors(6,4,0,0,c);
  com.sun.management.ThreadMXBean bean=(com.sun.management.ThreadMXBean)java.lang.management.ManagementFactory.getThreadMXBean();bean.setThreadAllocatedMemoryEnabled(true);
  for(int n=0;n<300000;n++)SignatureSmartPreviewPalette.resolveColors(1+n%32,4,0,0,c);
  long id=Thread.currentThread().getId(),before=bean.getThreadAllocatedBytes(id);
  for(int n=0;n<100000;n++)SignatureSmartPreviewPalette.resolveColors(1+n%32,4,0,0,c);
  long allocated=bean.getThreadAllocatedBytes(id)-before;yes(allocated==0);
  System.out.println("PASS: category colors, 300 custom themes, contrast, exact legacy Matte, migration and 100000 cached palette resolves; HotSpot allocated bytes="+allocated+" (not ART/FPS)");
 }
}
