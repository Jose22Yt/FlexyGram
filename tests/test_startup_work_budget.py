"""Exercise production page selection and dock measurement with counted children."""
import sqlite3
from test_render_work_reuse import JAVA, probe
from test_composer_layout import method


def test_archive_initial_page_keeps_pagination_and_end_threshold(tmp_path):
    source = (JAVA/'org/telegram/messenger/MessagesStorage.java').read_text()
    start = source.index('                    if (a == 0) {', source.index('public void getDialogs(int folderId'))
    end = source.index('\n\n', start)
    branch = source[start:end]
    probe(tmp_path, {'Probe.java': '''public class Probe{
 static void check(boolean b){if(!b)throw new AssertionError();}
 public static void main(String[]args){
 for(int count:new int[]{1,19,20,32,100,150})for(int a=0;a<2;a++){
  int offset=64,off,cnt;
  BRANCH
  check(a==0?off==offset&&cnt==count:off==0&&cnt>=20&&cnt<=100&&cnt==(count<20?20:Math.min(100,count)));
 }
 }}'''.replace('BRANCH', branch)})
    # A bounded first page leaves the remainder available through the normal offset.
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE dialogs(did INTEGER, pinned INTEGER, date INTEGER)')
    db.executemany('INSERT INTO dialogs VALUES (?,0,?)', [(i,i) for i in range(101)])
    pages = [db.execute('SELECT did FROM dialogs ORDER BY pinned DESC,date DESC LIMIT ?,?', (offset,32)).fetchall() for offset in range(0,101,32)]
    assert len(pages[0]) == 32
    assert [row[0] for page in pages for row in page] == list(reversed(range(101)))


def test_native_layout_skips_hidden_tabs_during_measurement():
    source=(JAVA/'org/telegram/ui/MainTabsLayout.java').read_text()
    measure=method(source,'protected void onMeasure(int widthMeasureSpec, int heightMeasureSpec)')
    assert 'isViewVisible(child)' in measure
    assert 'if (!isViewVisible(getChildAt(a))) continue;' in measure
