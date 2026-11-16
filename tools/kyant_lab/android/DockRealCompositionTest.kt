package app.flexygram.kyant

import android.view.View
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.lifecycle.Lifecycle
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.util.ReflectionHelpers
import org.telegram.messenger.ApplicationLoader
import org.telegram.ui.MainTabsLayout
import org.telegram.ui.Components.glass.GlassTabView

/** Real composition readiness, never a test assignment to ready. Hardware is a test input. */
@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w360dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class DockRealCompositionTest {
 @get:Rule val compose=createAndroidComposeRule<ComponentActivity>()
 @Test fun realCompositionPublishesAgainAfterPause() {
  lateinit var host:KyantDockView
  lateinit var root:FrameLayout
  lateinit var dock:MainTabsLayout
  lateinit var wrapper:KyantDockContainer
  lateinit var scene:View
  compose.runOnUiThread {
   val activity=compose.activity
   ApplicationLoader.applicationContext=activity.applicationContext
   ReflectionHelpers.setStaticField(KyantDockConfig::class.java,"preferences",null)
   KyantDockConfig.setEnabled(true)
   root=FrameLayout(activity)
   scene=View(activity)
   root.addView(scene,FrameLayout.LayoutParams(-1,-1))
   dock=MainTabsLayout(activity)
   repeat(3){dock.addView(GlassTabView(activity),android.widget.LinearLayout.LayoutParams(100,72))}
   wrapper=KyantDockContainer(activity,dock)
   wrapper.addView(dock,FrameLayout.LayoutParams(300,72))
   host=KyantDockView(activity,dock,scene)
   wrapper.addView(host,FrameLayout.LayoutParams(-1,-1))
   root.addView(wrapper,FrameLayout.LayoutParams(360,72).apply{topMargin=700})
   activity.setContentView(root)
   root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY))
   root.layout(0,0,360,800)
   val info=ReflectionHelpers.getField<Any>(host,"mAttachInfo")
   ReflectionHelpers.setField(info,"mHardwareAccelerated",true)
   host.onHostResume()
   root.viewTreeObserver.dispatchOnPreDraw()
  }
  compose.waitForIdle()
  compose.runOnIdle {assertTrue("Initial real composition publishes readiness",host.isRendering())}
  repeat(3){
   compose.runOnUiThread {host.onHostPause();assertFalse(host.hasComposition);dock.alpha=0f}
   compose.runOnUiThread {host.onHostResume();root.viewTreeObserver.dispatchOnPreDraw()}
   compose.runOnUiThread {
    assertFalse("The first foreground draw can precede the native bar reveal",host.hasComposition)
    dock.alpha=1f
    // MainTabsActivity.checkUi_tabsPosition publishes the animation factor without relayout.
    host.syncFromNative()
    root.viewTreeObserver.dispatchOnPreDraw()
   }
   compose.waitForIdle()
   compose.runOnIdle {assertTrue("A recreated real composition publishes readiness",host.isRendering())}
  }
  // Match MainTabsActivity: detach the entire optional host across actual Activity stop/start.
  repeat(3){
   compose.runOnUiThread {
    host.onHostPause();wrapper.removeView(host)
    assertFalse(host.isAttachedToWindow);assertFalse(host.hasComposition)
   }
   compose.activityRule.scenario.moveToState(Lifecycle.State.CREATED)
   compose.activityRule.scenario.moveToState(Lifecycle.State.RESUMED)
   compose.runOnUiThread {
    assertTrue("The opt-in remains stored across a real Activity stop",KyantDockConfig.enabled())
    host=KyantDockView(compose.activity,dock,scene)
    wrapper.addView(host,FrameLayout.LayoutParams(-1,-1))
    root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY))
    root.layout(0,0,360,800)
    val info=ReflectionHelpers.getField<Any>(host,"mAttachInfo")
    ReflectionHelpers.setField(info,"mHardwareAccelerated",true)
    host.onHostResume();root.viewTreeObserver.dispatchOnPreDraw()
   }
   compose.waitForIdle()
   compose.runOnIdle {assertTrue("The replacement optical view really composes after Activity stop/start",host.isRendering())}
  }
  compose.runOnUiThread {host.onHostPause();wrapper.removeView(host);KyantDockConfig.setEnabled(false)}
 }
}
