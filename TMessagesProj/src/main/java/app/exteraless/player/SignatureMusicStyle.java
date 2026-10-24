package app.exteraless.player;

/** Pure geometry/palette policy. No playback state, preferences or rendering loop. */
public final class SignatureMusicStyle {
    private SignatureMusicStyle() {}
    public static int surface(boolean dark) { return dark ? 0xff111b24 : 0xfff3f8fc; }
    public static int raised(boolean dark) { return dark ? 0xff22333f : 0xffe2eef6; }
    public static int text(boolean dark) { return dark ? 0xffedf5fa : 0xff152c3e; }
    public static int secondary(boolean dark) { return dark ? 0xffb4c9d6 : 0xff526d80; }
    public static int accent(boolean dark) { return dark ? 0xff77d9f6 : 0xff008acb; }
    public static int border(boolean dark) { return dark ? 0xff425664 : 0xffcddde8; }
    public static float clamp(float value, float low, float high) {
        return Math.max(low, Math.min(Math.max(low, high), value));
    }
    /** Balanced art, shrinking first on short screens; remaining content may scroll. */
    public static int cover(int width, int available, int minimum) {
        return Math.max(minimum, Math.min(Math.round(width * .72f), available));
    }
}
