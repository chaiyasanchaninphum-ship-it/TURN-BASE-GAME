# Cut the front-view full body (leftmost tall figure) out of a character sheet as an RGBA image.
# Background = flat sheet colour; enclosed holes are kept opaque unless they are flat background.
import sys,numpy as np
from PIL import Image
from scipy import ndimage
src,out,H_OUT=sys.argv[1],sys.argv[2],int(sys.argv[3])
im=Image.open(src).convert('RGB');a=np.asarray(im).astype(np.float32);H,W,_=a.shape
# background = most common colour inside the panel (some sheets have a darker frame border)
M=40;q=(a[M:-M,M:-M]//4).astype(int).reshape(-1,3);keys=q[:,0]*4096+q[:,1]*64+q[:,2]
k=np.bincount(keys).argmax();bg=a[M:-M,M:-M].reshape(-1,3)[keys==k].mean(0)
d=np.sqrt(((a-bg)**2).sum(2));mask=d>20
B=int(sys.argv[4]) if len(sys.argv)>4 else 28;mask[:B]=mask[-B:]=False;mask[:,:B]=mask[:,-B:]=False
mask=ndimage.binary_opening(mask,iterations=2)   # drop thin frame lines
lab,n=ndimage.label(ndimage.binary_dilation(mask,iterations=3))
objs=ndimage.find_objects(lab);cand=[(sl[1].start,i+1,sl) for i,sl in enumerate(objs) if (sl[0].stop-sl[0].start)>H*.6]
_,li,sl=min(cand);comp=(lab==li)&ndimage.binary_dilation(mask,iterations=1)
# split a neighbouring figure that touches this one: cut at the thinnest column right of the head
top,bot=sl[0].start,sl[0].stop;fh=bot-top
band=comp[top+int(fh*.06):top+int(fh*.14)].any(0);hc=np.where(band)[0]
run_end=hc[0]
for c in hc[1:]:
    if c-run_end>6: break
    run_end=c
hx=int((hc[0]+run_end)/2)   # leftmost head only (neighbour heads share the same height)
if sl[1].stop-sl[1].start>fh*.62:
    colc=comp.sum(0).astype(float);lo,hi=hx+int(fh*.12),min(W-1,hx+int(fh*.36))
    cut=lo+int(np.argmin(colc[lo:hi]))
    if colc[cut]<fh*.3: comp[:,cut:]=False;print('cut at',cut,'count',int(colc[cut]))
filled=ndimage.binary_fill_holes(comp);holes=filled&~comp
hl,hn=ndimage.label(holes)
for k in range(1,hn+1):
    hm=hl==k
    if (d[hm]<9).mean()>.85 and hm.sum()>60: filled[hm]=False   # genuine background gap (e.g. between arm and body)
core=ndimage.binary_erosion(filled,iterations=2)
soft=np.clip((d-10)/20,0,1)
alpha=np.where(core,1.0,soft*ndimage.binary_dilation(filled,iterations=2))
ys,xs=np.where(alpha>.05);y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
rgba=np.dstack([a,alpha*255]).astype(np.uint8)[y0:y1,x0:x1]
img=Image.fromarray(rgba,'RGBA');w=round(img.width*H_OUT/img.height)
img.resize((w,H_OUT),Image.LANCZOS).save(out)
print(out,(w,H_OUT))
