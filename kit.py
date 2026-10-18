"""Kit (ConvertKit) email signup for 'NAB Daily' (form 10061594). Gated by KIT=1 in build.py (off by default: production
builds and the hourly cron do not include it). Also runnable standalone on a built dir: python3 kit.py <distdir>.
- Plain HTML <form> posting to Kit's public form endpoint; no API key anywhere in the page.
- Invisible reCAPTCHA is ON for the form, so Kit's own embed (ck.5.js) sends a reCAPTCHA v3 token with each signup.
  We do the same, but lazily: Google's reCAPTCHA script (Kit's public site key) is loaded only on first focus/hover of the form.
  Kit's "quarantined"/consent replies are handled by showing Kit's guard page in an overlay, as ck.5.js does.
  No JS (or script blocked): the browser does a normal POST to Kit, which shows Kit's own confirm/thank-you page.
- CASL: unchecked, required consent checkbox; sender name + contact shown next to the form."""
import glob, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FORM_ID = "10061594"
ACTION = f"https://app.kit.com/forms/{FORM_ID}/subscriptions"
SITEKEY = "6LdkIV0UAAAAABtNVAAP99TC6f_18LiETnPK6ziX"  # Kit's public reCAPTCHA v3 site key, as used by https://f.convertkit.com/ckjs/ck.5.js (not a secret)
SENDER = "NextAiBreakout"; CONTACT = "hello@nextaibreakout.com"

def form(uid, heading="The daily breakout, in your inbox.", sub="Top 10 movers and the frontier releases. One email a day. No hype."):
    return f"""<section id="subscribe" class="signup kit"><img class="kit-bg" src="/kit-bg.webp" alt="" width="1100" height="619" loading="lazy" decoding="async"><div><h2>{heading}</h2><p class="dim">{sub}</p>
<p class="kit-sender mono dim">From {SENDER} · <a href="mailto:{CONTACT}">{CONTACT}</a>. Double opt-in: we email you a confirm link first.</p></div>
<form class="kit-form" action="{ACTION}" method="post" accept-charset="UTF-8" data-kit="{FORM_ID}"><label class="mono dim" for="em-{uid}">Email address</label>
<div><input id="em-{uid}" name="email_address" type="email" autocomplete="email" inputmode="email" placeholder="you@company.com" required aria-describedby="km-{uid}"><button class="btn pri" type="submit">Subscribe</button></div>
<label class="kit-ok"><input type="checkbox" required> <span>Yes, email me the {SENDER} daily. Unsubscribe anytime.</span></label>
<p class="kit-msg mono" id="km-{uid}" role="status" aria-live="polite"></p></form></section>"""

CSS = """
/* Kit signup (KIT=1) */
.signup.kit{position:relative;overflow:hidden;isolation:isolate}
.kit-bg{position:absolute;inset:0;width:100%;height:100%;max-width:none;object-fit:cover;object-position:right center;z-index:-1;opacity:.55;pointer-events:none}
.signup.kit>div,.signup.kit form{position:relative}
.kit-sender{font-size:11px;margin:10px 0 0}.kit-sender a{color:var(--gr)}
.kit-ok{display:flex!important;gap:9px;align-items:flex-start;margin:12px 0 0!important;font-size:13px!important;color:var(--fg);cursor:pointer;line-height:1.4}
.kit-ok input{flex:none!important;width:17px!important;height:17px;margin:1px 0 0;accent-color:#3DDC84;padding:0}
.signup .kit-form button{flex:none}
.signup input:focus-visible,.signup button:focus-visible,.kit-ok input:focus-visible{outline:2px solid #3DDC84;outline-offset:2px}
.kit-msg{min-height:3.2em;margin:10px 0 0;font-size:12px;color:var(--mut)}.kit-msg.ok{color:#3DDC84}.kit-msg.err{color:#F2B8A2}
.kit-form.done>div,.kit-form.done .kit-ok,.kit-form.done>label{visibility:hidden}
.kit-ov{position:fixed;inset:0;z-index:50;background:rgba(5,6,5,.82);display:flex;align-items:center;justify-content:center;padding:16px}
.kit-ov iframe{width:min(520px,100%);height:min(560px,90vh);border:1px solid #1E2220;border-radius:12px;background:#fff}
.kit-ov button{position:absolute;top:14px;right:16px}
.kit-welcome{padding-top:56px;min-height:52vh}.kit-welcome h1{margin-top:10px}
@media (max-width:640px){.kit-ok{font-size:12px!important}.kit-welcome{padding-top:32px}}
"""

