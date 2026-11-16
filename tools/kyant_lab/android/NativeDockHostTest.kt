package app.flexygram.kyant

import android.view.Gravity
import android.view.MotionEvent
import android.view.View
import android.widget.Button
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.ComposeView
import org.junit.Assert.*
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.shadows.ShadowLooper
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

/** Real Android measurement and touch dispatch with a real Compose fillMaxSize overlay.
 * Scene controls are explicit test fixtures. This does not benchmark physical GPU rendering.
 */
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w360dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class NativeDockHostTest {
    private class Fixture(corrected: Boolean, bottomInset: Int = 0) {
        val controller = Robolectric.buildActivity(ComponentActivity::class.java).setup()
        val activity = controller.get()
        val root = FrameLayout(activity)
        val dock = View(activity)
        val wrapper: FrameLayout = if (corrected) KyantDockContainer(activity, dock) else FrameLayout(activity)
        var clicks = 0
        var moves = 0
        val scene = object: FrameLayout(activity) {
            override fun onTouchEvent(event: MotionEvent): Boolean {
                if (event.actionMasked == MotionEvent.ACTION_MOVE) moves++
                return true
            }
        }
        init {
            root.addView(scene, FrameLayout.LayoutParams(-1,-1))
            for (top in intArrayOf(24,144,300)) {
                val button = Button(activity).apply { text="Native control"; setOnClickListener { clicks++ } }
                scene.addView(button, FrameLayout.LayoutParams(120,64).apply { leftMargin=20; topMargin=top })
            }
            wrapper.setPadding(0,0,0,bottomInset)
            wrapper.setOnClickListener { /* Original native wrapper consumes its own bar area. */ }
            wrapper.addView(dock, FrameLayout.LayoutParams(-1,72,Gravity.BOTTOM))
            val overlay = ComposeView(activity).apply { setContent { Box(Modifier.fillMaxSize()) } }
            wrapper.addView(overlay, FrameLayout.LayoutParams(-1,-1))
            root.addView(wrapper, FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM))
            activity.setContentView(root)
            measure()
        }
        fun measure() {
            root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),
                View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY))
            root.layout(0,0,360,800)
        }
        fun touch(action: Int, x: Float, y: Float, offset: Long = 0) {
            val event=MotionEvent.obtain(100,100+offset,action,x,y,0)
            root.dispatchTouchEvent(event)
            event.recycle()
        }
        fun tap(y: Float) { touch(MotionEvent.ACTION_DOWN,60f,y); touch(MotionEvent.ACTION_UP,60f,y,20); ShadowLooper.idleMainLooper() }
        fun close() { controller.pause().stop().destroy() }
    }

    @Test fun originalMatchParentComposeOverlayExpandsWrapperAndBlocksNativeControls() {
        val f=Fixture(false)
        try {
            assertEquals(800,f.wrapper.measuredHeight)
            f.tap(50f); f.tap(170f); f.tap(330f)
            assertEquals("Legacy wrapper intercepts the whole screen",0,f.clicks)
        } finally { f.close() }
    }

    @Test fun boundedOverlayPreservesNativeBarBoundsAndPassesHeaderChatsAndScroll() {
        val f=Fixture(true,24)
        try {
            assertFalse("Optical edges may draw outside the wrapper",f.wrapper.clipChildren)
            assertFalse(f.wrapper.clipToPadding)
            assertNull("No rectangular backdrop on the Android host",f.wrapper.background)
            assertEquals("No platform rectangular elevation shadow",0f,f.wrapper.elevation,0f)
            assertEquals(96,f.wrapper.measuredHeight)
            assertEquals(704,f.wrapper.top)
            assertEquals(72,f.dock.height)
            assertEquals(24,f.wrapper.paddingBottom)
            f.tap(50f); f.tap(170f); f.tap(330f)
            assertEquals("Native controls above the dock remain clickable",3,f.clicks)
            f.touch(MotionEvent.ACTION_DOWN,250f,500f)
            f.touch(MotionEvent.ACTION_MOVE,250f,400f,20)
            f.touch(MotionEvent.ACTION_UP,250f,400f,40)
            assertTrue("Scroll gestures reach the native scene",f.moves>0)
            f.dock.visibility=View.GONE
            f.measure()
            assertEquals("Hidden dock leaves only native system padding",24,f.wrapper.height)
            f.tap(330f)
            assertEquals(4,f.clicks)
        } finally { f.close() }
    }
}
