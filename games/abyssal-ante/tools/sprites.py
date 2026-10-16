# Clean 8x5 hero sprite sheets (256x320 cells; rows idle/attack/hit/ultimate/death):
# drop fragments that spill in from neighbouring cells, replace broken frames with the nearest good one,
# despill the green chroma fringe, downscale, and record per-hero anchors (head/feet/centre) for the stage.
import sys,os,glob,json,numpy as np
from PIL import Image
from scipy import ndimage
SRC=sys.argv[1:-2];OUT=sys.argv[-2];SCALE=float(sys.argv[-1])
CW,CH,COLS,ROWS=256,320,8,5;ROWN=['idle','attack','hit','ult','death']
os.makedirs(OUT,exist_ok=True);meta={}
def segments(prof,gap=5):
    xs=np.where(prof>0)[0];segs=[]
    if not len(xs): return segs
    st=pv=xs[0]
    for x in xs[1:]:
        if x-pv>gap: segs.append((st,pv+1));st=x
        pv=x
    segs.append((st,pv+1));return segs
def realign(a,hid):
    # Rows whose 8 characters drift off the 256px grid are re-sliced: find the character blobs,
    # fit centre = o + i*p, and copy a p-wide window around each fitted centre into its cell.
    W=a.shape[1];res=a.copy()
    for r in range(ROWS):
        band=a[r*CH:(r+1)*CH];prof=(band[...,3]>40).sum(0)
        segs=segments(prof);mass=[prof[s0:s1].sum() for s0,s1 in segs]
        if not segs: continue
        top=sorted(mass,reverse=True)[:8];thr=.25*np.median(top)
        big=[(s0,s1) for (s0,s1),m in zip(segs,mass) if m>=thr and s1-s0>=30]
        if len(big)!=8: report.append(f'{hid} row{r}: {len(big)} blobs, grid kept');continue
        cen=np.array([(np.arange(s0,s1)*prof[s0:s1]).sum()/prof[s0:s1].sum() for s0,s1 in big])
        if all(abs(cen[i]-(i*CW+CW/2))<64 and big[i][0]>=i*CW-4 and big[i][1]<=(i+1)*CW+4 for i in range(8)): continue
        i=np.arange(8);p,o=np.polyfit(i,cen,1)
        for k in range(8):
            c=o+k*p;x0=int(round(c-p/2));x1=int(round(c+p/2));cell=np.zeros((CH,CW,4),np.float32)
            sx0,sx1=max(0,x0),min(W,x1);dx=int(round(CW/2-(c-sx0)))
            dx0=max(0,dx);sx0+=dx0-dx;w=min(sx1-sx0,CW-dx0)
            if w>0: cell[:,dx0:dx0+w]=band[:,sx0:sx0+w]
            res[r*CH:(r+1)*CH,k*CW:(k+1)*CW]=cell
        report.append(f'{hid} row{r}: realigned pitch {p:.0f} offset {o:.0f}')
    return res
