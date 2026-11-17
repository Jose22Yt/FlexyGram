package app.flexygram.kyant;

/** Pure physical geometry shared by drawing, capture and hit testing. */
public final class KyantDockGeometry {
    private KyantDockGeometry() {}
    public static float panelInset(int height, int paddingTop, int paddingBottom, float panelHeight) {
        // Symmetric native padding is decorative. Only the extra bottom inset is system space.
        int systemBottom = Math.max(0, paddingBottom - paddingTop);
        return (height - systemBottom - panelHeight) / 2f;
    }

    /** Changes to icon pixels must not trigger an unchanged dock layout/composition. */
    public static final class State {
        private float x = Float.NaN, y = Float.NaN;
        private int width = -1, height = -1, top, bottom;
        private boolean rtl, dark;

        public boolean update(float x, float y, int width, int height, int top, int bottom,
                              boolean rtl, boolean dark) {
            if (this.x == x && this.y == y && this.width == width && this.height == height
                    && this.top == top && this.bottom == bottom && this.rtl == rtl && this.dark == dark) return false;
            this.x = x; this.y = y; this.width = width; this.height = height;
            this.top = top; this.bottom = bottom; this.rtl = rtl; this.dark = dark;
            return true;
        }
    }
}
