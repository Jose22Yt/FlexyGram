#!/usr/bin/env python3
"""Import original Telegram-iOS template glyphs at their point dimensions.

--sources: regenerate Android vectors/rasters from frozen upstream (build tools only).
No flag: regenerate the small runtime alias map from committed provenance metadata.
--check: verify all packaged/source hashes and that generated map is up to date.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, pathlib, re, shutil, sys
import xml.etree.ElementTree as ET
from aliases import GROUPS
from catalog import COMMIT, SOURCES, EXTRA, PLAYER, PREVIEW, TABS
from fidelity import compare

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
RES = ROOT/'TMessagesProj/src/main/res'
JAVA = ROOT/'TMessagesProj/src/main/java/app/flexygram/icons'
A = '{http://schemas.android.com/apk/res/android}'
ET.register_namespace('android', A[1:-1])


def digest(data): return hashlib.sha256(data).hexdigest()
def git_blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def number(v): return format(float(v), '.10g')
def resource_name(key): return 'fg_ios_original_'+re.sub('[^a-z0-9]+','_',key.lower().replace('@animation:','animation_')).strip('_')
def snake(text): return re.sub(r'(?<=[a-z0-9])(?=[A-Z])','_',text).lower()


def build_bindings(keys):
    names = {p.stem for p in RES.glob('drawable*/*') if p.is_file()}
    base = {n:SOURCES[k] for k,g in GROUPS.items() if k in SOURCES for n in g.split()}
    # Exact action names only. These are menu actions, never substring guesses for photo tools etc.
    for key in sorted(keys):
        if key.startswith('Chat/Context Menu/'):
            n = snake(key.rsplit('/',1)[1])
            for prefix in ['msg_', 'menu_']:
                base.setdefault(prefix+n,key)
    for key, group in EXTRA.items():
        for name in group.split(): base[name]=key
    # Distinct states must not collapse (read/unread, pin/unpin, repeat one/all).
    dimensions = json.loads((ROOT/'tools/cupertino/mapping.json').read_text())
    result = {}
    for name in sorted(names):
        if name.startswith('fg_ios_'): continue  # Packaged assets terminate lookup, without recursion.
        canonical = re.sub(r'_(remix|solar)$','',name)
        key = base.get(canonical)
        if key is None: continue
        legacy = dimensions.get(name,{})
        result[name] = {'key':key,'asset':resource_name(key), 'color':legacy.get('color',0xff000000),
                        'mirrored':legacy.get('mirrored',False)}
    return result


def pdf_path(items, closed):
    out=[];current=None
    def pt(p): return number(p.x)+','+number(p.y)
    def begin(p):
        nonlocal current
        if current is None or abs(current.x-p.x)>1e-6 or abs(current.y-p.y)>1e-6:
            out.append('M'+pt(p))
        current=p
    for item in items:
        kind=item[0]
        if kind=='l':
            begin(item[1]);out.append('L'+pt(item[2]));current=item[2]
        elif kind=='c':
            begin(item[1]);out.append('C'+' '.join(pt(p) for p in item[2:]));current=item[-1]
        elif kind=='re':
            r=item[1];points=[r.tl,r.tr,r.br,r.bl] if item[2]==1 else [r.tl,r.bl,r.br,r.tr]
            out.append('M'+pt(points[0])+''.join('L'+pt(p) for p in points[1:])+'Z');current=None
        elif kind=='qu':
            q=item[1];points=[q.ul,q.ur,q.lr,q.ll]
            out.append('M'+pt(points[0])+''.join('L'+pt(p) for p in points[1:])+'Z');current=None
        else: raise ValueError('Unsupported PDF primitive '+kind)
    if closed: out.append('Z')
    return ' '.join(out)


def vector_from_pdf(page, width, height):
    # Shading, text, raster images or nontrivial transparency groups use a faithful
    # build-time raster instead of silently dropping content or retracing contours.
    if any(t not in ('fill-path','stroke-path','ignore-text') for t,*_ in page.get_bboxlog()):
        raise ValueError('PDF uses shading/text/raster')
    root=ET.Element('vector',{A+'width':number(width)+'dp',A+'height':number(height)+'dp',
        A+'viewportWidth':number(width),A+'viewportHeight':number(height)})
    page_group=ET.SubElement(root,'group')
    ET.SubElement(page_group,'clip-path',{A+'pathData':f'M0,0 H{number(width)} V{number(height)} H0 Z'})
    stack=[(0,page_group)]
    for d in page.get_drawings(extended=True):
        level=d.get('level',0)
        while len(stack)>1 and stack[-1][0]>level: stack.pop()
        parent=stack[-1][1]
        if d['type']=='group':
            if d.get('opacity',1)!=1 or d.get('blendmode','Normal')!='Normal': raise ValueError('PDF transparency group')
            stack.append((level+1,ET.SubElement(parent,'group')));continue
        data=pdf_path(d['items'],d.get('closePath'))
        if d['type']=='clip':
            group=ET.SubElement(parent,'group')
            ET.SubElement(group,'clip-path',{A+'pathData':data,A+'fillType':'evenOdd' if d.get('even_odd') else 'nonZero'})
            stack.append((level+1,group));continue
        attrs={A+'pathData':data,A+'fillType':'evenOdd' if d.get('even_odd') else 'nonZero'}
        if d['type'] in ('f','fs'):
            attrs[A+'fillColor']='#FFFFFFFF';attrs[A+'fillAlpha']=number(d.get('fill_opacity',1))
        if d['type'] in ('s','fs'):
            if d.get('dashes') not in (None,'[] 0','[] 0.0'): raise ValueError('PDF dashed stroke')
            caps=d.get('lineCap',(0,0,0))
            if len(set(caps))>1: raise ValueError('Different PDF cap types')
            attrs.update({A+'strokeColor':'#FFFFFFFF',A+'strokeWidth':number(d['width']),
                A+'strokeAlpha':number(d.get('stroke_opacity',1)),
                A+'strokeLineCap':('butt','round','square')[caps[0]],
                A+'strokeLineJoin':('miter','round','bevel')[int(d.get('lineJoin',0))]})
        ET.SubElement(parent,'path',attrs)
    return ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n'


def import_sources(repo):
    import fitz
    from PIL import Image
    from rlottie_python import LottieAnimation
    import subprocess
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    if head!=COMMIT: raise SystemExit('Expected immutable upstream commit '+COMMIT+', got '+head)
    tree=subprocess.check_output(['git','ls-tree','-rz','--full-tree','HEAD'],cwd=repo)
    upstream_blobs={entry.split(b'\t',1)[1].decode():entry.split(b'\t',1)[0].split()[2].decode()
                    for entry in tree.split(b'\0') if b' blob 'in entry}
    upstream=repo/'submodules/TelegramUI/Images.xcassets'
    # Only explicit action bindings are packaged; illustrations and launcher identities are excluded.
    keys={str(p.relative_to(upstream)).removesuffix('.imageset') for p in upstream.rglob('*.imageset')}
    bindings=build_bindings(keys)
    used=sorted({v['key'] for v in bindings.values()} | set(PLAYER.values()) | set(PREVIEW) | set(TABS.values()) | {'Navigation/Back','Navigation/Close'})
    missing=[key for key in used if (not key.startswith('@animation:') and key not in keys)
             or (key.startswith('@animation:') and not (repo/'submodules/TelegramUI/Resources/Animations'/key.split(':',1)[1]).is_file())]
    if missing: raise SystemExit('Missing original sources: '+', '.join(missing))
    for p in RES.glob('drawable*/fg_ios_original_*'): p.unlink()
    old=HERE/'upstream'
    if old.exists(): shutil.rmtree(old)
    records=[]
    for key in used:
        name=resource_name(key);docs=[];images=[];frame=None
        if key.startswith('@animation:'):
            source=repo/'submodules/TelegramUI/Resources/Animations'/key.split(':',1)[1]
            obj=json.loads(source.read_bytes());w,h=obj['w'],obj['h']
            animation=LottieAnimation.from_file(str(source));frame=min(animation.lottie_animation_get_totalframe()-1,int(obj['op']-obj.get('ip',0))-1)
            for density,scale in [('mdpi',1),('hdpi',1.5),('xhdpi',2),('xxhdpi',3),('xxxhdpi',4)]:
                image=animation.render_pillow_frame(frame,width=round(w*scale),height=round(h*scale)).convert('RGBA')
                images.append((density,image))
            kind='original-lottie-final-frame'
        else:
            directory=upstream/(key+'.imageset')
            if not directory.is_dir(): raise SystemExit('Missing original asset: '+key)
            spec=json.loads((directory/'Contents.json').read_text())
            files=[(directory/a['filename'],a.get('scale')) for a in spec['images'] if 'filename' in a]
            if not files: raise SystemExit('No source artwork: '+key)
            source,scale=next(((p,s) for p,s in files if p.suffix in ('.pdf','.svg')),max(files,key=lambda a:float((a[1] or '1x')[:-1])))
            docs.append(directory/'Contents.json')
            if source.suffix in ('.pdf','.svg'):
                opened=fitz.open(source)
                if source.suffix=='.svg': opened=fitz.open('pdf',opened.convert_to_pdf())
                page=opened[0];w,h=page.rect.width,page.rect.height
                try:
                    data=vector_from_pdf(page,w,h)
                    error,coverage=compare(page,data)
                    if error>0.5 or coverage>0.005: raise ValueError('Geometry validation requires original raster')
                    target=RES/'drawable'/(name+'.xml');target.write_bytes(data);kind='original-'+source.suffix[1:]+'-paths'
                except ValueError:
                    kind='original-'+source.suffix[1:]+'-raster'
                    for density,s in [('mdpi',1),('hdpi',1.5),('xhdpi',2),('xxhdpi',3),('xxxhdpi',4)]:
                        pix=page.get_pixmap(matrix=fitz.Matrix(s,s),alpha=True)
                        images.append((density,Image.frombytes('RGBA',[pix.width,pix.height],pix.samples)))
            else:
                image=Image.open(source).convert('RGBA');scale=float((scale or '1x')[:-1]);w,h=image.width/scale,image.height/scale
                # Use upstream scale variants unchanged in resolution; Android handles density.
                for p,s in files:
                    factor=float((s or '1x')[:-1]);density={1:'mdpi',2:'xhdpi',3:'xxhdpi'}.get(factor)
                    if density: images.append((density,Image.open(p).convert('RGBA')));docs.append(p)
                kind='original-png-template'
        outputs=[]
        if images:
            for density,image in images:
                # Native UIImage template semantics use the source alpha, with the app's tint.
                # White RGB also supports Android's existing MULTIPLY controls without darkening.
                white=Image.new('RGBA',image.size,(255,255,255,0));white.putalpha(image.getchannel('A'))
                target=RES/('drawable-'+density)/(name+'.png');white.save(target,optimize=True)
                outputs.append({'path':str(target.relative_to(ROOT)),'sha256':digest(target.read_bytes())})
        else: outputs.append({'path':str(target.relative_to(ROOT)),'sha256':digest(target.read_bytes())})
        docs.append(source);originals=[]
        for src in sorted(set(docs)):
            rel=src.relative_to(repo);raw=src.read_bytes()
            if git_blob(raw)!=upstream_blobs.get(str(rel)): raise SystemExit('Modified upstream source: '+str(rel))
            dest=HERE/'upstream'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest)
            originals.append({'path':str(dest.relative_to(ROOT)),'upstream_path':str(rel),'sha256':digest(raw),'git_blob':git_blob(raw)})
        records.append({'key':key,'asset':name,'width_dp':w,'height_dp':h,'kind':kind,'frame':frame,'template':True,'sources':originals,'outputs':outputs})
    manifest={'repository':'TelegramMessenger/Telegram-iOS','commit':COMMIT,'renderers':{'pymupdf':fitz.VersionBind,'rlottie-python':'1.3.8'},'assets':records}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n')
    for file in ['LICENSE','README.md']:
        if (repo/file).exists(): shutil.copyfile(repo/file,HERE/('UPSTREAM-'+file))
    return bindings


def outputs():
    manifest=json.loads((HERE/'manifest.json').read_text());known={a['key'] for a in manifest['assets']}
    bindings=build_bindings(known)
    # Generating with committed keys must give exactly the audited action catalog.
    if not {b['key'] for b in bindings.values()}<=known: raise SystemExit('Alias without audited asset')
    rows=['// Generated by tools/ios_originals/generate.py from original Telegram-iOS artwork.',
        'package app.flexygram.icons;','import org.telegram.messenger.R;','final class ExactIconMap {',
        ' private ExactIconMap() {}',' static final class Entry {',
        '  final int id, asset, color; final boolean mirrored;',
        '  Entry(int i,int a,int c,boolean m){id=i;asset=a;color=c;mirrored=m;}',' }',
        ' private static final class Holder {static final Entry[] DATA=build();}',
        ' static Entry get(int id){if(id<=0)return null;Entry[] data=Holder.DATA;int lo=0,hi=data.length-1;',
        '  while(lo<=hi){int mid=(lo+hi)>>>1,key=data[mid].id;if(key<id)lo=mid+1;else if(key>id)hi=mid-1;else return data[mid];}return null;}',
        ' private static Entry[] build(){Entry[] data={']
    for name,b in bindings.items(): rows.append(f'  new Entry(R.drawable.{name},R.drawable.{b["asset"]},0x{b["color"]:08x},{str(b["mirrored"]).lower()}),')
    rows += [' };java.util.Arrays.sort(data,(a,b)->Integer.compare(a.id,b.id));return data;}','}']
    constants=['// Generated original source IDs, used by direct-drawing controls too.','package app.flexygram.icons;','import org.telegram.messenger.R;','public final class IosOriginalAssets {',' private IosOriginalAssets() {}']
    for name,key in PLAYER.items():constants.append(f' public static final int {name}=R.drawable.{resource_name(key)};')
    for name,key in TABS.items():constants.append(f' public static final int TAB_{name}=R.drawable.{resource_name(key)};')
    constants.append(' public static final int[] PREVIEW={0,'+','.join('R.drawable.'+resource_name(key)for key in PREVIEW)+'};')
    constants += [f' public static final int BACK=R.drawable.{resource_name("Navigation/Back")};','}']
    return {JAVA/'ExactIconMap.java':'\n'.join(rows)+'\n',JAVA/'IosOriginalAssets.java':'\n'.join(constants)+'\n',
            ROOT/'tools/exact_icons/mapping.json':json.dumps(bindings,indent=2)+'\n',
            HERE/'coverage.json':json.dumps({'original_assets':len(manifest['assets']),
                'mapped_aliases':len(bindings),'native_tab_roles':len(TABS),'native_preview_roles':len(PREVIEW),
                'legacy_catalog':'tools/cupertino/mapping.json',
                'legacy_aliases_not_replaced':sorted(set(json.loads((ROOT/'tools/cupertino/mapping.json').read_text()))-set(bindings)),
                'note':'Unreplaced aliases retain their existing Android/app artwork. No iOS counterpart is invented; this is not a claim of complete iOS 27 coverage.'},indent=2)+'\n'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--sources',type=pathlib.Path);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    if args.sources:import_sources(args.sources.resolve())
    for path,text in outputs().items():
        if args.check:
            if path.read_text()!=text:raise SystemExit('Stale generated file: '+str(path))
        else:path.write_text(text)
    if args.check:
        manifest=json.loads((HERE/'manifest.json').read_text())
        for asset in manifest['assets']:
            for file in asset['sources']+asset['outputs']:
                if digest((ROOT/file['path']).read_bytes())!=file['sha256']:raise SystemExit('Modified artwork: '+file['path'])
    print('Original assets:',len(json.loads((HERE/'manifest.json').read_text())['assets']),'aliases:',len(json.loads((ROOT/'tools/exact_icons/mapping.json').read_text())))

if __name__=='__main__':main()
