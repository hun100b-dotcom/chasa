"""하늘·날씨 재료 미리보기 시트(갤러리용). 실행: python3 sky_sheet.py → assets3d/previews/sky_sheet_{a,b}.jpg"""
import os, numpy as np
from PIL import Image
S=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","assets3d","sky"); P=os.path.join(os.path.dirname(os.path.abspath(__file__)),"..","..","assets3d","previews")
L=lambda n:Image.open(os.path.join(S,n)).convert("RGBA")
def over(bg,fg): b=bg.convert("RGBA"); b.alpha_composite(fg.resize(b.size) if fg.size!=b.size else fg); return b.convert("RGB")
# A: 하늘 띠 3종 + 구름 3종(하늘 위) + 달 4단계(밤 하늘 위)
W=1200
rows=[]
for v in ("clear","overcast","fog"): rows.append(Image.open(os.path.join(S,f"sky_gradient_{v}.png")).convert("RGB").resize((W,90)))
a=Image.new("RGB",(W,90*3+6*2+ 330),(20,20,26)); y=0
for r in rows: a.paste(r,(0,y)); y+=96
sky=Image.open(os.path.join(S,"sky_gradient_clear.png")).convert("RGB")
bgs=[sky.crop((int(480*10/24),0,int(480*10/24)+1,128)).resize((300,330)),sky.crop((int(480*10/24),0,int(480*10/24)+1,128)).resize((300,330)),sky.crop((int(480*17.8/24),0,int(480*17.8/24)+1,128)).resize((300,330))]
x=0
for nm,bg in zip(("cumulus","cirrus","storm"),bgs):
    c=L(f"cloud_{nm}.png").resize((300,300)); t=bg.convert("RGBA"); t.alpha_composite(c,(0,15)); a.paste(t.convert("RGB"),(x,y)); x+=300
night=sky.crop((0,0,1,128)).resize((300,330)).convert("RGBA"); st=L("stars.png").resize((300,300)); night.alpha_composite(st,(0,15))
a.paste(night.convert("RGB"),(x,y)); a.convert("RGB").save(os.path.join(P,"sky_sheet_a.jpg"),quality=88)
# B: 달 4 + 해 + 비 + 파문 + 안개
b=Image.new("RGB",(1200,520),(14,20,40)); x=0
for ph in ("crescent","first_quarter","full","last_quarter"):
    bg=Image.new("RGBA",(200,200),(14,22,46,255)); bg.alpha_composite(L("moon_halo.png").resize((200,200))); bg.alpha_composite(L(f"moon_{ph}.png").resize((200,200))); b.paste(bg.convert("RGB"),(x,0)); x+=200
bg=Image.new("RGBA",(200,200),(120,160,206,255)); bg.alpha_composite(L("sun_disc.png").resize((200,200))); b.paste(bg.convert("RGB"),(x,0)); x+=200
fb_=Image.new("RGBA",(200,200),(60,70,80,255)); fb_.alpha_composite(L("mist_puffs.png").crop((0,0,256,256)).resize((200,200))); b.paste(fb_.convert("RGB"),(x,0))
rain=Image.new("RGBA",(512,300),(52,62,72,255)); rain.alpha_composite(L("rain_streaks_far.png").crop((0,0,512,300))); rain.alpha_composite(L("rain_streaks_near.png").crop((0,0,512,300))); b.paste(rain.convert("RGB"),(0,210))
sp=L("rain_splash_sheet.png"); sbg=Image.new("RGBA",sp.size,(86,78,62,255)); sbg.alpha_composite(sp); sbg=sbg.resize((sp.width*3//2,sp.height*3//2)); b.paste(sbg.convert("RGB"),(530,210))
fog=Image.open(os.path.join(S,"fog_noise.png")).convert("L").resize((250,250)); b.paste(Image.merge("RGB",(fog,fog,fog)),(530,360-30+0)) if False else None
b.save(os.path.join(P,"sky_sheet_b.jpg"),quality=88)
