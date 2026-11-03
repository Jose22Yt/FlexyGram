"""Exercise the live allocation-free layout math without Android rendering stubs."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def test_pair_stays_centered_adjacent_and_inside_insets(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    probe = tmp_path / 'PairProbe.java'
    probe.write_text('''import app.flexygram.navigation.LiquidNavigationMath;
import app.flexygram.composer.ComposerStyle;
public class PairProbe {
 static void check(boolean value) {if(!value)throw new AssertionError();}
 public static void main(String[] args) {
  for(int scale=1;scale<=4;scale++) for(int screen:new int[]{280,320,360,412,600,840})
   for(int count=2;count<=6;count++) for(int fraction:new int[]{55,70,85,100})
    for(boolean rtl:new boolean[]{false,true}) {
     int inset=12*scale, available=(screen-24)*scale, search=48*scale, gap=8*scale;
     int remaining=available-search-gap;
     int dock=Math.min(remaining,Math.max(48*count*scale,remaining*fraction/100));
     int start=LiquidNavigationMath.pairStart(inset,available,dock,search,gap);
     int d=rtl?start+search+gap:start;
     int s=rtl?start:start+dock+gap;
     check(Math.min(d,s)>=inset);
     check(Math.max(d+dock,s+search)<=inset+available);
     check(rtl?d-(s+search)==gap:s-(d+dock)==gap);
     int freeLeft=start-inset;
     int freeRight=inset+available-(start+dock+gap+search);
     check(Math.abs(freeLeft-freeRight)<=1);
    }
  for(int level=0;level<=2;level++) {
   check(ComposerStyle.diameter(level)==44-2*ComposerStyle.inset(level));
   check(ComposerStyle.diameter(level)<=44);
  }
 }
}''')
    files = [JAVA / 'app/flexygram/navigation/LiquidNavigationMath.java',
             JAVA / 'app/flexygram/composer/ComposerStyle.java',
             JAVA / 'app/flexygram/composer/ComposerGeometry.java', probe]
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    *map(str, files)], check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'PairProbe'], check=True, capture_output=True)
