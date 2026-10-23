#!/usr/bin/env python3
"""Deterministic Android adaptation of the owner's selected original artwork.
Requires Pillow. No network, image generation, recoloring or alternate design.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import hashlib

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).with_name('flexygram-blue-original.png')

def main():
    original = Image.open(SOURCE).convert('RGB')
    alpha = ROOT/'TMessagesProj/src/connectedAlpha/res'
    for density, size in [('mdpi',48),('hdpi',72),('xhdpi',96),('xxhdpi',144),('xxxhdpi',192)]:
        for name in ('ic_launcher_exteraless','ic_launcher_exteraless_round'):
            original.resize((size,size),Image.Resampling.LANCZOS).save(alpha/f'mipmap-{density}/{name}.png')
    original.resize((768,768),Image.Resampling.LANCZOS).save(alpha/'drawable-nodpi/flexygram_launcher_art.png')
    original.resize((512,512),Image.Resampling.LANCZOS).save(ROOT/'TMessagesProj/src/main/res/drawable-nodpi/flexygram_brand.png')
    # Extract the connected paper plane from the owner's actual image; exclude
    # separate pale frame highlights. The adaptive monochrome layer is optional
    # launcher tint artwork, never substituted for the official color icon.
    im=original.resize((384,384),Image.Resampling.LANCZOS);pixels=im.load();remaining=set()
    for y in range(384):
        for x in range(384):
            p=pixels[x,y]
            if min(p)>155 and max(p)-min(p)<100:remaining.add((x,y))
    largest=set()
    while remaining:
        seed=remaining.pop();component={seed};queue=[seed]
        for x,y in queue:
            for pt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if pt in remaining:remaining.remove(pt);component.add(pt);queue.append(pt)
        if len(component)>len(largest):largest=component
    mask=Image.new('RGBA',(384,384),(255,255,255,0))
    for pt in largest:mask.putpixel(pt,(255,255,255,255))
    mask=mask.resize((768,768),Image.Resampling.LANCZOS)
    a=mask.getchannel('A').point(lambda v:255 if v>127 else 0)
    ImageDraw.floodfill(a,(0,0),128);a=a.point(lambda v:0 if v==128 else 255)
    a=a.resize((1536,1536),Image.Resampling.LANCZOS).resize((768,768),Image.Resampling.LANCZOS)
    out=Image.new('RGBA',(768,768),(255,255,255,0));out.putalpha(a)
    out.save(alpha/'drawable-nodpi/flexygram_launcher_mono.png')
    print('Original artwork SHA-256:',hashlib.sha256(SOURCE.read_bytes()).hexdigest())
if __name__=='__main__':main()