JS = """<script>(()=>{const K='%s',fs=document.querySelectorAll('form.kit-form');if(!fs.length||!window.fetch||!window.FormData)return;let L;
const load=()=>L||(L=new Promise((ok,no)=>{if(window.grecaptcha&&grecaptcha.execute)return grecaptcha.ready(ok);const s=document.createElement('script');s.src='https://www.google.com/recaptcha/api.js?render='+K;s.async=true;s.onload=()=>grecaptcha.ready(ok);s.onerror=()=>{L=null;no(new Error('recaptcha'))};document.head.appendChild(s)}));
const wait=(p,ms)=>Promise.race([p,new Promise((_,no)=>setTimeout(()=>no(new Error('timeout')),ms))]);
const guard=url=>new Promise(done=>{const o=document.createElement('div'),f=document.createElement('iframe'),x=document.createElement('button');o.className='kit-ov';f.src=url;f.title='Confirm you are human';x.className='btn';x.type='button';x.textContent='Close';
const end=v=>{removeEventListener('message',m);o.remove();done(v)},m=e=>{let h='';try{h=new URL(e.origin).hostname}catch(_){}if(!/(^|\\.)(kit|convertkit)\\.com$/.test(h))return;const n=e.data&&e.data.name;if(n==='ckjs:guard:confirmed')end(true)};
addEventListener('message',m);x.onclick=()=>end(false);o.append(f,x);document.body.append(o)});
fs.forEach(f=>{const b=f.querySelector('button'),msg=f.querySelector('.kit-msg'),say=(t,c)=>{msg.textContent=t;msg.className='kit-msg mono'+(c?' '+c:'')};
const warm=()=>load().catch(()=>{});f.addEventListener('focusin',warm,{once:true});f.addEventListener('pointerenter',warm,{once:true});
const ok=()=>{f.classList.add('done');say('Almost done: check your inbox and click the confirm link to start the daily email.','ok')};
f.addEventListener('submit',async ev=>{if(f.dataset.native)return;ev.preventDefault();if(!f.reportValidity())return;b.disabled=true;say('Sending…');
let t='';try{await wait(load(),8000);t=await wait(grecaptcha.execute(K,{action:'formsubmit'}),8000)}catch(e){f.dataset.native=1;return f.submit()}
const d=new FormData(f);d.append('token',t);d.append('referrer',document.referrer);d.append('host',location.href);d.append('search',location.search);d.append('ckjs_version','6');
let j;try{const r=await fetch(f.action,{method:'POST',body:d,headers:{Accept:'application/json','X-CKJS-Version':'6'}});j=await r.json()}catch(e){f.dataset.native=1;return f.submit()}
b.disabled=false;if(j&&j.status==='quarantined'&&j.url){say('One more step: confirm you are human.');return(await guard(j.url))?ok():say('Not finished. Press Subscribe to try again.','err')}
if(j&&j.status==='success'){if(j.consent&&j.consent.enabled&&j.consent.url)await guard(j.consent.url);return ok()}
const er=j&&j.errors;say((er&&(er.messages||[]).join(' '))||'That did not go through. Check the address and try again.','err')})})})()</script>""" % SITEKEY

def apply(DIST):
    shutil.copy(os.path.join(HERE, "kit", "kit-bg.webp"), os.path.join(DIST, "kit-bg.webp"))
    css = os.path.join(DIST, "seo2.css") if os.path.exists(os.path.join(DIST, "seo2.css")) else os.path.join(DIST, "style.css")
    c = open(css).read()
    if "Kit signup (KIT=1)" not in c: open(css, "w").write(c + CSS)
    n = 0
    # homepage: replace the disabled "Email launching soon" slot in #subscribe
    hp = os.path.join(DIST, "index.html"); h = open(hp).read()
    h2 = re.sub(r'<section id="subscribe" class="signup">.*?</section>', lambda m: form("home"), h, 1, re.S)
    if h2 == h or "Email launching soon" in h2: raise SystemExit("[kit] homepage #subscribe slot not found")
    open(hp, "w").write(h2.replace("</body>", JS + "</body>", 1)); n += 1
    # bottom of every /daily/ page and every item page (inside <main>, after the content)
    pages = glob.glob(os.path.join(DIST, "daily", "**", "index.html"), recursive=True) + glob.glob(os.path.join(DIST, "item", "**", "index.html"), recursive=True)
    for p in pages:
        h = open(p).read()
        if 'class="kit-form"' in h: continue
        k = h.rfind("</main>")
        if k < 0: continue
        h = h[:k] + form("p", "Get the daily breakout by email.", "The hourly top 10 and frontier releases, in one email a day.") + h[k:]
        open(p, "w").write(h.replace("</body>", JS + "</body>", 1)); n += 1
    welcome(DIST)
    print(f"[kit] signup form on {n} pages (home + {n - 1} daily/item); /welcome/ written (noindex, not in sitemap/llms)")

def welcome(DIST):
    """/welcome/ thank-you page: noindex + canonical, no signup form, deliberately left out of sitemap.xml and llms.txt."""
    import datetime as dt, build as B
    page = B.head(f"You're in | {B.BRAND}", "Thanks for subscribing to the NextAiBreakout daily email.", "/welcome/", "/").replace("</head>", '<meta name="robots" content="noindex"></head>', 1) + """<main class="prose kit-welcome">
<p class="kick mono">SUBSCRIBED</p><h1>You're in.</h1><p class="dim">Check tomorrow's email for the daily breakout.</p>
<div class="btns"><a class="btn pri" href="/daily/">See today's breakouts</a><a class="btn" href="/">Back to home</a></div></main>""" + B.foot(dt.date.today().year, "/") + "</body></html>"
    p = os.path.join(DIST, "welcome", "index.html")
    if B.SEO2:
        import seo2; seo2.wr(p, page)  # same fonts/nav/footer links as every other SEO2 page
    else:
        os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(page)

if __name__ == "__main__": apply(sys.argv[1])
