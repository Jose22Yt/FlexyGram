"""Production Java palette checks for the Alpha1278 folder badge fix.

This is not a physical APK or GPU frame-time measurement.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
PRODUCTION=ROOT/"TMessagesProj/src/main/java/app/flexygram/home/SignatureFolderAccent.java"
TABS=ROOT/"TMessagesProj/src/main/java/org/telegram/ui/Components/FilterTabsView.java"


class FolderBadges1278(unittest.TestCase):
    def test_java_palette_light_dark_custom_and_transitions(self):
        source=r"""
import app.flexygram.home.SignatureFolderAccent;
public final class SignatureFolderBadgeProbe {
    private static long cases;
    static void require(boolean condition,String reason) {
        cases++;
        if(!condition)throw new AssertionError(reason);
    }
    static int blend(int a,int b,float f) {
        int color=0;
        for(int shift=0;shift<=24;shift+=8)
            color |= Math.round(((a>>>shift)&255)+(((b>>>shift)&255)-((a>>>shift)&255))*f)<<shift;
        return color;
    }
    public static void main(String[] args) {
        for(boolean dark:new boolean[]{false,true}) {
            int surface=dark?0xff32353b:0xfff1f2f5;
            int neutral=dark?0xffe7e9ed:0xff454c56;
            int preferred=dark?0xffffffff:0xff000000;
            int[] accents={
                0xff60a9f8,0xff17a66a,0xff531e80,0xfff6d63d,
                0xff111111,0xffeeeeee,0xffee5777,0xff22b3b6,
                0xff808080,0xff555555,0xfffafafa,0xff090c16,
                0x8066b5ee
            };
            for(int accent:accents) {
                SignatureFolderAccent palette=new SignatureFolderAccent();
                require(palette.update(accent,preferred,surface,neutral),"theme loaded");
                int actual=palette.color;
                require(SignatureFolderAccent.contrast(palette.ink,actual)>=4.5,
                        "selected text contrast");
                int previousBadge=0;
                for(int i=0;i<=128;i++) {
                    float f=i/128f;
                    int pill=blend(surface,actual,f);
                    int ink=palette.inkAt(f);
                    int badge=palette.badgeSurfaceAt(f);
                    int badgeText=palette.badgeInkAt(f);
                    require(SignatureFolderAccent.contrast(ink,pill)>=4.5,
                            "folder text at "+i+" accent "+Integer.toHexString(accent));
                    require(SignatureFolderAccent.contrast(badgeText,badge)>=4.5,
                            "badge contrast at "+i+" accent "+Integer.toHexString(accent));
                    require((badge>>>24)==255,"opaque badge surface");
                    if(i>0) {
                        int max=0;
                        for(int shift=0;shift<=16;shift+=8) {
                            int delta=Math.abs(((badge>>>shift)&255)-((previousBadge>>>shift)&255));
                            max=Math.max(max,delta);
                        }
                        require(max<=7,"badge background continuity");
                    }
                    previousBadge=badge;
                }
                if(accent==0xff60a9f8||accent==0xff17a66a) {
                    require(palette.badgeSurfaceAt(1f)!=0xff000000,
                            "active badge must not be black");
                    require(palette.ink!=0xff000000,
                            "active ink must not inherit pure black");
                }
                require(!palette.update(accent,preferred,surface,neutral),"cached identical palette");
            }
        }
        System.out.println("PASS "+cases+" real Java contrast/cached/transition assertions");
    }
}
"""
        with tempfile.TemporaryDirectory() as folder:
            test=Path(folder)/"SignatureFolderBadgeProbe.java"
            test.write_text(source)
            compile=subprocess.run(["javac","-d",folder,str(PRODUCTION),str(test)],
                                   text=True,capture_output=True)
            self.assertEqual(compile.returncode,0,compile.stderr)
            result=subprocess.run(["java","-cp",folder,"SignatureFolderBadgeProbe"],
                                  text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn("PASS ",result.stdout)

    def test_signature_view_only_palette_no_new_per_frame_paints(self):
        code=TABS.read_text()
        self.assertIn("signatureDefaultColors",code)
        self.assertIn("signaturePalette.badgeSurfaceAt(signatureSelected)",code)
        self.assertIn("signaturePalette.badgeInkAt(signatureSelected)",code)
        self.assertIn("textPaint.setColor(signaturePalette.inkAt(signatureSelected))",code)
        self.assertNotIn("counterPaint.setColor(app.flexygram.home.SignatureHomePainter.blend",code)
        self.assertIn("if (signatureHome)",code)
        self.assertIn("if (!signatureHome)",code)
        self.assertIn("SignatureHomeStyle.selection",code)
        self.assertIn("SignatureHomeStyle.selectedSurface",code)

    def test_scoped_review(self):
        from folder_badge1278_contract import verify_current
        verify_current()


if __name__=="__main__":
    unittest.main()
