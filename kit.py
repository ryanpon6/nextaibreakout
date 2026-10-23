"""Kit (ConvertKit) email signup for 'NAB Daily' (form 10061594). Gated by KIT=1 in build.py (off by default: production
builds and the hourly cron do not include it). Also runnable standalone on a built dir: python3 kit.py <distdir>.
- Plain HTML <form> posting to Kit's public form endpoint; no API key anywhere in the page.
- Invisible reCAPTCHA is ON for the form, so Kit's own embed (ck.5.js) sends a reCAPTCHA v3 token with each signup.
  We do the same, but lazily: Google's reCAPTCHA script (Kit's public site key) is loaded only on first focus/hover of the form.
  Kit's "quarantined"/consent replies are handled by showing Kit's guard page in an overlay, as ck.5.js does.
  No JS (or script blocked): the browser does a normal POST to Kit, which shows Kit's own confirm/thank-you page.
- Honeypot: hidden off-screen 'nab_hp_x' field (wrapper aria-hidden, input tabindex=-1, autocomplete=new-password so browsers do not autofill it). If it is filled,
  the JS drops the submit and shows the normal success message (no POST to Kit). It is removed from the FormData we send.
  LIMITATION: with JS off/blocked the native POST still reaches Kit (field included, Kit ignores it); Kit's reCAPTCHA + double opt-in remain the backstop.
  On the native fallback after a reCAPTCHA/fetch failure (f.submit()) the honeypot check has already run.
- CASL: unchecked, required consent checkbox (name=consent; the browser blocks submit until ticked); sender name shown next to the form.
- Placement (signup-staged): below the content, inside <main>, on every item page, every blog post (/blog/<slug>/) and only those
  /daily/<date>/ pages whose emails/<date>.checker is exactly one line 'CHECKER: PASS <iso+offset> sha256=<sha256 of emails/<date>.html>' (dir: $NAB_EMAILS or ./emails).
  No passing .checker file -> no box on that daily page (the /daily/ index gets none either). Build prints the counts.
- No page-name hidden field: Kit has no custom fields and none is added without Ryan's OK; measurement uses Kit's referrer/host value. 'host' is sent as origin+path only and 'search' (query string / UTM tags) is sent empty."""
import glob, os, re, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))
FORM_ID = "10061594"
ACTION = f"https://app.kit.com/forms/{FORM_ID}/subscriptions"
SITEKEY = "6LdkIV0UAAAAABtNVAAP99TC6f_18LiETnPK6ziX"  # Kit's public reCAPTCHA v3 site key, as used by https://f.convertkit.com/ckjs/ck.5.js (not a secret)
SENDER = "NextAiBreakout"

def form(uid, heading="Don't miss the next breakout.", sub="The day's top AI breakouts, in one email each morning.", variant="closer"):
    """variant: closer (big section, #subscribe), hero (compact, inside the homepage hero), page (bottom of item/daily pages)."""
    fields = f"""<form class="kit-form" action="{ACTION}" method="post" accept-charset="UTF-8" data-kit="{FORM_ID}"><label class="kit-l" for="em-{uid}">Email address</label>
<div class="kit-row"><input id="em-{uid}" name="email_address" type="email" autocomplete="email" inputmode="email" placeholder="you@company.com" required aria-describedby="km-{uid}"><button class="btn pri" type="submit">{'Get the daily brief' if variant == 'hero' else 'Subscribe'}</button></div>
<label class="kit-ok"><input type="checkbox" name="consent" value="yes" required> <span>Yes, email me the {SENDER} daily. Unsubscribe anytime.</span></label>
<div class="kit-hp" aria-hidden="true" style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden"><label for="hp-{uid}">Leave this empty</label><input id="hp-{uid}" name="nab_hp_x" type="text" tabindex="-1" autocomplete="new-password" value=""></div>
<p class="kit-msg" id="km-{uid}" role="status" aria-live="polite"></p></form>"""
    if variant == "hero":
        return f'<div class="kit-hero">{fields}</div>'
    sid = ' id="subscribe"' if variant == "closer" else ""
    return f"""<section{sid} class="signup kit kit-{variant}"><div><h2>{heading}</h2><p class="dim">{sub}</p>
<p class="kit-sender dim">From {SENDER}. Double opt-in: we email you a confirm link first.</p></div>
{fields}</section>"""

