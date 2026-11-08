"""Rebuild the original geometric Acquill starter mark; optional Pillow dependency."""
from pathlib import Path
from PIL import Image, ImageDraw

root=Path(__file__).resolve().parents[1]/'assets';root.mkdir(exist_ok=True)
svg='<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><rect width="512" height="512" rx="96" fill="#153e35"/><path d="M108 388 227 118h58l119 270h-72l-25-64H201l-25 64Z" fill="#f5f0df"/><path d="m221 269 35-91 35 91Z" fill="#153e35"/><path d="M320 108h77v18h-77zm0 33h55v18h-55z" fill="#d1ad69"/></svg>'
(root/'icon.svg').write_text(svg)
s=4;image=Image.new('RGBA',(512*s,512*s),(0,0,0,0));draw=ImageDraw.Draw(image)
def points(values):return [(x*s,y*s) for x,y in values]
draw.rounded_rectangle((0,0,512*s,512*s),radius=96*s,fill='#153e35')
draw.polygon(points([(108,388),(227,118),(285,118),(404,388),(332,388),(307,324),(201,324),(176,388)]),fill='#f5f0df')
draw.polygon(points([(221,269),(256,178),(291,269)]),fill='#153e35')
draw.rectangle((320*s,108*s,397*s,126*s),fill='#d1ad69')
draw.rectangle((320*s,141*s,375*s,159*s),fill='#d1ad69')
image.resize((512,512),Image.Resampling.LANCZOS).save(root/'icon.png')
