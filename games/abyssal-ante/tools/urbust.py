# Build 3:4 bust portraits from the front view of a character sheet: key out the flat
# sheet background, crop head-to-chest, composite on an element-coloured glow.
import sys,numpy as np
from PIL import Image,ImageFilter
src,out,c1,c2=sys.argv[1:5]
im=Image.open(src).convert('RGB');a=np.asarray(im).astype(np.float32);H,W,_=a.shape
bg=np.median(np.concatenate([a[:8].reshape(-1,3),a[-8:].reshape(-1,3),a[:,:8].reshape(-1,3)]),axis=0)
d=np.sqrt(((a-bg)**2).sum(2))
mask=d>22
# left figure = the tall connected component whose left edge is nearest the sheet's left side
from scipy import ndimage
lab,n=ndimage.label(ndimage.binary_dilation(mask,iterations=3))
objs=ndimage.find_objects(lab);cand=[(sl[1].start,i+1,sl) for i,sl in enumerate(objs) if (sl[0].stop-sl[0].start)>H*.6]
_,li,sl=min(cand);fig_m=ndimage.binary_dilation(lab==li,iterations=4)
top,bot=sl[0].start,sl[0].stop;fh=bot-top
band=(lab==li)[top+int(fh*.07):top+int(fh*.15)];hx=np.where(band.any(0))[0];hx=(hx.min()+hx.max())/2
bh=int(fh*(float(sys.argv[5]) if len(sys.argv)>5 else .44));bw=int(bh*.75);cy=top-int(bh*.1);cx=int(hx-bw/2)
x0,x1=sl[1].start,sl[1].stop
alpha=np.clip((d-14)/22,0,1)*fig_m
rgba=np.dstack([a,alpha*255]).astype(np.uint8)
fig=Image.fromarray(rgba,'RGBA')
crop=Image.new('RGBA',(bw,bh),(0,0,0,0));crop.paste(fig.crop((cx,cy,cx+bw,cy+bh)),(0,0))
OW,OH=382,512;crop=crop.resize((OW,OH),Image.LANCZOS)
hx2=lambda h:tuple(int(h[i:i+2],16) for i in (1,3,5))
C1,C2=np.array(hx2(c1),float),np.array(hx2(c2),float);base=np.array([5,3,7],float)
yy,xx=np.mgrid[0:OH,0:OW];r=np.sqrt(((xx-OW*.5)/OW)**2+((yy-OH*.32)/OH*1.1)**2)/.75
t=np.clip(r,0,1)[...,None]
col=np.where(t<.55,C2*.55*(1-t/.55)+C1*(t/.55),C1*(1-(t-.55)/.45)+base*((t-.55)/.45))
bgim=Image.fromarray(np.clip(col,0,255).astype(np.uint8),'RGB').convert('RGBA')
glow=crop.split()[3].filter(ImageFilter.GaussianBlur(10));gl=Image.new('RGBA',(OW,OH),hx2(c2)+(0,));gl.putalpha(glow.point(lambda v:int(v*.55)))
outim=Image.alpha_composite(Image.alpha_composite(bgim,gl),crop)
# bottom shade like the painted busts
sh=np.zeros((OH,OW,4),np.uint8);sh[...,3]=(np.clip((yy-OH*.7)/(OH*.3),0,1)*150).astype(np.uint8)
outim=Image.alpha_composite(outim,Image.fromarray(sh,'RGBA'))
outim.convert('RGB').save(out,quality=95)
print(out,'fig',x0,x1,top,bot,'crop',cx,cy,bw,bh)
