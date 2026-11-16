package app.flexygram.kyant;

import android.graphics.*;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;
import org.robolectric.annotation.Config;
import org.robolectric.annotation.GraphicsMode;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;
import static org.junit.Assert.*;

/** Real Skia compilation and uniform validation, not a physical-device performance test. */
@RunWith(RobolectricTestRunner.class)
@Config(sdk=35)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
public class NativeGlassTest {
 @Test public void upstreamProgramCompilesAndAcceptsResizingAndCorners() {
  AndroidUtilities.context = RuntimeEnvironment.getApplication();
  String program = AndroidUtilities.readRes(R.raw.kyant_rounded_rect_refraction);
  assertTrue(program.contains("uniform shader content;"));
  assertFalse(program.contains("refract_index"));
  RenderNode node = new RenderNode("KyantNativeSurfaceProbe");
  KyantGlassEffect effect = new KyantGlassEffect(node);
  effect.update(320,64,32,32,32,32);
  for (int i=0;i<1000;i++) effect.update(320,64,32,32,32,32);
  effect.update(160,46,23,16,0,8);
  effect.update(16,16,500,500,500,500);
  effect.update(0,0,0,0,0,0);
  // A normal Bitmap Canvas must never be used to apply this hardware-only effect.
  assertFalse(new Canvas(Bitmap.createBitmap(32,32,Bitmap.Config.ARGB_8888)).isHardwareAccelerated());
 }
}
