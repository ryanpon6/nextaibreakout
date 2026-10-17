from PIL import Image, ImageDraw, ImageFont
B="/usr/share/fonts/truetype/dejavu/"
def f(n,s): return ImageFont.truetype(B+n,s)
BG=(10,10,10); W=(242,242,242); G=(61,220,132); GL=(26,40,32); M=(150,155,152)
def art(w,h,k,seed=0):
    im=Image.new("RGB",(w,h),BG); d=ImageDraw.Draw(im); s=int(60*k)
    for x in range(0,w,s): d.line([x,0,x,h],fill=GL,width=max(1,int(k)))
    for y in range(0,h,s): d.line([0,y,w,y],fill=GL,width=max(1,int(k)))
    r=int(5*k)
    for i,(gx,gy) in enumerate([(3,2),(7,5),(12,3),(16,7),(19,2),(23,6),(9,9),(27,4)]):
        gx=(gx+seed)%(w//s); x,y=gx*s,(gy%(h//s))*s
        d.ellipse([x-r,y-r,x+r,y+r],fill=G)
    d.rectangle([0,0,w,int(8*k)],fill=G); return im,d
def fit(d,t,font,size,maxw):
    while d.textlength(t,font=f(font,size))>maxw: size-=2
    return f(font,size)
import sys
ONLY=set(sys.argv[1:])
def card(fn,w,h,k,kicker,title,sub,seed=0,note=None):
    if ONLY and fn not in ONLY: return
    im,d=art(w,h,k,seed)
    sx,sy=(w-1000*k*w/1200/k)/2 if False else 0,0
    # safe area: centered, width 1000/1200 of w, height 500/630 of h
    sw,sh=w*1000/1200,h*500/630; x0=(w-sw)/2; y0=(h-sh)/2
    # panel behind text for legibility (flat)
    ft=fit(d,title,"DejaVuSans-Bold.ttf",int(sh*0.26),sw-40*k)
    fs=fit(d,sub,"DejaVuSans.ttf",int(sh*0.085),sw-40*k)
    fk=f("DejaVuSansMono-Bold.ttf",int(sh*0.06))
    th=ft.getbbox(title)[3]; 
    d.rectangle([x0,y0+sh*0.08,x0+sw,y0+sh*0.92],fill=BG)
    y=y0+sh*0.16
    d.text((x0+20*k,y),kicker,font=fk,fill=G); y+=sh*0.14
    d.text((x0+20*k,y),title,font=ft,fill=W); y+=th+sh*0.06
    d.text((x0+20*k,y),sub,font=fs,fill=M)
    if note: d.text((x0+20*k,y+sh*0.13),note,font=f("DejaVuSans.ttf",int(sh*0.06)),fill=M)
    fu=f("DejaVuSansMono-Bold.ttf",int(sh*0.055)); u="nextaibreakout.com"
    d.text((x0+sw-20*k-d.textlength(u,font=fu),y0+sh*0.92-sh*0.12),u,font=fu,fill=G)
    im.save(fn,optimize=True)
card("og-default.png",1200,630,1,"NEXTAIBREAKOUT","NextAiBreakout","Tracking the road to superintelligence")
card("og-grok-bot.png",1200,630,1,"NEXTAIBREAKOUT","Grok Bot updates","What Grok Bots are doing in the real world",2)
card("grok-bot-hero.png",3200,1200,2,"NEXTAIBREAKOUT","Grok Bot updates","What Grok Bots are doing in the real world",2)
card("og-labs.png",1200,630,1,"NEXTAIBREAKOUT","AI Labs","Latest releases from the frontier labs",4)
card("og-blog.png",1200,630,1,"NEXTAIBREAKOUT","Breakouts","What moved in AI, and what's next",6)
labs={"xai":"SpaceXSI (xAI)","tesla-ai":"Tesla AI","openai":"OpenAI","anthropic":"Anthropic","google-deepmind":"Google DeepMind","meta":"Meta"}
for i,(s,n) in enumerate(labs.items()):
    note='Unofficial tracker, not affiliated with Tesla' if s=='tesla-ai' else None
    card(f"labs-{s}-header.png",2400,800,2,"AI LABS · NEXTAIBREAKOUT",n,"Latest releases, tracked by NextAiBreakout",i,note)
    card(f"labs-{s}-og.png",1200,630,1,"AI LABS",n,"Latest releases, tracked by NextAiBreakout",i,note)
