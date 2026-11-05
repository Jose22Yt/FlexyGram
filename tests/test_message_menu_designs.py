"""Native message permission admission and live popup ordering; widget rendering has a separate Android probe."""
from pathlib import Path
import re
import xml.etree.ElementTree as E
from test_render_work_reuse import probe, JAVA


def method(source, anchor):
    start=source.index(anchor);end=source.index('{',start)+1;level=1
    while level:
        level+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]


def test_actual_chat_permission_admission_never_uses_the_users_chosen_actions(tmp_path):
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    admission=method(chat,'private java.util.EnumSet<app.flexygram.bubbles.interaction.BubbleActionPanelView.Action> signatureContextActions(')
    used=set(re.findall(r'OPTION_\w+',admission))
    constants=''.join('static final int '+key+'='+value+';' for key,value in re.findall(r'public final static int (OPTION_\w+) = (\d+);',chat) if key in used)
    enum=re.search(r'public enum Action \{([^}]+)\}',(JAVA/'app/flexygram/bubbles/interaction/BubbleActionPanelView.java').read_text())[1]
    files={
      'app/flexygram/bubbles/interaction/BubbleActionPanelView.java':'package app.flexygram.bubbles.interaction;public class BubbleActionPanelView{public enum Action{'+enum+'}}',
      'Probe.java':'''import java.util.*;import app.flexygram.bubbles.interaction.BubbleActionPanelView.Action;
public class Probe {
 static class Status{boolean allowReply,allowCopy,allowForward,allowEdit,allowDelete;}
 static class Owner{boolean noforwards;}
 static class Message{Owner messageOwner=new Owner();boolean ephemeral;boolean isEphemeral(){return ephemeral;}}
 Status lastMessageMenuStatus=new Status();Message selectedObject=new Message();CONSTANTS
 ADMISSION
 public static void main(String[]args){Probe p=new Probe();ArrayList<Integer> options=new ArrayList<>();
 if(!p.signatureContextActions(options).isEmpty())throw new AssertionError("No permissions must admit no primary actions");
 p.lastMessageMenuStatus.allowCopy=true;if(!p.signatureContextActions(options).equals(EnumSet.of(Action.COPY,Action.STICKER)))throw new AssertionError();
 p.selectedObject.messageOwner.noforwards=true;if(p.signatureContextActions(options).contains(Action.STICKER))throw new AssertionError("Protected content sticker bypass");
 p.selectedObject.messageOwner.noforwards=false;p.selectedObject.ephemeral=true;if(p.signatureContextActions(options).contains(Action.STICKER))throw new AssertionError("Ephemeral content sticker bypass");
 p.lastMessageMenuStatus.allowCopy=false;options.add(OPTION_SHARE);options.add(OPTION_COPY_LINK);options.add(OPTION_SAVE_TO_GALLERY2);options.add(OPTION_PIN);
 if(!p.signatureContextActions(options).equals(EnumSet.of(Action.SHARE,Action.LINK,Action.SAVE,Action.PIN)))throw new AssertionError("Only native eligible options can be added");
 }}'''.replace('CONSTANTS',constants).replace('ADMISSION',admission),
    }
    probe(tmp_path,files,[])


def test_live_popup_preserves_reactions_message_menu_order_and_revalidates_clicks():
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    reactions=chat.index('scrimPopupContainerLayout.addView(reactionsLayout, params)')
    gap=chat.index('scrimPopupContainerLayout.addView(signatureMessageGap',reactions)
    menu=chat.index('scrimPopupContainerLayout.addView(popupLayout',gap)
    assert reactions<gap<menu
    assert 'compactContext ? 8 : -20' in chat[:reactions]
    listener=chat[chat.index('panel.setListener(action->'):chat.index('ChatScrimPopupContainerLayout scrimPopupContainerLayout =',chat.index('panel.setListener(action->'))]
    assert listener.index('if(!freshAllowed.contains(action))return;')<listener.index('FlexyStickerSheet.show')
    assert listener.index('fillMessageMenu(')<listener.index('case SAVE:processSelectedOption')
    assert 'new android.graphics.drawable.ColorDrawable(Color.TRANSPARENT)' in chat
    assert '"bubble_style","context"' in (JAVA/'app/flexygram/settings/signature/SignatureDirectSettingsActivity.java').read_text()


def test_menu_translation_keys_and_all_labels_are_present():
    root=JAVA.parent/'res';sets=[]
    for language in ['values','values-es','values-ru']:
        tree=E.parse(root/language/'flexy_message_menu.xml')
        sets.append({item.attrib['name']for item in tree.getroot()})
        assert all(item.text for item in tree.getroot())
    assert sets[0]==sets[1]==sets[2]


def test_live_cards_share_existing_blur_source_and_preserve_input_layer():
    chat=(JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    block=chat[chat.index('final boolean menuBlur ='):chat.index('panel.setListener(action->')]
    assert 'BlurredBackgroundProviderImpl.checkBlurEnabled(currentAccount, themeDelegate)' in block
    assert 'panel.setSurfaceFactory' in block and 'scrimBlur3Factory.create(target, true)' in block
    assert 'nativeMenu.setBackgroundColor(Color.TRANSPARENT)' in block
    assert 'scrimBlur3Factory.create(nativeScroll, true)' in block
    assert 'makeGlobalBlurBitmaps' not in block and 'captureBlur' not in block
    start=chat.index('final int messageScrimSave = canvas.save();')
    end=chat.index('canvas.restoreToCount(messageScrimSave);',start)
    assert chat.index('canvas.clipRect(0, 0, getMeasuredWidth(), messageScrimBottom);',start)<chat.index('if (scrimViewReaction == null || scrimView == null)',start)<end
    assert end<chat.index('if (scrimView != null || messageEnterTransitionContainer.isRunning())',end)
    assert 'chatInputViewsContainer.getInputBubbleTop()' in chat[start:end]
