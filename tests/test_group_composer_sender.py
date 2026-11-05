"""Execute native send-as eligibility/layout, with deterministic Android doubles."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_send_as_stays_in_compact_pill_and_restores_native_params(tmp_path):
    source=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
    methods='\n'.join(method(source,s) for s in ['private boolean hasFlexySpecialControls()', 'private boolean applyFlexySenderPresentation('])
    probe(tmp_path,{'Probe.java':'''import app.flexygram.composer.*;
public class Probe {
 static int VISIBLE=0,GONE=8;
 static class MarginLayoutParams {int leftMargin;}
 static class FrameLayout {static class LayoutParams extends MarginLayoutParams {int width,height,bottomMargin;}}
 static class View {int visibility=VISIBLE;Object tag;FrameLayout.LayoutParams params=new FrameLayout.LayoutParams();int getVisibility(){return visibility;}Object getTag(){return tag;}Object getLayoutParams(){return params;}}
 boolean isChat=true,isStories,botRow;Object parentFragment=new Object();View senderSelectView,botCommandsMenuButton,botWebViewButton,emojiButton=new View();
 int flexyInsetDp,flexyGapDp;float density=1;
 int dp(float n){return (int)Math.ceil(n*density);}boolean wantsFlexyBotRow(){return botRow;}
 METHODS
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[] args){Probe p=new Probe();check(!p.hasFlexySpecialControls());p.senderSelectView=new View();p.emojiButton.params.leftMargin=100;
 check(!p.hasFlexySpecialControls());
 for(float d:new float[]{1,1.5f,2,3})for(int level=0;level<3;level++)for(int gap=2;gap<=8;gap++){
 p.density=d;p.flexyInsetDp=ComposerStyle.inset(level);p.flexyGapDp=gap;
 check(p.applyFlexySenderPresentation(true));FrameLayout.LayoutParams lp=p.senderSelectView.params;
 float pillLeft=ComposerGeometry.pillLeft(0,p.dp(44)-p.dp(p.flexyInsetDp),p.dp(gap));
 check(lp.leftMargin>=pillLeft&&lp.bottomMargin>=p.dp(p.flexyInsetDp));
 check(lp.leftMargin+lp.width<=p.dp(ComposerGeometry.senderTextStart(p.flexyInsetDp,gap)));
 check(lp.width+2*lp.bottomMargin==p.dp(44)||Math.abs(lp.width+2*lp.bottomMargin-p.dp(44))<=2);
 check(p.dp(ComposerGeometry.senderTextStart(p.flexyInsetDp,gap))+p.dp(56)<p.dp(280));
 p.applyFlexySenderPresentation(false);check(lp.width==p.dp(36)&&lp.leftMargin==p.dp(4.66f)&&lp.bottomMargin==p.dp(4));
 }
 p.botWebViewButton=new View();check(p.hasFlexySpecialControls());p.botWebViewButton=null;
 p.botCommandsMenuButton=new View();check(p.hasFlexySpecialControls());p.botCommandsMenuButton=null;
 p.isStories=true;check(p.hasFlexySpecialControls());p.isStories=false;
 p.senderSelectView.visibility=GONE;check(!p.applyFlexySenderPresentation(true)&&p.hasFlexySpecialControls());
 p.senderSelectView=null;p.emojiButton.params.leftMargin=0;check(!p.applyFlexySenderPresentation(true)&&!p.hasFlexySpecialControls());
 }
}'''.replace('METHODS',methods)},[JAVA/'app/flexygram/composer/ComposerGeometry.java',JAVA/'app/flexygram/composer/ComposerStyle.java'])


def test_compact_sender_animation_does_not_move_text_or_request_layout_per_frame():
    source=(JAVA/'org/telegram/ui/Components/ChatActivityEnterView.java').read_text()
    update=method(source,'public void updateSendAsButton(boolean forceHide, boolean animated)')
    start=update.index('if (flexyCompactRequested && isChat && !isStories)')
    end=update.index('if ((isLiveComment',start)
    branch=update[start:end]
    assert 'setTranslationX(0)' in branch and 'messageTextTranslationX = 0' in branch
    assert '.animate().alpha(1f)' in branch
    assert 'addUpdateListener' not in branch and branch.count('requestLayout();')==1
    apply=method(source,'private void applyFlexyComposerPresentation(')
    assert 'ComposerGeometry.senderTextStart' in apply
    assert 'richDraftPreview.getLayoutParams()).leftMargin = text.leftMargin' in apply
