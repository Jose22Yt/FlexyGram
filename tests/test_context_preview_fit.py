"""Run the real placement math across pinned/translation/keyboard safe areas."""
from pathlib import Path
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
JAVA = ROOT / 'TMessagesProj/src/main/java'


def test_whole_message_fits_and_spring_never_flips_preview(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    probe = tmp_path / 'FullPreviewProbe.java'
    probe.write_text('''import app.flexygram.bubbles.interaction.ContextPreviewPlacement;
public class FullPreviewProbe {
 static void check(boolean ok){if(!ok)throw new AssertionError();}
 public static void main(String[] args) {
  for(int panels:new int[]{0,48,100,180}) for(int keyboard:new int[]{0,250})
   for(int window:new int[]{700,1000,1600}) for(int menu:new int[]{150,260})
    for(int height:new int[]{24,64,200,1200,12000}) for(int sourceTop:new int[]{-1000,100,500,2000}) {
     int top=32+56+panels,bottom=window-keyboard-88;
     int chrome=Math.min(menu,bottom-top-48);
     if(chrome<64)continue;
     var p=ContextPreviewPlacement.fit(sourceTop,height,top,bottom,chrome,64,8);
     check(p.popupY>=top);
     check(p.popupY+chrome+p.gapHeight<=bottom);
     float actualTop=sourceTop+height*(1-p.scale)*.5f+p.offsetY;
     float actualBottom=actualTop+height*p.scale;
     check(Math.abs(actualTop-(p.popupY+64+8))<.02f);
     check(actualBottom<=p.popupY+64+p.gapHeight-8+.02f);
     check(p.scrollRange<.02f);
     float finalScale=ContextPreviewPlacement.animatedScale(p.scale,1.2f,1.25f);
     if(p.scale<1f)check(Math.abs(finalScale-p.scale)<.00001f);
     for(float phase:new float[]{-.2f,0,.25f,.5f,1,1.2f})
      check(ContextPreviewPlacement.animatedScale(p.scale,phase,1.25f)>0);
    }
 }
}''')
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path),
                    str(JAVA / 'app/flexygram/bubbles/interaction/ContextPreviewPlacement.java'),
                    str(ROOT / 'tools/beta_integration/PlacementProbe.java'), str(probe)],
                   check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'PlacementProbe'], check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'FullPreviewProbe'], check=True, capture_output=True)


def test_full_preview_does_not_overwrite_normal_row_text_block_cache():
    cell = (JAVA / 'org/telegram/ui/Cells/ChatMessageCell.java').read_text()
    # Both text and animated emoji must use local all-block bounds, leaving scrolling caches intact.
    assert cell.count('if (origin && !drawAllBlocks && !fullyDraw)') == 2
    assert 'if (fullyDraw) {\n                this.firstVisibleBlockNum = 0;' not in cell
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    start = chat.index('boolean oldFullyDraw = cell != null && cell.isFullyDraw();')
    end = chat.index('cell.setFullyDraw(oldFullyDraw)', start)
    assert 'cell.drawOutboundsContent(canvas)' in chat[start:end]
    assert '} finally {' in chat[start:end]


def test_popup_bottom_compiles_with_fractional_animated_input_height(tmp_path):
    if not shutil.which('java'):
        pytest.skip('JDK required')
    chat = (JAVA / 'org/telegram/ui/ChatActivity.java').read_text()
    start = chat.index('int availableBottom =', chat.index('if (compactContext && signatureMessageGap != null)'))
    expression = chat[start:chat.index(';', start) + 1]
    probe = tmp_path / 'PopupBottomProbe.java'
    probe.write_text('''public class PopupBottomProbe {
 static class View { int height; int getHeight(){return height;} }
 static class Insets { int getCurrentMaxBottomInset(){return 20;} }
 static class TopicsTabsView { enum Position { BOTTOM } }
 static View chatListView=new View(),contentView=new View();
 static Insets windowInsetsStateHolder=new Insets();
 static float inputIslandHeightCurrent,tabs;
 static float getTopicTabsSideSize(TopicsTabsView.Position p){return tabs;}
 static int dp(int n){return n;}
 static int bottom(int[] window,int[] contentWindow){EXPRESSION return availableBottom;}
 public static void main(String[] args){
  for(int listHeight:new int[]{400,1000}) for(float input:new float[]{0,48,48.25f,96.75f})
   for(float tab:new float[]{0,32,32.5f}) {
    chatListView.height=listHeight;contentView.height=900;inputIslandHeightCurrent=input;tabs=tab;
    int actual=bottom(new int[]{0,50},new int[]{0,10});
    double bound=Math.min(50+listHeight,10+900-20-input-tab-9)-8;
    if(actual>bound||bound-actual>=1)throw new AssertionError("unsafe bottom "+actual+" / "+bound);
   }
 }
}'''.replace('EXPRESSION', expression))
    subprocess.run(['java', '-m', 'jdk.compiler/com.sun.tools.javac.Main', '-d', str(tmp_path), str(probe)],
                   check=True, capture_output=True)
    subprocess.run(['java', '-cp', str(tmp_path), 'PopupBottomProbe'], check=True, capture_output=True)
