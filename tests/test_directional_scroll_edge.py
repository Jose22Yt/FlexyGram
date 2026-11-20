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
        final float band = DirectionalScrollEdge.BAND_DP, strength = DirectionalScrollEdge.STRENGTH, yEdge = 500f;
        final float testY = 440f;
        final float oldDisplacement = DirectionalScrollEdge.projectY(testY, yEdge,
                DirectionalScrollEdge.proximity(testY, yEdge, 136f), .68f) - testY;
        final float newDisplacement = DirectionalScrollEdge.projectY(testY, yEdge,
                DirectionalScrollEdge.proximity(testY, yEdge, band), strength) - testY;
        require(newDisplacement / oldDisplacement > 1.8f && newDisplacement / oldDisplacement < 2.2f);
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
        require(DirectionalScrollEdge.engagement(0, 36) == 0f);
        require(DirectionalScrollEdge.engagement(18, 36) == .5f);
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

    assert 'getBoolean(LEGACY_KEY, false) ? 1 : 0' in settings
    assert 'return style >= 1 && style <= 4;' in settings
    assert 'DirectionalScrollSettings.setEnabled(!DirectionalScrollSettings.enabled())' in toggle
    assert 'createSingleChoiceDialog' not in toggle
    assert toggle.count('addRow("flexyDirectionalScrollEdge")') == 1
    assert home.count('enableDirectionalScrollEdge(') == chat.count('enableDirectionalScrollEdge(') == 1
    assert 'instanceof DialogCell' in home[home.index('public class DialogsRecyclerView'):]
    assert 'getCurrentMessagesGroup() == null' in chat
    assert '!ignoreClipChild' in method(common, 'protected final boolean isDirectionalScrollEdgeDrawing()')
    assert 'clearDirectionalScrollEdge();' not in method(common, 'public boolean dispatchTouchEvent(MotionEvent ev)')
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
    assert 'switch (drawingScrollStyle)' not in draw
    assert draw.index('if (scrollEdgeProjection == null)') < draw.index('new float[8]')


def test_direction_changes_release_before_handoff_and_resume_from_visible_intensity(tmp_path):
    probe(tmp_path, {'Probe.java': '''
import app.flexygram.scroll.DirectionalScrollEdge;
import app.flexygram.scroll.DirectionalScrollMotion;
public class Probe {
    static void check(boolean valid) { if (!valid) throw new AssertionError(); }
    public static void main(String[] args) {
        final var m = new DirectionalScrollMotion();
        final int bottom = DirectionalScrollEdge.BOTTOM, top = DirectionalScrollEdge.TOP;
        m.scroll(bottom, 36, 36, 0);
        check(m.edge() == bottom && m.intensity() == 1 && !m.needsFrame());
        m.stop(100);
        m.advance(237);
        check(m.edge() == bottom && Math.abs(m.intensity() - .5f) < .005f);
        final float beforeResume = m.intensity();
        m.scroll(bottom, 1, 36, 237);
        check(m.intensity() == beforeResume && m.needsFrame());
        m.advance(337);
        check(m.intensity() == 1 && !m.needsFrame());

        m.scroll(top, 27, 36, 337);
        m.advance(389);
        check(m.edge() == bottom && Math.abs(m.intensity() - .5f) < .01f);
        m.scroll(top, 11, 36, 392);
        m.advance(442);
        check(m.edge() == top && m.intensity() == 0 && m.needsFrame());
        m.advance(542);
        check(m.edge() == top && m.intensity() == 1 && !m.needsFrame());

        m.scroll(bottom, 36, 36, 550);
        m.stop(570);
        m.advance(800);
        check(m.edge() == DirectionalScrollEdge.NONE && m.intensity() == 0 && !m.needsFrame());
        m.scroll(bottom, 1, 36, 802);
        check(m.intensity() < .005f);
        m.scroll(bottom, 17, 36, 811);
        check(m.intensity() == .5f);
        m.reset();
        check(m.edge() == DirectionalScrollEdge.NONE && !m.needsFrame());
    }
}'''}, [JAVA/'app/flexygram/scroll/DirectionalScrollEdge.java',
        JAVA/'app/flexygram/scroll/DirectionalScrollMotion.java'])
