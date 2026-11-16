package app.flexygram.kyant;

/** Pure physical geometry shared by drawing, capture and hit testing. */
public final class KyantDockGeometry {
    private KyantDockGeometry() {}
    public static float panelInset(int height, int paddingTop, int paddingBottom, float panelHeight) {
        // Symmetric native padding is decorative. Only the extra bottom inset is system space.
        int systemBottom = Math.max(0, paddingBottom - paddingTop);
        return (height - systemBottom - panelHeight) / 2f;
    }
}