CSS = ""  # Kit form styles live in static/style.css (they follow the site theme)

JS = """<script>(()=>{const K='%s',fs=document.querySelectorAll('form.kit-form');if(!fs.length||!window.fetch||!window.FormData)return;let L;
const load=()=>L||(L=new Promise((ok,no)=>{if(window.grecaptcha&&grecaptcha.execute)return grecaptcha.ready(ok);const s=document.createElement('script');s.src='https://www.google.com/recaptcha/api.js?render='+K;s.async=true;s.onload=()=>grecaptcha.ready(ok);s.onerror=()=>{L=null;no(new Error('recaptcha'))};document.head.appendChild(s)}));
const wait=(p,ms)=>Promise.race([p,new Promise((_,no)=>setTimeout(()=>no(new Error('timeout')),ms))]);
const guard=url=>new Promise(done=>{const o=document.createElement('div'),f=document.createElement('iframe'),x=document.createElement('button');o.className='kit-ov';f.src=url;f.title='Confirm you are human';x.className='btn';x.type='button';x.textContent='Close';
const end=v=>{removeEventListener('message',m);o.remove();done(v)},m=e=>{let h='';try{h=new URL(e.origin).hostname}catch(_){}if(!/(^|\\.)(kit|convertkit)\\.com$/.test(h))return;const n=e.data&&e.data.name;if(n==='ckjs:guard:confirmed')end(true)};
addEventListener('message',m);x.onclick=()=>end(false);o.append(f,x);document.body.append(o)});
fs.forEach(f=>{const b=f.querySelector('button'),msg=f.querySelector('.kit-msg'),say=(t,c)=>{msg.textContent=t;msg.className='kit-msg'+(c?' '+c:'')};
const warm=()=>load().catch(()=>{});f.addEventListener('focusin',warm,{once:true});f.addEventListener('pointerenter',warm,{once:true});
const ok=()=>{f.classList.add('done');say('Almost done: check your inbox and click the confirm link to start the daily email.','ok')};
const hp=f.querySelector('input[name=nab_hp_x]');
f.addEventListener('submit',async ev=>{if(f.dataset.native)return;ev.preventDefault();if(hp&&hp.value){return ok()}if(!f.reportValidity())return;b.disabled=true;say('Sending…');
let t='';try{await wait(load(),8000);t=await wait(grecaptcha.execute(K,{action:'formsubmit'}),8000)}catch(e){f.dataset.native=1;return f.submit()}
const d=new FormData(f);d.delete('nab_hp_x');d.append('token',t);d.append('referrer',document.referrer);d.append('host',location.origin+location.pathname);d.append('search','');d.append('ckjs_version','6');
let j;try{const r=await fetch(f.action,{method:'POST',body:d,headers:{Accept:'application/json','X-CKJS-Version':'6'}});j=await r.json()}catch(e){f.dataset.native=1;return f.submit()}
b.disabled=false;if(j&&j.status==='quarantined'&&j.url){say('One more step: confirm you are human.');return(await guard(j.url))?ok():say('Not finished. Press Subscribe to try again.','err')}
if(j&&j.status==='success'){if(j.consent&&j.consent.enabled&&j.consent.url)await guard(j.consent.url);return ok()}
const er=j&&j.errors;say((er&&(er.messages||[]).join(' '))||'That did not go through. Check the address and try again.','err')})})})()</script>""" % SITEKEY

