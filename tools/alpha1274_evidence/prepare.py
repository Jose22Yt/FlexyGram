"""Supplemental renderer-only checks against frozen application sources; no APK is built."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);control=Path(__file__).resolve().parent
p=root/'tools/connected_alpha/bubble_visual/BubbleVisualTest.java.in'
s=p.read_text();position=s.rfind('\n}');assert position>0
p.write_text(s[:position]+(control/'outline_method.java.txt').read_text()+s[position:])
# Native View parents clip their children; the direct Canvas fixture must do this explicitly.
p=root/'tools/connected_alpha/header_visual/HeaderVisualTest.java.in'
s=p.read_text();before='canvas.save();canvas.translate(0,i*200);preview.draw(canvas);canvas.restore();'
after='canvas.save();canvas.clipRect(0,i*200,401,(i+1)*200);canvas.translate(0,i*200);preview.draw(canvas);canvas.restore();'
assert before in s;p.write_text(s.replace(before,after))
p=root/'tools/connected_alpha/music_visual/LayoutFixture.java.in';s=p.read_text()
s=s.replace('PlayerColors colors=PlayerColors.fromSeed(0,dark)','PlayerColors colors=PlayerColors.fromSignatureArtwork(0xffb5776a,dark)')
before='titleRow=new LinearLayout(c);titleRow.setOrientation(1);titleRow.addView(text(c,"Alone",24,colors.onSurface));titleRow.addView(text(c,"Marshmello",16,colors.onSurfaceVariant));content.addView(titleRow);'
after='titleRow=new LinearLayout(c);titleRow.setOrientation(0);titleRow.setGravity(Gravity.CENTER_VERTICAL);LinearLayout titles=new LinearLayout(c);titles.setOrientation(1);titles.setPadding(dp(60),0,0,0);TextView title=text(c,"Alone",24,colors.onSurface),artist=text(c,"Marshmello",16,colors.onSurfaceVariant);title.setGravity(Gravity.CENTER_HORIZONTAL);artist.setGravity(Gravity.CENTER_HORIZONTAL);titles.addView(title,new LinearLayout.LayoutParams(-1,-2));titles.addView(artist,new LinearLayout.LayoutParams(-1,-2));titleRow.addView(titles,new LinearLayout.LayoutParams(0,-2,1));MorphButton favorite=new MorphButton(c,PlayerIcon.stroke(PlayerIcon.HEART,24));favorite.setColors(colors.primaryContainer,colors.primary,colors.primaryContainer,colors.primary);titleRow.addView(favorite,LayoutHelper.createLinear(48,48,Gravity.CENTER_VERTICAL,12,0,0,0));content.addView(titleRow);'
assert before in s;p.write_text(s.replace(before,after))
print('Renderer fixture inputs updated; application source and native engines unchanged. Synthetic evidence only.')
