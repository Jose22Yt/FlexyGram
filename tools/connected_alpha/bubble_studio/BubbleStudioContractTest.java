/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.bubbles.interaction.BubbleStickerSpec;
import app.flexygram.bubbles.interaction.BubbleTouchPolicy;

public final class BubbleStudioContractTest {
    private static int cases;
    private static void yes(boolean ok, String name) {
        cases++;
        if (!ok) throw new AssertionError(name);
    }
    private static void throwsInvalid(Runnable r, String why) {
        try { r.run(); throw new AssertionError("Should fail: " + why); }
        catch (IllegalArgumentException expected) { cases++; }
    }
    public static void main(String[] args) {
        yes(BubbleTouchPolicy.mayAnimate(true,true,true,false,false,false),"plain bubble");
        yes(!BubbleTouchPolicy.mayAnimate(true,true,true,true,false,false),"native links own clicks");
        yes(!BubbleTouchPolicy.mayAnimate(true,true,false,false,false,false),"outside bubble");
        yes(!BubbleTouchPolicy.mayAnimate(true,true,true,false,true,false),"selection");
        yes(!BubbleTouchPolicy.mayAnimate(true,true,true,false,false,true),"preview modal");
        yes(!BubbleTouchPolicy.mayAnimate(false,true,true,false,false,false),"disabled");
        yes(BubbleTouchPolicy.mayConvertToSticker(true,true,false,false,false,true,true),"eligible");
        yes(!BubbleTouchPolicy.mayConvertToSticker(true,true,true,false,false,true,true),"protected");
        yes(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,true,false,true,true),"ttl");
        yes(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,false,true,true,true),"spoiler");
        yes(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,false,false,false,true),"not supported");
        yes(!BubbleTouchPolicy.mayConvertToSticker(true,true,false,false,false,true,false),"cannot send");
        app.flexygram.bubbles.interaction.BubbleTapGestureState state =
                new app.flexygram.bubbles.interaction.BubbleTapGestureState();
        state.down(10, 10, 8, true);
        yes(state.isPressed(), "bubble down");
        yes(!state.move(13, 12), "small movement still press");
        yes(state.up(true), "one genuine tap");
        state.down(10, 10, 8, true);
        yes(state.move(100, 10), "scroll cancels press");
        yes(!state.up(true), "scroll no bubble click");
        state.down(10, 10, 8, true);
        state.longPress();
        yes(!state.up(true), "long press not simple tap");
        state.down(10, 10, 8, true);
        yes(!state.up(false), "native click veto respected");
        state.down(10, 10, 8, true);
        state.cancel();
        yes(!state.up(true), "cancelled native stream");
        int[] square = BubbleStickerSpec.dimensions(120,120);
        yes(square[0]==512&&square[1]==512,"square");
        int[] wide = BubbleStickerSpec.dimensions(360,180);
        yes(wide[0]==512&&wide[1]==256,"wide");
        int[] tall = BubbleStickerSpec.dimensions(180,360);
        yes(tall[0]==256&&tall[1]==512,"tall");
        throwsInvalid(()->BubbleStickerSpec.dimensions(0,100),"zero");
        throwsInvalid(()->BubbleStickerSpec.dimensions(100,0),"zero height");
        throwsInvalid(()->BubbleStickerSpec.dimensions(1000,100),"extreme aspect ratio");
        throwsInvalid(()->BubbleStickerSpec.dimensions(5000,20),"huge");
        byte[] webp = {'R','I','F','F',0,0,0,0,'W','E','B','P',0,0,0,0};
        yes(BubbleStickerSpec.isWebp(webp),"webp container");
        yes(!BubbleStickerSpec.isWebp(new byte[]{'P','N','G'}),"not png");
        yes(!BubbleStickerSpec.isWebp(new byte[0]),"not empty");
        yes(!BubbleStickerSpec.isWebp(new byte[BubbleStickerSpec.MAX_BYTES + 1]),"oversize");
        System.out.println("Bubble Studio contracts: " + cases + " passed.");
    }
}
