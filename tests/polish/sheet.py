import sys,glob,os
from PIL import Image,ImageDraw
# sheet.py out.png img1 img2 ... (grid 2 cols, labelled)
out=sys.argv[1];fs=sys.argv[2:];W=640
ims=[Image.open(f).convert('RGB') for f in fs];ims=[i.resize((W,int(i.height*W/i.width))) for i in ims];H=max(i.height for i in ims)
cols=2;rows=(len(ims)+1)//2;S=Image.new('RGB',(W*cols,H*rows),'white');d=ImageDraw.Draw(S)
for k,(i,f) in enumerate(zip(ims,fs)):
  x,y=(k%cols)*W,(k//cols)*H;S.paste(i,(x,y));d.rectangle([x,y,x+len(os.path.basename(f))*7+6,y+14],fill='black');d.text((x+3,y+2),os.path.basename(f),fill='white')
S.save(out)
