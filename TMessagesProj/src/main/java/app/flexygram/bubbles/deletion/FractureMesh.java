/* Adapted from Bubble Fracture v1.0 by @larrat23, supplied with this change.
 * Original attribution retained; see CREDITS.md. */

package app.flexygram.bubbles.deletion;
import java.util.*;
public final class FractureMesh {
    public static final class Piece {
        public final float[] xy;
        public final float cx,cy,delay,vx,vy,spin;
        Piece(float[] points,float x,float y,float wait,float dx,float dy,float turn) {
            xy=points;
            cx=x;
            cy=y;
            delay=wait;
            vx=dx;
            vy=dy;
            spin=turn;
        }
    }
    public static List<Piece> make(float w,float h,int count,long seed) {
        if(w<=0||h<=0)throw new IllegalArgumentException("Empty bubble");
        count=Math.max(8,Math.min(60,count));
        Random r=new Random(seed);
        float[][] sites=new float[count][2];
        int columns=Math.max(2,(int)Math.round(Math.sqrt(count*w/h)));
        int rows=(count+columns-1)/columns;
        for(int i=0;i<count;i++) {
            sites[i][0]=w*((i%columns)+.2f+.6f*r.nextFloat())/columns;
            sites[i][1]=h*((i/columns)+.2f+.6f*r.nextFloat())/rows;
        }
        List<Piece> result=new ArrayList<Piece>();
        for(int i=0;i<count;i++) {
            List<float[]> poly=new ArrayList<float[]>();
            poly.add(new float[] {
                0,0
            }
            );
            poly.add(new float[] {
                w,0
            }
            );
            poly.add(new float[] {
                w,h
            }
            );
            poly.add(new float[] {
                0,h
            }
            );
            for(int j=0;j<count&&!poly.isEmpty();j++)if(i!=j) {
                float a=sites[j][0]-sites[i][0],b=sites[j][1]-sites[i][1],c=(sites[j][0]*sites[j][0]+sites[j][1]*sites[j][1]-sites[i][0]*sites[i][0]-sites[i][1]*sites[i][1])/2;
                List<float[]> clipped=new ArrayList<float[]>();
                float[] prev=poly.get(poly.size()-1);
                float pd=a*prev[0]+b*prev[1]-c;
                for(float[] p:poly) {
                    float d=a*p[0]+b*p[1]-c;
                    if((d<=0)!=(pd<=0)) {
                        float t=pd/(pd-d);
                        clipped.add(new float[] {
                            prev[0]+t*(p[0]-prev[0]),prev[1]+t*(p[1]-prev[1])
                        }
                        );
                    }
                    if(d<=0)clipped.add(p);
                    prev=p;
                    pd=d;
                }
                poly=clipped;
            }
            if(poly.size()<3)continue;
            float[] xy=new float[poly.size()*2];
            float x=0,y=0;
            for(int j=0;j<poly.size();j++) {
                xy[j*2]=poly.get(j)[0];
                xy[j*2+1]=poly.get(j)[1];
                x+=xy[j*2];
                y+=xy[j*2+1];
            }
            x/=poly.size();
            y/=poly.size();
            float delay=.06f+.28f*(1-y/h)+.10f*r.nextFloat();
            result.add(new Piece(xy,x,y,delay,(x/w-.5f)*140+(r.nextFloat()-.5f)*90,-30-r.nextFloat()*65,(r.nextFloat()-.5f)*160));
        }
        return result;
    }
    public static float phase(float progress,float delay) {
        return Math.max(0,Math.min(1,(progress-delay)/(1-delay)));
    }
    public static float fade(float progress) {
        float x=Math.max(0,Math.min(1,(progress-.78f)/.22f));
        return 1-x*x*(3-2*x);
    }
}
