// Explicit isolated host API; not shipped in the application.
package org.telegram.messenger;
public class AndroidUtilities {
 public static android.content.Context context;
 public static int dp(float value){return (int)Math.ceil(value * context.getResources().getDisplayMetrics().density);}
 public static float dpf2(float dp) { return dp * context.getResources().getDisplayMetrics().density; }
 public static String readRes(int id) {
  try (java.io.InputStream stream = context.getResources().openRawResource(id)) {
   return new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8);
  } catch (java.io.IOException e) { throw new IllegalStateException(e); }
 }
}
