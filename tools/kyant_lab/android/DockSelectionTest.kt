package app.flexygram.kyant

import androidx.compose.runtime.*
import androidx.compose.ui.test.junit4.createComposeRule
import app.flexygram.kyant.utils.DockSelectionAnimation
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode

@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w480dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class DockSelectionTest {
 @get:Rule val compose=createComposeRule()
 @Test fun selectorStaysBoundedAndNewGestureReplacesPendingMotion() {
  lateinit var selector:DockSelectionAnimation
  compose.mainClock.autoAdvance=false
  compose.setContent {
   val scope=rememberCoroutineScope()
   selector=remember {DockSelectionAnimation(scope,0f,0f..3f,onDragStopped={},onDrag={_,_->})}
  }
  compose.runOnIdle {selector.animateToValue(3f)}
  compose.mainClock.advanceTimeBy(80)
  compose.runOnIdle {assertTrue(selector.value in 0f..3f);assertTrue("Tab clicks activate the lens",selector.pressProgress>0f);selector.updateValue(1f)}
  compose.mainClock.advanceTimeBy(32)
  compose.runOnIdle {assertEquals(1f,selector.value,.001f);selector.animateToValue(99f)}
  compose.mainClock.advanceTimeBy(240)
  compose.runOnIdle {assertEquals(3f,selector.value,.001f);selector.updateValue(-99f)}
  compose.mainClock.advanceTimeBy(32)
  compose.runOnIdle {assertEquals(0f,selector.value,.001f)}
  compose.mainClock.advanceTimeBy(1000)
  compose.runOnIdle {
   assertEquals(0f,selector.value,.001f);assertEquals(0f,selector.pressProgress,.001f)
   selector.animateToValue(3f);selector.animateToValue(1f);selector.animateToValue(2f)
  }
  compose.mainClock.advanceTimeBy(80)
  compose.runOnIdle {assertTrue("A cancelled transition cannot release the newer optical pulse",selector.pressProgress>0f)}
  compose.mainClock.advanceTimeBy(500)
  compose.runOnIdle {assertEquals(2f,selector.value,.001f);assertEquals(0f,selector.pressProgress,.001f)}
 }
}