report=[]
files={};[files.setdefault(os.path.basename(f).split('_')[2],f) for f in SRC]
for hid,f in sorted(files.items()):
    a=np.asarray(Image.open(f).convert('RGBA')).astype(np.float32)
    out=np.zeros_like(a);info=[[None]*COLS for _ in range(ROWS)]
    # some sheets clip every cell to an inner box (e.g. x 21..234): find it from edges shared by many cells
    ex0,ex1=[],[]
    for r in range(ROWS):
        for c in range(COLS):
            xs_=np.where((a[r*CH:(r+1)*CH,c*CW:(c+1)*CW,3]>40).any(0))[0]
            if len(xs_): ex0.append(int(xs_[0]));ex1.append(int(xs_[-1]))
    v0,n0=np.unique(ex0,return_counts=True);v1,n1=np.unique(ex1,return_counts=True)
    clipL=int(v0[n0.argmax()]) if n0.max()>=8 and v0[n0.argmax()]>2 else -99
    clipR=int(v1[n1.argmax()]) if n1.max()>=8 and v1[n1.argmax()]<CW-3 else 999
    for r in range(ROWS):
        for c in range(COLS):
            cell=a[r*CH:(r+1)*CH,c*CW:(c+1)*CW].copy();m=cell[...,3]>40
            lab,n=ndimage.label(ndimage.binary_dilation(m,iterations=2),structure=np.ones((3,3)))
            if n==0: info[r][c]=dict(area=0,edge=True,spill=0,frag=0,cut=True,feet=CW/2);continue
            areas=ndimage.sum(m,lab,range(1,n+1));main=int(np.argmax(areas))+1
            keep=np.zeros_like(m);spill=0.0;frag=0
            def hardcut(k,sl):
                # touches the sheet's inner clip box = a piece sliced out of a neighbouring frame
                return sl[1].start<=clipL+1 or sl[1].stop-1>=clipR-1
            for k,sl in enumerate(ndimage.find_objects(lab),start=1):
                ys,xs=sl;touch=ys.start==0 or xs.start==0 or ys.stop>=CH or xs.stop>=CW
                stray=xs.stop<=CW*.2 or ys.stop<=CH*.2 or (ys.stop<=CH*.3 and (ys.stop-ys.start)<CH*.1)   # leftovers of the previous frame / the row above
                if k==main: keep|=lab==k
                elif hardcut(k,sl): frag+=areas[k-1]>=.15*areas[main-1];spill+=areas[k-1]
                elif not touch and not stray and areas[k-1]>=25: keep|=lab==k
                else: spill+=areas[k-1] if touch else 0
            maincut=False
            cell[...,3]*=keep
            mm=lab==main;ys,xs=np.where(mm)
            info[r][c]=dict(spill=spill,frag=frag,cut=bool(maincut),feet=float(xs[ys>=ys.max()-CH*.12].mean()),area=float(areas[main-1]),edge=bool(xs.min()<=1 or xs.max()>=CW-2),bbox=[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())])
            out[r*CH:(r+1)*CH,c*CW:(c+1)*CW]=cell
    # rows assembled from mis-sized frames: centre every frame on the character's feet
    messy=[r for r in range(ROWS) if sum(1 for c in range(COLS) if info[r][c]['frag'])>=2]
    for r in messy:
        for c in range(COLS):
            dx=int(round(CW/2-info[r][c]['feet']))
            if dx: out[r*CH:(r+1)*CH,c*CW:(c+1)*CW]=np.roll(out[r*CH:(r+1)*CH,c*CW:(c+1)*CW],dx,axis=1)
            if 'bbox' in info[r][c]: b=info[r][c]['bbox'];info[r][c]['bbox']=[b[0]+dx,b[1],b[2]+dx,b[3]]
    idleA=np.median([info[0][c]['area'] for c in range(COLS)])
    def hardcut_main(r,c):
        b=info[r][c].get('bbox');return bool(b) and (b[0]<=clipL+1 or b[2]>=clipR-1) and info[r][c]['area']<.8*idleA and r in messy
    bad={}
    for r in range(ROWS):
        lo=.45 if r<4 else .3   # lying-down death frames have a smaller silhouette
        bad[r]=[c for c in range(COLS) if info[r][c]['area']<lo*idleA or (info[r][c]['edge'] and info[r][c]['area']<.75*idleA) or (hardcut_main(r,c)) or (info[r][c].get('spill',0)>.18*idleA and not info[r][c]['frag'])]
        good=[c for c in range(COLS) if c not in bad[r]]
        for c in bad[r]:
            if not good: break
            g=min(good,key=lambda x:abs(x-c))
            out[r*CH:(r+1)*CH,c*CW:(c+1)*CW]=out[r*CH:(r+1)*CH,g*CW:(g+1)*CW]
    off=[ROWN[r] for r in range(ROWS) if len(bad[r])>3]
    # despill: pull green down to max(r,b) on soft edges and on pixels next to transparency
    al=out[...,3];edge=(al<250)|ndimage.binary_dilation(al<20,iterations=2)
    g=out[...,1];lim=np.maximum(out[...,0],out[...,2])+6
    out[...,1]=np.where(edge&(g>lim),lim,g)
    # anchors from the idle row (union of main-body boxes)
    bb=np.array([info[0][c]['bbox'] for c in range(COLS)])
    meta[hid]=dict(t=round(bb[:,1].min()/CH,3),f=round(bb[:,3].max()/CH,3),x=round(((bb[:,0].min()+bb[:,2].max())/2)/CW,3),off=off)
    img=Image.fromarray(np.clip(out,0,255).astype(np.uint8),'RGBA')
    img=img.resize((round(CW*SCALE)*COLS,round(CH*SCALE)*ROWS),Image.LANCZOS)
    img.save(f'{OUT}/{hid}.webp','WEBP',quality=int(os.environ.get('Q','74')),method=6)
    report.append(f"{hid:10s} clip={clipL},{clipR} messy={messy} bad={ {ROWN[r]:bad[r] for r in bad if bad[r]} } off={off} kb={os.path.getsize(f'{OUT}/{hid}.webp')//1024}")
json.dump(meta,open(f'{OUT}/meta.json','w'),separators=(',',':'))
print('\n'.join(report));print('total KB',sum(os.path.getsize(p) for p in glob.glob(OUT+'/*.webp'))//1024)
