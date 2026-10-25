"""Reuse explicit Music doubles; run actual changed inner LineView and detach body.
FrameLayout shell is a fixture, not full LyricsView/RecyclerListView/auth/playback.
"""
import importlib.util
import subprocess
from pathlib import Path


def method(source, anchor):
    start = source.index(anchor)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


def write_stubs(source, root):
    radius_spec = importlib.util.spec_from_file_location('radius_probe_fixture', root/'tools/connected_alpha/performance/radius_probe.py')
    radius = importlib.util.module_from_spec(radius_spec)
    radius_spec.loader.exec_module(radius)
    radius.write_sources(source)
    spec = importlib.util.spec_from_file_location('original_music_stubs', root/'tools/connected_alpha/music_visual/stubs.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.write_stubs(source, root)
    def put(path, text):
        dest = source/path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    package = root/'TMessagesProj/src/main/java/app/exteraless/player'
    for name in ('LyricsFill', 'Lyrics'):
        put('app/exteraless/player/'+name+'.java', (package/(name+'.java')).read_text())
    put('tw/nekomimi/nekogram/helpers/TypefaceHelper.java', '''package tw.nekomimi.nekogram.helpers;
public class TypefaceHelper {public static android.graphics.Typeface lyricsTypeface(){return android.graphics.Typeface.create("sans-serif",1);}}''')
    actual = (package/'LyricsView.java').read_text()
    body = actual[actual.index('    private class LineView extends View'):actual.rfind('\n}')]
    # The outer callback functions are copied too; only their container/list dependencies are doubles.
    detach = method(actual, '    protected void onDetachedFromWindow()')
    shell = (Path(__file__).parent/'LyricsHarness.java.in').read_text()
    for token, replacement in {'_LINE_': body, '_CURRENT_': method(actual, '    private long currentMs()'),
                               '_PLAYING_': method(actual, '    private boolean isPlaying()'), '_DETACH_': detach}.items():
        shell = shell.replace(token, replacement)
    put('app/exteraless/player/LyricsHarness.java', shell)
    original = subprocess.check_output(['git','show','997ac40a65be00c672dc8009b61f55825537d498:TMessagesProj/src/main/java/app/exteraless/player/LyricsView.java'], cwd=root, text=True)
    before = (Path(__file__).parent/'LyricsHarness.java.in').read_text().replace('LyricsHarness','BaselineLyricsHarness').replace('post(scrollToCurrent)', 'list.post(scrollToCurrent)')
    for token, replacement in {'_LINE_': original[original.index('    private class LineView extends View'):original.rfind('\n}')],
            '_CURRENT_': method(original,'    private long currentMs()'), '_PLAYING_': method(original,'    private boolean isPlaying()'),
            '_DETACH_': ''}.items(): before = before.replace(token,replacement)
    put('app/exteraless/player/BaselineLyricsHarness.java', before)

