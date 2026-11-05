"""Real extended position policy: negative translation without negative layout heights."""
from test_render_work_reuse import JAVA, probe


def test_deep_lowering_is_allowed_and_portable_without_negative_reservation(tmp_path):
    probe(tmp_path,{'Probe.java':'''import app.flexygram.composer.*;import app.flexygram.studio.core.*;
public class Probe {
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 check(ComposerStyle.MIN_POSITION==-160&&ComposerStyle.MAX_POSITION==16);
 for(int position=-160;position<=16;position++){
 check(ComposerStyle.position(position)==position);
 check(ComposerStyle.offset(position)==10+position);
 check(ComposerStyle.reserve(position)>=0);
 check(44+ComposerStyle.reserve(position)>=44);
 check(StudioSchema.key("composer","position").validate(position).equals(position));
 }
 check(-ComposerStyle.offset(-160)==150); // Whole island translates down, without clamping to screen.
 check(ComposerStyle.position(Integer.MIN_VALUE)==-160&&ComposerStyle.position(Integer.MAX_VALUE)==16);
 check(ComposerStyle.offset(0)==10&&ComposerStyle.reserve(0)==10);
 check(ComposerStyle.reserve(-4)==6&&ComposerStyle.reserve(-10)==0);
 for(int invalid:new int[]{-161,17}){
 try{StudioSchema.key("composer","position").validate(invalid);throw new AssertionError();}catch(IllegalArgumentException expected){}
 }
 }
}'''},[JAVA/'app/flexygram/composer/ComposerStyle.java',JAVA/'app/flexygram/composer/ComposerGeometry.java',JAVA/'app/flexygram/studio/core/StudioSchema.java'])


def test_both_sliders_use_policy_limits_and_reset_is_still_accessible():
    gallery=(JAVA/'app/flexygram/settings/signature/ConversationStyleSettingsActivity.java').read_text()
    legacy=(JAVA/'app/flexygram/composer/FlexyComposerSettingsActivity.java').read_text()
    for source in [gallery,legacy]:
        assert 'ComposerStyle.MAX_POSITION' in source and 'ComposerStyle.MIN_POSITION' in source
    assert 'FlexyComposerConfig.setPosition(0)' in gallery
