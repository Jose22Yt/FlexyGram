package app.flexygram.icons;

import android.graphics.Path;

/** Project-drawn companions for symbols absent from Cupertino Icons 1.0.8.
 * Shared paths are immutable after construction; each drawable retains its own paint. */
public final class CupertinoSupplement {
    private static final Path crown = crown(false), crownOff = crown(true);
    private static final Path baseball = baseball(), fingerprint = fingerprint();
    private CupertinoSupplement() {}
    public static Path path(int code) {
        switch(code){case 0xe001:return baseball;case 0xe002:return crown;
            case 0xe003:return fingerprint;case 0xe004:return crownOff;default:return null;}
    }
    private static Path crown(boolean off){
        Path p=new Path();p.moveTo(4,17);p.lineTo(2.5f,6);p.lineTo(8,10);p.lineTo(12,3);
        p.lineTo(16,10);p.lineTo(21.5f,6);p.lineTo(20,17);p.close();p.moveTo(5,21);p.lineTo(19,21);
        if(off){p.moveTo(2,2);p.lineTo(22,22);}return p;
    }
    private static Path baseball(){
        Path p=new Path();p.addCircle(12,12,9,Path.Direction.CW);
        p.moveTo(6,5);p.cubicTo(12,8,12,16,6,19);p.moveTo(18,5);p.cubicTo(12,8,12,16,18,19);
        p.moveTo(7,8);p.lineTo(10,7);p.moveTo(8,12);p.lineTo(11,12);p.moveTo(7,16);p.lineTo(10,17);
        p.moveTo(14,7);p.lineTo(17,8);p.moveTo(13,12);p.lineTo(16,12);p.moveTo(14,17);p.lineTo(17,16);return p;
    }
    private static Path fingerprint(){
        Path p=new Path();p.moveTo(3,10);p.cubicTo(3,0,21,0,21,10);
        p.moveTo(5,18);p.cubicTo(7,14,5,10,7,7);p.cubicTo(10,3,18,5,18,10);p.cubicTo(18,16,19,19,21,21);
        p.moveTo(8,22);p.cubicTo(12,17,8,12,10,9);p.cubicTo(11,7,15,8,15,11);p.cubicTo(14,16,15,20,17,23);
        p.moveTo(12,11);p.cubicTo(12,16,13,20,12,23);p.moveTo(2,14);p.lineTo(3,13);return p;
    }
}
