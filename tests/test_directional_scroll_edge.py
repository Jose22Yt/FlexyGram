"""The entering edge is exclusive, and only intersecting rows can fold."""
from test_composer_layout import method
from test_render_work_reuse import JAVA, probe


def test_edge_geometry_one_side_at_a_time_and_settles_without_overshoot(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.scroll.DirectionalScrollEdge;
public class Probe {
    static void require(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        int bottom = DirectionalScrollEdge.forDelta(0, 1);
        int top = DirectionalScrollEdge.forDelta(bottom, -1);
        require(bottom == DirectionalScrollEdge.BOTTOM && top == DirectionalScrollEdge.TOP);
        require(DirectionalScrollEdge.forDelta(top, 0) == top);
        for (int edge : new int[]{top, bottom}) {
            float previous = 1f;
            for (int distance = 1; distance <= 64; distance++) {
                float y = edge == top ? 100 + distance - 48 : 500 - distance;
                float fold = DirectionalScrollEdge.fold(edge, 100, 500, y, y + 48, 64);
                require(fold >= 0 && fold < previous);
                require(DirectionalScrollEdge.fold(-edge, 100, 500, y, y + 48, 64) == 0f);
                previous = fold;
            }
            require(previous == 0f);
            require(DirectionalScrollEdge.fold(edge, 100, 500, 250, 290, 64) == 0f);
            require(DirectionalScrollEdge.fold(edge, 100, 500, 38, 100, 64) == 0f);
            require(DirectionalScrollEdge.fold(edge, 100, 500, 500, 600, 64) == 0f);
        }
        require(DirectionalScrollEdge.settle(0, 120) == 1f);
        require(DirectionalScrollEdge.settle(60, 120) == .25f);
        require(DirectionalScrollEdge.settle(120, 120) == 0f);
        require(DirectionalScrollEdge.settle(150, 120) == 0f);
    }
}'''}, [JAVA/'app/flexygram/scroll/DirectionalScrollEdge.java'])


def test_effect_is_opt_in_and_confined_to_live_drawing_of_two_surfaces():
    common = (JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    home = (JAVA/'org/telegram/ui/DialogsActivity.java').read_text()
    chat = (JAVA/'org/telegram/ui/ChatActivity.java').read_text()
    toggle = (JAVA/'app/flexygram/home/HomeListSettingsActivity.java').read_text()
    settings = (JAVA/'app/flexygram/scroll/DirectionalScrollSettings.java').read_text()

    assert 'getBoolean(KEY, false)' in settings
    assert toggle.count('addRow("flexyDirectionalScrollEdge")') == 1
    assert home.count('enableDirectionalScrollEdge(') == chat.count('enableDirectionalScrollEdge(') == 1
    assert 'instanceof DialogCell' in home[home.index('public class DialogsRecyclerView'):]
    assert 'getCurrentMessagesGroup() == null' in chat
    assert '!ignoreClipChild' in method(common, 'protected final boolean isDirectionalScrollEdgeDrawing()')
    assert 'clearDirectionalScrollEdge();' in method(common, 'public boolean dispatchTouchEvent(MotionEvent ev)')
    assert 'getScrollState() == SCROLL_STATE_IDLE' in method(common, 'public void onScrolled(int dx, int dy)')
    assert 'drawingScrollEdge = DirectionalScrollEdge.NONE;' in method(common, 'protected void dispatchDraw(@NonNull Canvas canvas)')
    assert 'isAccessibilityScreenReaderEnabled()' in method(common, 'private void prepareDirectionalScrollEdge()')
