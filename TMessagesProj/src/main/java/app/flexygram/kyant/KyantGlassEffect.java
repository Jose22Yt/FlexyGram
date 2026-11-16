package app.flexygram.kyant;

import android.graphics.RenderEffect;
import android.graphics.RenderNode;
import android.graphics.RuntimeShader;
import androidx.annotation.RequiresApi;
import org.telegram.messenger.AndroidUtilities;
import org.telegram.messenger.R;

/** Native View adapter for Kyant's unchanged rounded-rectangle lens program (Apache 2.0).
 * Shared scene sources supply the blur/vibrancy once; this node applies only the lens.
 * Mutable uniforms belong to the surface. No Compose host, bitmap, ticker or second capture.
 */
@RequiresApi(33)
public final class KyantGlassEffect {
    private static final class Program {
        static final String CODE = AndroidUtilities.readRes(R.raw.kyant_rounded_rect_refraction);
    }
    private final RenderNode node;
    private final RuntimeShader shader = new RuntimeShader(Program.CODE);
    private int width = -1, height = -1;
    private float topLeft, topRight, bottomRight, bottomLeft, refraction;

    public KyantGlassEffect(RenderNode node) { this.node = node; }

    public void update(int width, int height, float tl, float tr, float br, float bl) {
        if (width <= 0 || height <= 0) return;
        float maxRadius = Math.min(width, height) / 2f;
        tl = Math.max(0, Math.min(tl, maxRadius));
        tr = Math.max(0, Math.min(tr, maxRadius));
        br = Math.max(0, Math.min(br, maxRadius));
        bl = Math.max(0, Math.min(bl, maxRadius));
        // Keep the center outside the refraction band even in a small circular button.
        float band = Math.min(AndroidUtilities.dpf2(24f), maxRadius);
        if (this.width == width && this.height == height && topLeft == tl && topRight == tr
                && bottomRight == br && bottomLeft == bl && refraction == band) return;
        this.width = width; this.height = height;
        topLeft = tl; topRight = tr; bottomRight = br; bottomLeft = bl; refraction = band;
        shader.setFloatUniform("size", width, height);
        shader.setFloatUniform("offset", 0f, 0f);
        shader.setFloatUniform("cornerRadii", tl, tr, br, bl);
        shader.setFloatUniform("refractionHeight", band);
        shader.setFloatUniform("refractionAmount", -band);
        shader.setFloatUniform("depthEffect", 0f);
        node.setRenderEffect(RenderEffect.createRuntimeShaderEffect(shader, "content"));
    }
}
