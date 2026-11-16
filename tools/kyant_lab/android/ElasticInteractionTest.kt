package app.flexygram.kyant

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.drawable.GradientDrawable
import android.os.SystemClock
import android.view.MotionEvent
import android.view.View
import android.view.animation.AlphaAnimation
import android.view.animation.Transformation
import android.widget.Button
import android.widget.EditText
import android.widget.FrameLayout
import androidx.activity.ComponentActivity
import app.flexygram.elastic.*
import org.junit.*
import org.junit.Assert.*
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.shadows.ShadowLooper
import org.robolectric.shadows.ShadowSystemClock
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.telegram.messenger.ApplicationLoader
import org.telegram.messenger.LiteMode
import org.telegram.messenger.SharedConfig
import java.time.Duration

@RunWith(RobolectricTestRunner::class)
@Config(sdk=[35],qualifiers="w360dp-h800dp-mdpi")
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class ElasticInteractionTest {
 private val activityController=Robolectric.buildActivity(ComponentActivity::class.java).setup()
 private val activity=activityController.get()
 private val root=FrameLayout(activity)
 private var clicks=0
 private val button=Button(activity).apply { text="Send"; setOnClickListener { clicks++ } }
 @Before fun setup() {
  ApplicationLoader.applicationContext=activity
  org.telegram.messenger.AndroidUtilities.context=activity
  SharedConfig.animations=true;LiteMode.saver=false
  ElasticConfig.setEnabled(true)
  root.addView(button,FrameLayout.LayoutParams(100,56).apply { leftMargin=60;topMargin=140 })
  activity.setContentView(root)
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY))
  root.layout(0,0,360,800)
 }
 @After fun close() { ElasticConfig.setEnabled(false);activityController.pause().stop().destroy() }
 private fun touch(action:Int,x:Float=100f,y:Float=164f) {
  val location=IntArray(2);root.getLocationOnScreen(location)
  val now=SystemClock.uptimeMillis()
  val e=MotionEvent.obtain(0,now,action,x+location[0],y+location[1],0)
  e.offsetLocation(-location[0].toFloat(),-location[1].toFloat())
  ElasticInteraction.observe(root,e)
  root.dispatchTouchEvent(e);e.recycle()
 }
 private fun step(view:View,count:Int) {
  repeat(count) {
   ShadowSystemClock.advanceBy(Duration.ofMillis(16))
   view.animation?.getTransformation(SystemClock.uptimeMillis(),Transformation())
  }
 }
 @Test fun visibleDeformationDoesNotChangeHitMatrixOrLoseNativeClick() {
  touch(MotionEvent.ACTION_DOWN)
  assertNotNull(button.animation)
  step(button,8)
  val t=Transformation();button.animation!!.getTransformation(SystemClock.uptimeMillis(),t)
  val m=FloatArray(9);t.matrix.getValues(m)
  assertTrue("Press deformation is visible",kotlin.math.abs(m[0]-1)>.32f)
  assertEquals(1f,button.scaleX,0f);assertEquals(1f,button.scaleY,0f)
  assertTrue("Native hit matrix stays unchanged",button.matrix.isIdentity)
  touch(MotionEvent.ACTION_UP);ShadowLooper.idleMainLooper()
  assertEquals(1,clicks)
  step(button,100);assertNull(button.animation)
 }
 @Test fun scrollCancellationAndDetachLeaveNoStuckTransformation() {
  touch(MotionEvent.ACTION_DOWN)
  touch(MotionEvent.ACTION_MOVE,100f,250f)
  touch(MotionEvent.ACTION_CANCEL,100f,250f)
  step(button,100);assertNull(button.animation)
  touch(MotionEvent.ACTION_DOWN)
  assertNotNull(button.animation)
  root.removeView(button)
  // Android keeps an animating removed child until the next traversal.
  root.draw(Canvas(Bitmap.createBitmap(360,800,Bitmap.Config.ARGB_8888)))
  assertNull(button.animation)
 }
 @Test fun offPowerSavingAndExistingNativeAnimationAreRespected() {
  ElasticConfig.setEnabled(false);touch(MotionEvent.ACTION_DOWN);assertNull(button.animation)
  touch(MotionEvent.ACTION_UP);ShadowLooper.idleMainLooper();assertEquals(1,clicks)
  ElasticConfig.setEnabled(true);LiteMode.saver=true
  touch(MotionEvent.ACTION_DOWN);assertNull(button.animation);touch(MotionEvent.ACTION_CANCEL)
  LiteMode.saver=false;SharedConfig.animations=false
  touch(MotionEvent.ACTION_DOWN);assertNull(button.animation);touch(MotionEvent.ACTION_CANCEL)
  SharedConfig.animations=true
  val native=AlphaAnimation(.3f,1f).apply { duration=1000 }
  button.startAnimation(native)
  touch(MotionEvent.ACTION_DOWN)
  assertSame("Existing native transition must survive",native,button.animation)
 }
 @Test fun nativeEditFocusAndTextSelectionArePreserved() {
  val field=EditText(activity).apply { setText("Native text") }
  root.addView(field,FrameLayout.LayoutParams(240,64).apply{leftMargin=20;topMargin=240})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,100f,270f);touch(MotionEvent.ACTION_UP,100f,270f);ShadowLooper.idleMainLooper()
  assertTrue(field.hasFocus());field.setSelection(0,6)
  assertEquals(0,field.selectionStart);assertEquals(6,field.selectionEnd)
  assertEquals("Native text",field.text.toString())
 }
 @Test fun localFusionConnectsOnlyTheGapAndDisappearsOnRelease() {
  val group=FrameLayout(activity).apply{setBackgroundColor(0xff121212.toInt());clipChildren=false}
  root.addView(group,FrameLayout.LayoutParams(320,120).apply{leftMargin=20;topMargin=300})
  fun pill(left:Int)=Button(activity).apply{
   background=GradientDrawable().apply{setColor(0xffeeeeee.toInt());cornerRadius=26f}
   setOnClickListener { clicks++ }
   group.addView(this,FrameLayout.LayoutParams(112,52).apply{leftMargin=left;topMargin=30})
  }
  val a=pill(42);val b=pill(166)
  ElasticFusionGroup.bind(group,a,b)
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  fun pixel():Int {val bmp=Bitmap.createBitmap(320,120,Bitmap.Config.ARGB_8888);group.draw(Canvas(bmp));return bmp.getPixel(160,56)}
  val before=pixel()
  touch(MotionEvent.ACTION_DOWN,110f,350f);step(a,8)
  val during=pixel()
  assertNotEquals("Registered surfaces have a visible fluid connector",before,during)
  touch(MotionEvent.ACTION_UP,110f,350f);step(a,100)
  assertEquals("Connector disappears at rest",before,pixel())
 }

 @Test fun scrollingNativeRecyclerViewCancelsElasticPressAndStillScrolls() {
  val list=androidx.recyclerview.widget.RecyclerView(activity)
  list.layoutManager=androidx.recyclerview.widget.LinearLayoutManager(activity)
  list.adapter=object:androidx.recyclerview.widget.RecyclerView.Adapter<androidx.recyclerview.widget.RecyclerView.ViewHolder>() {
   override fun getItemCount()=30
   override fun onCreateViewHolder(parent:android.view.ViewGroup,type:Int):androidx.recyclerview.widget.RecyclerView.ViewHolder {
    val row=Button(activity).apply { layoutParams=androidx.recyclerview.widget.RecyclerView.LayoutParams(-1,64);setOnClickListener { clicks++ } }
    return object:androidx.recyclerview.widget.RecyclerView.ViewHolder(row){}
   }
   override fun onBindViewHolder(holder:androidx.recyclerview.widget.RecyclerView.ViewHolder,pos:Int){(holder.itemView as Button).text="Chat $pos"}
  }
  root.addView(list,FrameLayout.LayoutParams(320,220).apply{leftMargin=20;topMargin=400})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,100f,470f)
  touch(MotionEvent.ACTION_MOVE,100f,430f)
  touch(MotionEvent.ACTION_MOVE,100f,410f)
  touch(MotionEvent.ACTION_UP,100f,410f)
  assertTrue("Native RecyclerView still receives scroll gestures",list.computeVerticalScrollOffset()>0)
  assertEquals("Dragging must not send a click",0,clicks)
 }

 @Test fun productionPreviewUsesRealNeighborSpacingAndVisibleJoining() {
  val preview=ElasticPreviewView(activity)
  root.addView(preview,FrameLayout.LayoutParams(360,132).apply {topMargin=300})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  val left=preview.getChildAt(0);val right=preview.getChildAt(1)
  val gap=right.left-left.right
  assertTrue("Production preview controls must be close enough to merge",gap in 1..17)
  val sampleX=(left.right+right.left)/2;val sampleY=left.top+left.height/2
  fun pixel():Int {val bmp=Bitmap.createBitmap(360,132,Bitmap.Config.ARGB_8888);preview.draw(Canvas(bmp));return bmp.getPixel(sampleX,sampleY)}
  val before=pixel();touch(MotionEvent.ACTION_DOWN,(left.left+left.width/2).toFloat(),(300+sampleY).toFloat());step(left,8)
  assertNotEquals("The actual settings preview shows fusion",before,pixel())
  touch(MotionEvent.ACTION_UP,(left.left+left.width/2).toFloat(),(300+sampleY).toFloat());step(left,100)
  assertEquals(before,pixel())
 }

 @Test fun rapidRetapKeepsSpringStateAndDifferentControlsRecoverTogether() {
  touch(MotionEvent.ACTION_DOWN);step(button,5)
  val animation=button.animation!!
  touch(MotionEvent.ACTION_UP)
  touch(MotionEvent.ACTION_DOWN)
  assertSame("Retap continues the existing spring, without snapping to its start",animation,button.animation)
  touch(MotionEvent.ACTION_UP)
  val second=Button(activity).apply{setOnClickListener {clicks++}}
  root.addView(second,FrameLayout.LayoutParams(100,56).apply{leftMargin=200;topMargin=140})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,240f,164f)
  assertSame("The preceding control keeps recovering smoothly",animation,button.animation)
  assertNotNull(second.animation)
  ElasticConfig.setEnabled(false)
  assertNull(button.animation);assertNull(second.animation)
 }
 @Test fun taggedPillStretchesBackgroundAndIconTogetherWithNativeClick() {
  val pill=FrameLayout(activity).apply {
   background=GradientDrawable().apply{setColor(0xff000000.toInt());cornerRadius=28f}
   setTag(org.telegram.messenger.R.id.flexy_elastic_surface,this)
  }
  val icon=Button(activity).apply{setOnClickListener {clicks++}}
  pill.addView(icon,FrameLayout.LayoutParams(40,40).apply{leftMargin=30;topMargin=8})
  root.addView(pill,FrameLayout.LayoutParams(100,56).apply{leftMargin=60;topMargin=260})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,110f,288f);step(pill,8)
  assertNotNull("The whole material surface owns the deformation",pill.animation)
  assertNull("The icon must not move independently",icon.animation)
  val t=Transformation();pill.animation!!.getTransformation(SystemClock.uptimeMillis(),t)
  val m=FloatArray(9);t.matrix.getValues(m)
  assertTrue("Whole-pill stretch is substantially visible",m[0]>1.16f)
  assertTrue("Its background compresses vertically with the content",m[4]<.87f)
  assertTrue(pill.matrix.isIdentity);assertTrue(icon.matrix.isIdentity)
  touch(MotionEvent.ACTION_UP,110f,288f);ShadowLooper.idleMainLooper()
  assertEquals(1,clicks);step(pill,100);assertNull(pill.animation)
 }

 @Test fun singleIconBackgroundWrapperIsPromotedWithoutAnimatingTheScreen() {
  val pill=FrameLayout(activity).apply {background=GradientDrawable().apply{setColor(0xff000000.toInt());cornerRadius=28f}}
  val icon=Button(activity).apply{setOnClickListener {clicks++}}
  pill.addView(icon,FrameLayout.LayoutParams(40,40).apply{leftMargin=30;topMargin=8})
  root.addView(pill,FrameLayout.LayoutParams(100,56).apply{leftMargin=60;topMargin=260})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,110f,288f)
  assertNotNull(pill.animation);assertNull(icon.animation);assertNull(root.animation)
  touch(MotionEvent.ACTION_UP,110f,288f);ShadowLooper.idleMainLooper();assertEquals(1,clicks)
 }

 @Test fun independentControlsNeverAnimateTheirSharedTaggedBar() {
  val bar=FrameLayout(activity).apply {
   setTag(org.telegram.messenger.R.id.flexy_elastic_surface,this) // A stale beta65 aggregate tag.
   setOnClickListener {clicks+=100}
  }
  val left=Button(activity).apply{setOnClickListener {clicks++}}
  val right=Button(activity).apply{setOnClickListener {clicks+=10}}
  bar.addView(left,FrameLayout.LayoutParams(80,56).apply{leftMargin=0})
  bar.addView(right,FrameLayout.LayoutParams(80,56).apply{leftMargin=120})
  root.addView(bar,FrameLayout.LayoutParams(240,56).apply{leftMargin=40;topMargin=400})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  touch(MotionEvent.ACTION_DOWN,70f,425f);step(left,8)
  assertNotNull(left.animation);assertNull(right.animation);assertNull(bar.animation)
  touch(MotionEvent.ACTION_UP,70f,425f);ShadowLooper.idleMainLooper();assertEquals(1,clicks)
  step(left,100)
  touch(MotionEvent.ACTION_DOWN,145f,425f) // Blank bar gap must not animate the whole panel.
  assertNull(bar.animation);assertNull(left.animation);assertNull(right.animation)
  touch(MotionEvent.ACTION_CANCEL,145f,425f)
 }

 @Test fun retainedControlMaterialAndContentDeformTogetherWhileSiblingPixelsStayUnchanged() {
  val bar=FrameLayout(activity).apply{setBackgroundColor(0xff999999.toInt());clipChildren=false}
  val own=Button(activity).apply{background=null;setOnClickListener{clicks++}}
  val neighbor=Button(activity).apply{background=android.graphics.drawable.ColorDrawable(0xff00ff00.toInt());setOnClickListener{clicks+=10}}
  bar.addView(own,FrameLayout.LayoutParams(80,56).apply{leftMargin=40;topMargin=20})
  bar.addView(neighbor,FrameLayout.LayoutParams(80,56).apply{leftMargin=200;topMargin=20})
  ElasticControlBackground.install(own,GradientDrawable().apply{setColor(0xff000000.toInt());cornerRadius=28f})
  root.addView(bar,FrameLayout.LayoutParams(320,100).apply{leftMargin=20;topMargin=400})
  root.measure(View.MeasureSpec.makeMeasureSpec(360,View.MeasureSpec.EXACTLY),View.MeasureSpec.makeMeasureSpec(800,View.MeasureSpec.EXACTLY));root.layout(0,0,360,800)
  fun pixels():Bitmap {val bmp=Bitmap.createBitmap(320,100,Bitmap.Config.ARGB_8888);bar.draw(Canvas(bmp));return bmp}
  val before=pixels()
  touch(MotionEvent.ACTION_DOWN,100f,445f);step(own,8)
  val during=pixels()
  assertNotEquals("The button background really deforms",before.getPixel(80,24),during.getPixel(80,24))
  for(y in 20..75)for(x in 200..279)assertEquals("Neighbor pixels are stationary",before.getPixel(x,y),during.getPixel(x,y))
  assertNull(neighbor.animation);assertNull(bar.animation)
  touch(MotionEvent.ACTION_UP,100f,445f);ShadowLooper.idleMainLooper();assertEquals(1,clicks)
  step(own,100)
  val restored=pixels();assertEquals(before.getPixel(80,24),restored.getPixel(80,24))
  ElasticConfig.setEnabled(false)
  assertEquals("OFF restores the original transparent control background",0xff999999.toInt(),pixels().getPixel(80,24))
 }

 @Test fun materialWrapperSurvivesThemeRippleReplacementAndPreservesPadding() {
  val view=Button(activity).apply{setPadding(4,6,8,10)}
  ElasticControlBackground.install(view,GradientDrawable().apply{setColor(0xff111111.toInt());cornerRadius=28f})
  val background=view.background
  assertEquals(4,view.paddingLeft);assertEquals(6,view.paddingTop);assertEquals(8,view.paddingRight);assertEquals(10,view.paddingBottom)
  ElasticControlBackground.updateOriginal(view,android.graphics.drawable.ColorDrawable(0x22000000))
  assertSame(background,view.background)
  assertEquals(view,view.getTag(org.telegram.messenger.R.id.flexy_elastic_surface))
  view.background.setVisible(false,false)
  assertFalse(view.background.isVisible)
  view.background.setVisible(true,false)
  assertTrue(view.background.isVisible)
 }

}
