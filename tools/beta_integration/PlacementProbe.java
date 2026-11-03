import app.flexygram.bubbles.interaction.ContextPreviewPlacement;
public final class PlacementProbe {
    static int checks;
    static void require(boolean value,String why){checks++;if(!value)throw new AssertionError(why);}
    public static void main(String[] args) {
        for(int usable:new int[]{240,360,640,900,1400}) {
            for(int chrome:new int[]{120,180,220}) {
                for(int height:new int[]{24,60,200,650,2000,10000}) {
                    for(int top:new int[]{-1000,0,30,200,800,4000}) {
                        var p=ContextPreviewPlacement.fit(top,height,32,32+usable,chrome,64,8);
                        require(p.popupY>=32,"above safe top");
                        require(p.popupY+Math.min(usable,chrome+p.gapHeight)<=32+usable,"below safe bottom");
                        require(p.scale>0f&&p.scale<=1,"bounded complete-preview scale");
                        require(Float.isFinite(p.offsetY)&&Float.isFinite(p.scrollRange),"finite geometry");
                        float positioned=top+height*(1-p.scale)*.5f+p.offsetY;
                        require(Math.abs(positioned-(p.popupY+64+8))<.02f,"exact source-to-gap placement");
                        require(p.scrollRange>=0,"scroll range");
                    }
                }
            }
        }
        var large=ContextPreviewPlacement.fit(800,4000,32,700,250,64,8);
        require(large.scrollRange<.01f && large.scale<.72f,"large messages fit completely");
        for(float target:new float[]{1f,.72f,.1f,.001f})
            for(float phase:new float[]{-.2f,0,.5f,1f,1.2f})
                for(float spring:new float[]{-.1f,.95f,1f,1.2f}) {
                    float scale=ContextPreviewPlacement.animatedScale(target,phase,spring);
                    require(scale>0f && Float.isFinite(scale),"spring never mirrors a tall preview");
                    if(target<1f) require(scale<=1f,"fitted spring stays within bounds");
                }
        System.out.println("PlacementProbe PASS: "+checks+" assertions (host geometry, no physical FPS)");
    }
}
