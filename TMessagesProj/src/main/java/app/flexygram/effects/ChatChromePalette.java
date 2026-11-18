package app.flexygram.effects;

/** Opaque chat controls stay visible over both AMOLED black and plain white. */
public final class ChatChromePalette {
    private ChatChromePalette() {}

    public static int surface(boolean dark) {
        return dark ? 0xff26272a : 0xfff4f5f7;
    }

    public static int outline(boolean dark) {
        return dark ? 0x30ffffff : 0x26000000;
    }
}
