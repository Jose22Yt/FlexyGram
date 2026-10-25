from release_1271_contract import read1270, restore1270
"""Integration contract: approved1266 composer bytes and executable settings routes.

Host fixtures exercise actual production route/row fragments, not a device screen.
"""
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
APPROVED='b478f02ad8a3cee5a17f58d3909c4961a3555651'
JAVA=ROOT/'TMessagesProj/src/main/java'

class ApprovedComposerIntegration(unittest.TestCase):
    def test_all_approved_composer_sources_artwork_and_preferences_are_identical(self):
        prefixes=('TMessagesProj/src/main/java/app/flexygram/composer/',
                  'TMessagesProj/src/main/res/drawable/flexy_composer_')
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',APPROVED],cwd=ROOT,text=True).splitlines()
        frozen=[p for p in paths if p.startswith(prefixes)]
        frozen += ['TMessagesProj/src/main/java/'+p for p in (
            'org/telegram/ui/Components/ChatActivityEnterView.java',
            'org/telegram/ui/Components/EditTextBoldCursor.java',
            'org/telegram/ui/Components/ChatActivityEnterViewAnimatedIconView.java',
            'app/exteraless/components/ChatActivityEnterViewStaticIconView.java',
            'org/telegram/ui/Components/chat/ChatInputViewsContainer.java')]
        frozen += ['TMessagesProj/src/main/res/'+locale+'/flexygram_composer.xml' for locale in ('values','values-es','values-ru')]
        self.assertGreater(len(frozen),20)
        for path in frozen:
            with self.subTest(path=path):
                self.assertEqual(__import__('studio_contract').restore(path,(ROOT/path).read_bytes()),subprocess.check_output(['git','show',APPROVED+':'+path],cwd=ROOT))
        expected={p for p in frozen if p.startswith(prefixes[0])}
        actual={str(p.relative_to(ROOT)) for p in (JAVA/'app/flexygram/composer').rglob('*') if p.is_file()}
        self.assertEqual(actual,expected)

    def test_actual_sections_text_input_rows_and_route_open_existing_activity(self):
        chats=read1270('TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraChatsActivity.java')
        root=__import__('studio_contract').restore('TMessagesProj/src/main/java/app/exteraless/settings/OpenExteraSettingsActivity.java',(JAVA/'app/exteraless/settings/OpenExteraSettingsActivity.java').read_bytes()).decode()
        rows=chats[chats.index('        linksHeaderRow = addRow("linksHeader");'):chats.index('        doubleTapHeaderRow = addRow("doubleTapHeader");')]
        fields=sorted(set(re.findall(r'\b(\w+Row)\s*=',rows)))
        start=chats.index('} else if (position == composerSettingsRow) {')+len('} else if (position == composerSettingsRow) {')
        route=chats[start:chats.index('} else if (position == menusRow)',start)]
        start=root.index('} else if (position == chatsRow) {')+len('} else if (position == chatsRow) {')
        entry=root[start:root.index('} else if (position == pluginsRow)',start)]
        fixture='''
public class SettingsRoute {
 static Object opened;
 static void presentFragment(Object activity){opened=activity;}
 static class ChatsConfig {static class Value {boolean flag;boolean Bool(){return flag;}}static Value inlineMathResult=new Value();}
 static class OpenExteraChatsActivity {
  int counter; _FIELDS_
  int addRow(String... key){return counter++;}
  void rows(){_ROWS_}
  void click(int position){if(position==composerSettingsRow){_ROUTE_}}
 }
 static void rootClick(){_ENTRY_}
 static void check(boolean v){if(!v)throw new AssertionError("settings route/order");}
 public static void main(String[] args){
  for(boolean enabled:new boolean[]{false,true}){
   ChatsConfig.inlineMathResult.flag=enabled;rootClick();check(opened instanceof OpenExteraChatsActivity);
   OpenExteraChatsActivity chats=(OpenExteraChatsActivity)opened;chats.rows();
   check(chats.flexyBubblesRow==chats.linksDividerRow+1);
   check(chats.inputHeaderRow==chats.flexyBubblesRow+1);
   check(chats.composerSettingsRow==chats.inputHeaderRow+1);
   check(chats.addCommaRow==chats.composerSettingsRow+1);
   chats.click(chats.composerSettingsRow);
   check(opened instanceof app.flexygram.composer.FlexyComposerSettingsActivity);
  }
  System.out.println("PASS actual settings row/route fragments; Android UI NOT_TESTED");
 }
}
'''.replace('_FIELDS_','int '+','.join(fields)+';').replace('_ROWS_',rows).replace('_ROUTE_',route).replace('_ENTRY_',entry)
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp);stub=d/'app/flexygram/composer/FlexyComposerSettingsActivity.java';stub.parent.mkdir(parents=True)
            stub.write_text('package app.flexygram.composer; public class FlexyComposerSettingsActivity {}')
            runner=d/'SettingsRoute.java';runner.write_text(fixture)
            subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-d',tmp,str(stub),str(runner)],check=True)
            self.assertIn('PASS actual settings',subprocess.check_output(['java','-cp',tmp,'SettingsRoute'],text=True))
