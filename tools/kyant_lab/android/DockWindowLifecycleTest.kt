package app.flexygram.kyant

import android.view.View
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.compose.runtime.MutableState
import org.junit.Test
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.util.ReflectionHelpers
import org.robolectric.util.ReflectionHelpers.ClassParameter
import org.telegram.messenger.ApplicationLoader
import org.telegram.ui.MainTabsLayout
import org.telegram.ui.Components.glass.GlassTabView

/** Real bridge/window callbacks. Hardware capability and completed composition publication are
 * explicit test inputs; this test does not claim physical GPU rendering or optical equivalence. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w360dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class DockWindowLifecycleTest {
 @Test fun enabledMaterialSurvivesWindowHideReturnAndFocusWithoutChangingPreference() {
  val controller=Robolectric.buildActivity(ComponentActivity::class.java).setup()
  val activity=controller.get()
  ApplicationLoader.applicationContext=activity
  KyantDockConfig.setEnabled(true)
  val root=FrameLayout(activity)
  val scene=View(activity)
  root.addView(scene,FrameLayout.LayoutParams(-1,-1))
  val dock=MainTabsLayout(activity)
  repeat(3){dock.addView(GlassTabView(activity),android.widget.LinearLayout.LayoutParams(100,72))}
  val wrapper=KyantDockContainer(activity,dock)
  wrapper.addView(dock,FrameLayout.LayoutParams(300,72))
  val host=KyantDockView(activity,dock,scene)
  wrapper.addView(host,FrameLayout.LayoutParams(-1,-1))
  root.addView(wrapper,FrameLayout.LayoutParams(360,72).apply{topMargin=700})
  activity.setContentView(root)
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY))
  root.layout(0,0,360,800)
  val info=ReflectionHelpers.getField<Any>(host,"mAttachInfo")
  val hardware=ReflectionHelpers.getField<Boolean>(info,"mHardwareAccelerated")
  fun available()=ReflectionHelpers.getField<MutableState<Boolean>>(host,"available\$delegate").value
  fun publishComposition(){ReflectionHelpers.getField<MutableState<Boolean>>(host,"ready\$delegate").value=true;host.syncFromNative()}
  fun window(visibility:Int){
   ReflectionHelpers.setField(info,"mWindowVisibility",visibility)
   ReflectionHelpers.callInstanceMethod<Unit>(host,"onWindowVisibilityChanged",ClassParameter.from(Int::class.javaPrimitiveType,visibility))
  }
  try {
   ReflectionHelpers.setField(info,"mHardwareAccelerated",true)
   window(View.VISIBLE)
   assertTrue(available());publishComposition();assertTrue(host.isRendering())
   repeat(3){
    window(View.INVISIBLE);assertFalse(available());assertFalse(host.isRendering())
    assertEquals(View.IMPORTANT_FOR_ACCESSIBILITY_AUTO,dock.importantForAccessibility)
    assertTrue("Backgrounding does not erase the opt-in",KyantDockConfig.enabled())
    window(View.VISIBLE);assertTrue("Window return reactivates the bridge",available())
    assertFalse("Native controls remain until the composition is ready",host.isRendering())
    publishComposition();assertTrue(host.isRendering())
    host.onWindowFocusChanged(true);assertTrue(host.isRendering())
   }
   KyantDockConfig.setEnabled(false);host.syncFromNative();assertFalse(available());assertFalse(host.isRendering())
  } finally {
   ReflectionHelpers.setField(info,"mHardwareAccelerated",hardware)
   KyantDockConfig.setEnabled(false);host.syncFromNative()
   controller.pause().stop().destroy()
  }
 }
}
