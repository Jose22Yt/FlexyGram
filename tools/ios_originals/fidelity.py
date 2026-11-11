"""Build-time geometry check, using the same renderer for source and converted paths.
Android/iOS GPU antialiasing can differ; this checks paths, holes and clips, not GPU parity.
"""
import xml.etree.ElementTree as ET
A='{http://schemas.android.com/apk/res/android}'


def vector_svg(data):
    root=ET.fromstring(data)
    svg=ET.Element('svg',{'xmlns':'http://www.w3.org/2000/svg','width':root.get(A+'width').removesuffix('dp'),
        'height':root.get(A+'height').removesuffix('dp'),'viewBox':'0 0 '+root.get(A+'viewportWidth')+' '+root.get(A+'viewportHeight')})
    defs=ET.SubElement(svg,'defs');clips=0
    def children(source,parent):
        nonlocal clips
        for node in source:
            if node.tag=='group': children(node,ET.SubElement(parent,'g'))
            elif node.tag=='clip-path':
                clips+=1;ident='clip'+str(clips)
                clip=ET.SubElement(defs,'clipPath',{'id':ident})
                ET.SubElement(clip,'path',{'d':node.get(A+'pathData'),'clip-rule':'evenodd' if node.get(A+'fillType')=='evenOdd' else 'nonzero'})
                parent=ET.SubElement(parent,'g',{'clip-path':'url(#'+ident+')'})
            elif node.tag=='path':
                attrs={'d':node.get(A+'pathData'),'fill-rule':'evenodd' if node.get(A+'fillType')=='evenOdd' else 'nonzero','fill':'none'}
                for original,target in [('fillColor','fill'),('fillAlpha','fill-opacity'),('strokeColor','stroke'),('strokeAlpha','stroke-opacity'),('strokeWidth','stroke-width'),('strokeLineCap','stroke-linecap'),('strokeLineJoin','stroke-linejoin')]:
                    v=node.get(A+original)
                    if v is not None: attrs[target]='#ffffff' if target in ('fill','stroke') else v
                ET.SubElement(parent,'path',attrs)
    children(root,svg)
    return ET.tostring(svg)


def compare(page,data,scale=4):
    import fitz
    from PIL import Image,ImageChops,ImageStat
    svg=fitz.open('svg',vector_svg(data));doc=fitz.open('pdf',svg.convert_to_pdf())
    def alpha(p):
        pix=p.get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=True)
        return Image.frombytes('RGBA',(pix.width,pix.height),pix.samples).getchannel('A')
    source,target=alpha(page),alpha(doc[0])
    if source.size!=target.size:return 255.0,1.0
    diff=ImageChops.difference(source,target);hist=diff.histogram()
    return ImageStat.Stat(diff).mean[0],sum(hist[17:])/(source.width*source.height)
