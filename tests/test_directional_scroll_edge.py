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
        final float band = 136f, strength = .68f, yEdge = 500f;
        float previous = Float.NEGATIVE_INFINITY;
        for (int y = 300; y <= 700; y++) {
            float proximity = DirectionalScrollEdge.proximity(y, yEdge, band);
            float projectedY = DirectionalScrollEdge.projectY(y, yEdge, proximity, strength);
            require(projectedY > previous);
            if (Math.abs(y - yEdge) >= band) require(projectedY == y);
            previous = projectedY;
        }
        float before = DirectionalScrollEdge.proximity(490, yEdge, band);
        float after = DirectionalScrollEdge.proximity(510, yEdge, band);
        require(before == after);
        float topY = DirectionalScrollEdge.projectY(490, yEdge, before, strength);
        float bottomY = DirectionalScrollEdge.projectY(510, yEdge, after, strength);
        require(bottomY - topY < 10f);
        require(Math.abs((bottomY + topY) / 2f - yEdge) < .001f);
        require(DirectionalScrollEdge.projectX(0, 200, 1f, strength) > 30f);
        require(DirectionalScrollEdge.projectX(0, 200, 0f, strength) == 0f);
        require(DirectionalScrollEdge.projectX(0, 200, 1f, 0f) == 0f);
        require(DirectionalScrollEdge.projectY(460, yEdge, 1f, 0f) == 460f);
        require(DirectionalScrollEdge.settle(0, 120) == 1f);
        require(DirectionalScrollEdge.settle(60, 120) == .5f);
        require(DirectionalScrollEdge.engagement(0, 36) == .45f);
        require(DirectionalScrollEdge.engagement(18, 36) > .8f);
        require(DirectionalScrollEdge.engagement(36, 36) == 1f);
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


def test_active_rows_are_projected_without_cutting_them_at_the_dock():
    common = (JAVA/'org/telegram/ui/Components/RecyclerListView.java').read_text()
    draw = method(common, 'protected final int beginDirectionalScrollEdge(')
    assert 'setPolyToPoly(scrollEdgeSource, 0, scrollEdgeTarget, 0, 4)' in draw
    assert 'canvas.concat(scrollEdgeProjection)' in draw
    assert 'clipRect' not in draw and 'saveLayer' not in draw
    assert draw.index('if (top == 0f && bottom == 0f') < draw.index('new Matrix()')
    assert draw.index('if (scrollEdgeProjection == null)') < draw.index('new float[8]')
