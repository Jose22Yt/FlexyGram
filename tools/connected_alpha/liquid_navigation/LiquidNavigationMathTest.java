/* SPDX-License-Identifier: GPL-3.0-or-later */
import app.flexygram.navigation.LiquidNavigationMath;
/** Android-free policy contract. Device gestures and rendering need separate tests. */
public final class LiquidNavigationMathTest {
    private static int checked;
    static void test(boolean ok,String name) { checked++; if(!ok) throw new AssertionError(name); }
    public static void main(String[] args) {
        test(LiquidNavigationMath.clampPercent(-3)==0,"negative transparency");
        test(LiquidNavigationMath.clampPercent(103)==100,"high transparency");
        test(LiquidNavigationMath.clampTabs(1)==2,"minimum viable tab count");
        test(LiquidNavigationMath.clampTabs(7)==6,"bounded preview count");
        test(LiquidNavigationMath.center(20,50,200)==50,"left bound");
        test(LiquidNavigationMath.center(500,50,200)==200,"right bound");
        test(LiquidNavigationMath.center(101,50,200)==101,"center follows finger");
        test(LiquidNavigationMath.stretch(0,80,.65f)==0,"no motion means no stretch");
        test(LiquidNavigationMath.stretch(800,80,1f)<=.19001f,"stretch stays subtle");
        test(LiquidNavigationMath.width(80,0)==80,"idle keeps native width");
        test(LiquidNavigationMath.width(80,.19f)<96,"stretch bounded");
        test(LiquidNavigationMath.compression(.19f)>.94f,"round shape never collapses");
        for(int i=0;i<400;i++){
            float v=LiquidNavigationMath.stretch(i-200,50,.75f);
            test(v>=0 && v<=.19f,"physical envelope "+i);
        }
        System.out.println("Liquid Navigation policy contracts passed: "+checked);
    }
}
