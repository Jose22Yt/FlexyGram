"""Actual capture-region filter and transition guard; no claim of physical GPU timing."""
from test_render_work_reuse import JAVA,probe
from test_composer_layout import method


def test_hidden_material_is_excluded_without_losing_alpha_or_repeating_invalidations(tmp_path):
    node=(JAVA/'org/telegram/ui/Components/blur3/drawable/BlurredBackgroundDrawableRenderNode.java').read_text()
    source=(JAVA/'org/telegram/ui/Components/blur3/source/BlurredBackgroundSourceRenderNode.java').read_text()
    probe(tmp_path,{'Probe.java':'''import java.util.*;
public class Probe {
 static class RectF{boolean empty;void inset(int x,int y){}boolean isEmpty(){return empty;}}
 static class BlurredBackgroundDrawableRenderNode{
  boolean sourceCaptureEnabled=true;final Notify source=new Notify();int alpha=255;
  boolean hasDisplayList(){return true;}int getAlpha(){return alpha;}RectF getPaddedBounds(){return new RectF();}void getPositionRelativeSource(RectF r){}
  SET GET
 }
 static class Notify{int calls;void dispatchOnDrawablesRelativePositionChange(){calls++;}}
 final List<BlurredBackgroundDrawableRenderNode> drawables=new ArrayList<>();
 REGIONS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){Probe p=new Probe();var band=new BlurredBackgroundDrawableRenderNode();var island=new BlurredBackgroundDrawableRenderNode();p.drawables.add(band);p.drawables.add(island);List<RectF> positions=new ArrayList<>();
 check(p.getVisiblePositions(positions,0,8)==2);
 for(int i=0;i<10000;i++)band.setSourceCaptureEnabled(false);
 check(band.source.calls==1&&band.alpha==255&&p.getVisiblePositions(positions,0,8)==1);
 for(int i=0;i<10000;i++)band.setSourceCaptureEnabled(true);
 check(band.source.calls==2&&p.getVisiblePositions(positions,0,8)==2);
 island.alpha=0;check(p.getVisiblePositions(positions,0,8)==1);
 }}'''.replace('SET',method(node,'public void setSourceCaptureEnabled(')).replace('GET',method(node,'public boolean isSourceCaptureEnabled(')).replace('REGIONS',method(source,'public int getVisiblePositions('))})
    draw=method(node,'public void draw(@NonNull Canvas canvas)')
    assert draw.index('!canvas.isHardwareAccelerated()')<draw.index('setSourceCaptureEnabled(true)')
    compositor=(JAVA/'org/telegram/ui/Components/chat/ChatInputViewsContainer.java').read_text()
    assert 'if (!snapshotPass)' in compositor and 'drawInputBackground && !islands' in compositor


def test_home_bar_never_enables_telegram_lens_but_other_surfaces_keep_their_policy():
    home=(JAVA/'org/telegram/ui/MainTabsActivity.java').read_text()
    assert 'iBlur3FactoryGlass.setLiquidGlassEffectAllowed(false)' in home
    assert 'BlurredBackgroundProviderImpl.mainTabsNormal(resourceProvider)' in home
    refresh=method(home,'private void blur3_updateColors()')
    assert '.setLiquidGlassEffectAllowed(false)' in refresh
    assert 'FLAG_LIQUID_GLASS' not in refresh
    pause=method(home,'public void onPause()')
    assert 'releaseKyantDock()' in pause
    provider=(JAVA/'org/telegram/ui/Components/blur3/drawable/color/impl/BlurredBackgroundProviderImpl.java').read_text()
    assert 'return mainTabs(resourcesProvider,false)' in method(provider,'public static BlurredBackgroundProvider mainTabsNormal(')
    assert 'return mainTabs(resourcesProvider,true)' in method(provider,'public static BlurredBackgroundProvider mainTabs(')
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    assert 'setLiquidGlassEffectAllowed(liquidPolicy)' in chat