def apply(DIST):
    n = 0
    # homepage: compact form in the hero, full form in the #subscribe slot
    hp = os.path.join(DIST, "index.html"); h = open(hp).read()
    h2 = re.sub(r'<section id="subscribe" class="signup">.*?</section>', lambda m: form("home"), h, 1, re.S)
    if h2 == h or "Email launching soon" in h2: raise SystemExit("[kit] homepage #subscribe slot not found")
    h2 = re.sub(r"<!--kit-hero-->.*?<!--/kit-hero-->", lambda m: form("hero", variant="hero"), h2, 1, re.S)
    open(hp, "w").write(h2.replace("</body>", JS + "</body>", 1)); n += 1
    # bottom of every /daily/ page and every item page (inside <main>, after the content)
    items = glob.glob(os.path.join(DIST, "item", "**", "index.html"), recursive=True)
    posts = glob.glob(os.path.join(DIST, "blog", "*", "index.html"))
    days = glob.glob(os.path.join(DIST, "daily", "*", "index.html"))
    ok_days = [p for p in days if passed(os.path.basename(os.path.dirname(p)))]
    print(f"[kit] daily: {len(ok_days)}/{len(days)} issues have a CHECKER: PASS file -> box only on those")
    for p in items + posts + ok_days:
        h = open(p).read()
        if 'class="kit-form"' in h: continue
        k = h.rfind("</main>")
        if k < 0: continue
        h = h[:k] + form("p", "Get the daily breakout by email.", "The day's top AI breakouts, in one email each morning.", "page") + h[k:]
        open(p, "w").write(h.replace("</body>", JS + "</body>", 1)); n += 1
    welcome(DIST)
    print(f"[kit] signup form on {n} pages (home + {n - 1} item/blog/daily); /welcome/ written (noindex, not in sitemap/llms)")

EMAILS = os.getenv("NAB_EMAILS") or os.path.join(HERE, "emails")
def passed(day):
    """True only if emails/<day>.checker is exactly one line 'CHECKER: PASS <iso> sha256=<64hex>', the iso parses with a UTC offset,
    and the hash equals sha256 of emails/<day>.html (which must exist). Anything else -> False."""
    import datetime, hashlib
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day): return False
    try:
        txt = open(os.path.join(EMAILS, day + ".checker"), encoding="utf-8").read()
        body = open(os.path.join(EMAILS, day + ".html"), "rb").read()
    except OSError: return False
    lines = txt.splitlines()
    if len(lines) != 1: return False
    m = re.fullmatch(r"CHECKER: PASS (\S+) sha256=([0-9a-f]{64})", lines[0])
    if not m: return False
    try: t = datetime.datetime.fromisoformat(m.group(1))
    except ValueError: return False
    if t.tzinfo is None: return False
    return hashlib.sha256(body).hexdigest() == m.group(2)

def welcome(DIST):
    """/welcome/ thank-you page: noindex + canonical, no signup form, deliberately left out of sitemap.xml and llms.txt."""
    import datetime as dt, build as B
    page = B.head(f"You're in | {B.BRAND}", "Thanks for subscribing to the NextAiBreakout daily email.", "/welcome/", "/").replace("</head>", '<meta name="robots" content="noindex"></head>', 1) + """<main class="prose kit-welcome">
<h1>You're in.</h1><p class="dim">Check tomorrow's email for the daily breakout.</p>
<div class="btns"><a class="btn pri" href="/daily/">See today's breakouts</a><a class="btn" href="/">Back to home</a></div></main>""" + B.foot(dt.date.today().year, "/") + "</body></html>"
    p = os.path.join(DIST, "welcome", "index.html")
    if B.SEO2:
        import seo2; seo2.wr(p, page)  # same fonts/nav/footer links as every other SEO2 page
    else:
        os.makedirs(os.path.dirname(p), exist_ok=True); open(p, "w").write(page)
    if os.path.isdir(os.path.join(DIST, "blog")):  # kit now runs after blog.apply, so add the same footer Blog link blog.py adds everywhere
        h = open(p).read(); ft = h.rfind("<footer")
        if ft >= 0 and 'href="/blog/">Blog</a>' not in h[ft:]:
            open(p, "w").write(h[:ft] + re.sub(r'(<a href="/?about(?:\.html)?">About</a>)', r'<a href="/blog/">Blog</a>\1', h[ft:], 1))

if __name__ == "__main__": apply(sys.argv[1])
