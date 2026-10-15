# Pack hero art into art/art_data.js: 3:4 bust portraits (382x512) + character sheets, as WebP data URIs.
import base64,io,glob,os,sys
from PIL import Image
ORDER=['lilac','azazel','seraphine','aurelia','nyx','kaelan','noct','evelyne','brand','garrick','sable','mira','silas','elva','ravek','oswin','vex','thorn','pip','greta','odric','liz','bram','wren']
QP,QS,SW=int(sys.argv[1]),int(sys.argv[2]),int(sys.argv[3])
def uri(im,q):
    b=io.BytesIO();im.save(b,'WEBP',quality=q,method=6);return 'data:image/webp;base64,'+base64.b64encode(b.getvalue()).decode()
P={};S={}
# myzip IMG_1528..1547 = heroes 24 → 5 (reverse order); the four URs come from urbust.py
for n,hid in zip(range(1528,1548),reversed(ORDER[4:])): P[hid]=Image.open(f'in/my/IMG_{n}.jpeg').convert('RGB')
for hid in ORDER[:4]: P[hid]=Image.open(f'art/ur_{hid}.png').convert('RGB')
# user-supplied replacement busts override the generated ones
for f in glob.glob('in/new/*_bust.*'): P[os.path.basename(f).split('_')[0]]=Image.open(f).convert('RGB')
# full-body figures (RGBA) cut from the sheets by fullbody.py
F={hid:Image.open(f'art/full/{hid}.png').convert('RGBA') for hid in ORDER}
for f in glob.glob('in/sh/sheets_png/*.png'):
    hid=os.path.basename(f).split('_',2)[2][:-4];im=Image.open(f).convert('RGB')
    S[hid]=im.resize((SW,round(im.height*SW/im.width)),Image.LANCZOS) if im.width>SW else im
assert set(P)==set(ORDER)==set(S),(set(ORDER)-set(P),set(ORDER)-set(S))
ps={k:uri(v.resize((382,512),Image.LANCZOS) if v.size!=(382,512) else v,QP) for k,v in P.items()}
ss={k:uri(v,QS) for k,v in S.items()}
fs={k:uri(v,QP) for k,v in F.items()}
js='const ART={p:{'+','.join(f'{k}:"{ps[k]}"' for k in ORDER)+'},\n s:{'+','.join(f'{k}:"{ss[k]}"' for k in ORDER)+'},\n f:{'+','.join(f'{k}:"{fs[k]}"' for k in ORDER)+'}};\n'
open('art/art_data.js','w').write(js)
print('portraits KB',sum(len(v) for v in ps.values())//1024,'sheets KB',sum(len(v) for v in ss.values())//1024,'full KB',sum(len(v) for v in fs.values())//1024,'total KB',len(js)//1024)
