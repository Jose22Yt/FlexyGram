package app.flexygram.kyant
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Rect
import androidx.compose.ui.layout.boundsInRoot
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.platform.LocalLayoutDirection
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.unit.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w480dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class NativeBoundsTest {
 @get:Rule val compose = createComposeRule()
 @Test fun legacyRootContainerMisplacesPhysicalOffsetsInRtl() {
  var bounds=Rect.Zero
  compose.setContent {
   CompositionLocalProvider(LocalDensity provides Density(1f),LocalLayoutDirection provides LayoutDirection.Rtl) {
    Box(Modifier.offset { IntOffset(40,20) }.size(300.dp,64.dp)) {
     Box(Modifier.fillMaxSize().onGloballyPositioned { bounds=it.boundsInRoot() })
    }
   }
  }
  compose.runOnIdle { assertNotEquals(Rect(40f,20f,340f,84f),bounds) }
 }
 @Test fun physicalDockBoundsStayIdenticalInLtrAndRtl() {
  var direction by mutableStateOf(LayoutDirection.Ltr)
  var width by mutableFloatStateOf(300f)
  var bounds = Rect.Zero
  compose.setContent {
   CompositionLocalProvider(LocalDensity provides Density(1f),LocalLayoutDirection provides direction) {
    NativeDockBoundsLayout(40,20,width) {
     Box(Modifier.fillMaxSize().onGloballyPositioned { bounds=it.boundsInRoot() })
    }
   }
  }
  compose.runOnIdle { assertEquals(Rect(40f,20f,340f,84f),bounds); direction=LayoutDirection.Rtl }
  compose.runOnIdle { assertEquals(Rect(40f,20f,340f,84f),bounds); width=240f }
  compose.runOnIdle { assertEquals(Rect(40f,20f,280f,84f),bounds) }
 }
}
