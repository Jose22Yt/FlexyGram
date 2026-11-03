"""Check production color output against independent WCAG math and dark photo backdrops."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def luminance(color):
    def linear(c):
        v = c / 255
        return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4
    return sum(weight * linear((color >> shift) & 255)
               for weight, shift in [(0.2126, 16), (0.7152, 8), (0.0722, 0)])


def contrast(a, b):
    a, b = luminance(a), luminance(b)
    return (max(a, b) + .05) / (min(a, b) + .05)


def composite(front, back):
    alpha = front >> 24
    return 0xff000000 | sum(round((((front >> shift) & 255) * alpha
                                 + ((back >> shift) & 255) * (255-alpha)) / 255) << shift
                            for shift in [16, 8, 0])


def test_light_glass_keeps_45_contrast_over_dark_and_colored_images(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    probe = tmp_path / 'ContrastProbe.java'
    probe.write_text('''import app.exteraless.appearance.GlassContrastPolicy;
public class ContrastProbe {
 public static void main(String[] args) {
  for(int base:new int[]{0xffffffff,0xfffafafc,0xffddeeff,0xffccffaa,0xff222222,0xff808080})
   for(int opacity:new int[]{51,107,133,184,217})
    for(int ink:new int[]{0xff808080,0xff2a8cca,0xffffffff,0xff000000,0x99808080,0xff369940}) {
     int surface=GlassContrastPolicy.lightSurface(base,opacity);
     int adjusted=GlassContrastPolicy.readableInk(ink,surface);
     System.out.println(Integer.toUnsignedString(surface)+" "+Integer.toUnsignedString(adjusted)+" "+Integer.toUnsignedString(ink));
    }
 }
}''')
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    str(JAVA / 'app/exteraless/appearance/GlassContrastPolicy.java'), str(probe)],
                   check=True, capture_output=True)
    output = subprocess.check_output(['java', '-cp', str(tmp_path), 'ContrastProbe'], text=True)
    rows = [list(map(int, line.split())) for line in output.splitlines()]
    assert len(rows) == 180
    backgrounds = [0xff000000, 0xff101820, 0xff300000, 0xff000030, 0xffffffff,
                   0xff00ff00, 0xffff0000, 0xff0000ff, 0xff707070]
    for surface, ink, original in rows:
        assert 184 <= surface >> 24 < 255  # Keep a translucent backdrop, including the custom dark tint.
        assert ink >> 24 == 255
        for background in backgrounds:
            assert contrast(ink, composite(surface, background)) >= 4.5
        if all(contrast(original | 0xff000000, composite(surface, b)) >= 4.5 for b in backgrounds):
            assert ink == original | 0xff000000  # Preserve already-legible theme colors.
