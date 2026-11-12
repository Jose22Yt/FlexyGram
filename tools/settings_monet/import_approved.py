"""Import the reviewed PNGs and lossless two-channel coverage data. No redraw/resampling."""
from pathlib import Path
from PIL import Image
import numpy as np,json,zipfile,io
ROOT=Path(__file__).resolve().parents[2]
archive=ROOT/'tools/settings_monet/sources/approved-icons.zip'
res=ROOT/'TMessagesProj/src/main/res';data=[]
(res/'drawable-nodpi').mkdir(exist_ok=True);(res/'raw').mkdir(exist_ok=True)
with zipfile.ZipFile(archive) as z:
 prefix='FlexyGram_Duotono_Monet_Bordes_Pulidos/'
 for name in sorted(n for n in z.namelist() if n.startswith(prefix+'android/res/drawable-nodpi/') and n.endswith('.png')):
  filename=Path(name).name;stem=Path(name).stem
  rgb=z.read(name);(res/'drawable-nodpi'/filename).write_bytes(rgb)
  original=np.array(Image.open(io.BytesIO(rgb)).convert('RGBA'))
  body=np.array(Image.open(io.BytesIO(z.read(prefix+'capas_tema/cuerpo/'+filename))))[:,:,3]
  accent=np.array(Image.open(io.BytesIO(z.read(prefix+'capas_tema/acento/'+filename))))[:,:,3]
  assert np.array_equal(body.astype(int)+accent,original[:,:,3])
  yy,xx=np.where(original[:,:,3]>0);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1))
  x0,y0,x1,y1=box
  packed=np.stack((body,accent,original[:,:,3]),axis=2)[y0:y1,x0:x1]
  Image.fromarray(packed,'RGB').save(res/'raw'/f'{stem}_coverage.png',optimize=True)
  data.append({'drawable':stem,'coverage':stem+'_coverage','bounds':box,'size':[x1-x0,y1-y0]})
(ROOT/'tools/settings_monet/approved_assets.json').write_text(json.dumps(data,indent=2)+'\n')
print(f'Imported {len(data)} reviewed icons; exact original PNG bytes and coverage sums verified.')
