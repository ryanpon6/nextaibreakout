#!/usr/bin/env python3
"""Render NextAiBreakout tip, share, OG and X cards in the Bot Cut-outs palette.

Read DESIGN.md first. Tokens, 3px ink outlines, hard shadows, Syne / DM Sans / Gochi Hand,
original robots only (no Grok or xAI logos). Never white text on red or ochre; never
#FF4B2B as text on the pale ground (use --red-ink).

Usage:
  python3 brand/render_cutouts.py            # tip cards + og-default into static/
  python3 brand/render_cutouts.py --x-cards  # also render 14 X cards
"""
from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "static")
TIPS_DIR = os.path.join(STATIC, "images", "tips")
X_DIR = "/workspace/shared/nab-relaunch/cards"

SYNE = "file:///usr/share/fonts/truetype/sand-box/google/Syne/Syne-VariableFont_wght.ttf"
DM = "file:///usr/share/fonts/truetype/sand-box/google/DM%20Sans/DMSans-VariableFont_opsz,wght.ttf"
GOCHI = "file:///usr/share/fonts/truetype/sand-box/google/Gochi%20Hand/GochiHand-Regular.ttf"

BG, PAPER, INK, MUT = "#E9EEF2", "#FFFFFF", "#0F1B3D", "#46506B"
RED, RED_INK, BLUE, OCH, SKY = "#FF4B2B", "#B92E16", "#2747F5", "#F2B01E", "#BFD0FF"

CHROME = [
    "google-chrome", "--headless=new", "--no-sandbox", "--disable-gpu",
    "--hide-scrollbars", "--force-device-scale-factor=1",
]

CSS = f"""
@font-face{{font-family:Syne;src:url('{SYNE}') format('truetype');font-weight:400 800;font-style:normal}}
@font-face{{font-family:'DM Sans';src:url('{DM}') format('truetype');font-weight:100 1000;font-style:normal}}
@font-face{{font-family:'Gochi Hand';src:url('{GOCHI}') format('truetype');font-weight:400;font-style:normal}}
:root{{--bg:{BG};--paper:{PAPER};--ink:{INK};--mut:{MUT};--red:{RED};--red-ink:{RED_INK};--blue:{BLUE};--och:{OCH};--sky:{SKY}}}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:100%;height:100%;background:var(--bg);color:var(--ink);font-family:'DM Sans',sans-serif;overflow:hidden}}
.bot{{position:relative;display:inline-flex;flex-direction:column;align-items:center}}
.bant{{position:relative;width:.12em;height:.46em;background:var(--ink)}}
.bant::before{{content:"";position:absolute;left:50%;top:-.24em;width:.3em;height:.3em;margin-left:-.15em;border-radius:50%;background:var(--a,var(--och));border:.07em solid var(--ink)}}
.bhead{{position:relative;flex:none;width:2.2em;height:1.7em;padding-bottom:.34em;background:var(--c,var(--red));border:.09em solid var(--ink);border-radius:var(--hr,.5em);display:flex;align-items:center;justify-content:center;gap:.36em;box-shadow:.14em .14em 0 var(--ink)}}
.beye{{position:relative;width:.44em;height:.44em;border-radius:50%;background:#fff;border:.07em solid var(--ink)}}
.beye::after{{content:"";position:absolute;left:32%;top:32%;width:44%;height:44%;border-radius:50%;background:var(--ink)}}
.beye.big{{width:.66em;height:.66em;box-shadow:0 0 0 .08em #fff,0 0 0 .15em var(--ink)}}
.bmouth{{position:absolute;bottom:.22em;left:50%;width:.7em;height:.28em;margin-left:-.35em;border:.07em solid var(--ink);border-top:0;border-radius:0 0 .4em .4em;background:#fff}}
.bbody{{position:relative;width:1.6em;height:1.15em;margin-top:.1em;background:var(--b,var(--c,var(--red)));border:.09em solid var(--ink);border-radius:.3em .3em .5em .5em;box-shadow:.14em .14em 0 var(--ink)}}
.barm{{position:absolute;top:.14em;width:.2em;height:.8em;background:var(--ink);border-radius:.1em;transform-origin:50% .1em}}
.barm.l{{left:-.36em;transform:rotate(22deg)}}.barm.r{{right:-.36em;transform:rotate(-22deg)}}
.brand{{display:flex;align-items:center;gap:12px;font-family:Syne,sans-serif;font-weight:800;letter-spacing:-.03em;color:var(--ink)}}
.brand .bhead{{font-size:15px;--c:var(--red);padding-bottom:0;box-shadow:2px 2px 0 var(--ink)}}
.pill{{display:inline-flex;align-items:center;gap:8px;background:var(--och);color:var(--ink);border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);border-radius:999px;padding:6px 16px 6px 12px;font-weight:700;letter-spacing:.01em}}
.pill i{{width:10px;height:10px;border-radius:50%;background:var(--ink);display:block;flex:none}}
.paper{{background:var(--paper);border:3px solid var(--ink);box-shadow:7px 7px 0 var(--ink)}}
.note{{font-family:'Gochi Hand',cursive;font-weight:400;color:var(--red-ink);letter-spacing:0}}
"""

def e(s):
    return html.escape(s, quote=True)

def bot_head(c="var(--red)", hr="", big=False, mouth=False):
    style = f"--c:{c}" + (f";--hr:{hr}" if hr else "")
    mouth_html = '<b class="bmouth"></b>' if mouth else ""
    return (f'<span class="bhead" style="{style}" aria-hidden="true">'
            f'<i class="beye{" big" if big else ""}"></i><i class="beye"></i>{mouth_html}</span>')

def bot(c="var(--red)", hr="", a="var(--och)", b="", big=False, size="64px"):
    style = f"font-size:{size};--c:{c}" + (f";--hr:{hr}" if hr else "") + (f";--a:{a}" if a else "") + (f";--b:{b}" if b else "")
    return (f'<span class="bot" style="{style}" aria-hidden="true"><span class="bant"></span>'
            f'<span class="bhead"><i class="beye{" big" if big else ""}"></i><i class="beye"></i>'
            f'<b class="bmouth"></b></span>'
            f'<span class="bbody"><i class="barm l"></i><i class="barm r"></i></span></span>')

LEAD = bot_head()
FOOTER = "From my Grok Bot setup"

def screenshot(page_html, dest, w, h):
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(page_html)
        src = f.name
    raw = dest + ".raw.png"
    try:
        subprocess.run(
            CHROME + [f"--window-size={w},{h}", f"--screenshot={raw}",
                      "--virtual-time-budget=4000", "file://" + src],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=60, check=False,
        )
        os.makedirs(os.path.dirname(os.path.abspath(dest)) or ".", exist_ok=True)
        os.makedirs(os.path.dirname(os.path.abspath(raw)) or ".", exist_ok=True)
        if not os.path.isfile(raw) or os.path.getsize(raw) < 1000:
            raise RuntimeError(f"chrome failed to write {raw}")
        im = Image.open(raw).convert("RGB")
        if im.size != (w, h):
            if im.size[0] >= w and im.size[1] >= h:
                im = im.crop((0, 0, w, h))
            else:
                canvas = Image.new("RGB", (w, h), (233, 238, 242))
                canvas.paste(im, (0, 0))
                im = canvas
        ext = dest.rsplit(".", 1)[-1].lower()
        if ext == "webp":
            im.save(dest, "WEBP", quality=86, method=6)
        elif ext in ("jpg", "jpeg"):
            im.save(dest, "JPEG", quality=90, optimize=True)
        else:
            im.save(dest, "PNG")
    finally:
        try:
            os.unlink(src)
        except OSError:
            pass
        if os.path.isfile(raw):
            os.unlink(raw)


def wrap_page(w, h, body, extra_css=""):
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{CSS}
body{{width:{w}px;height:{h}px;position:relative}}
{extra_css}
</style></head><body>
{body}
</body></html>"""


def shapes(kind="default"):
    # Decorative cut-outs, kept away from the main text column.
    if kind == "og":
        return """
<div style="position:absolute;left:-80px;top:-60px;width:340px;aspect-ratio:1.1;background:var(--och);border-radius:62% 38% 54% 46%/48% 60% 40% 52%;opacity:.7"></div>
<div style="position:absolute;right:-40px;top:20px;width:260px;aspect-ratio:1;background:var(--sky);border-radius:50%;opacity:.85"></div>
<div style="position:absolute;right:18%;bottom:-40px;width:220px;aspect-ratio:1;border-radius:50%;background-image:radial-gradient(var(--blue) 36%,transparent 38%);background-size:14px 14px;opacity:.35"></div>
"""
    return """
<div style="position:absolute;left:-90px;top:-70px;width:320px;aspect-ratio:1.1;background:var(--och);border-radius:62% 38% 54% 46%/48% 60% 40% 52%;opacity:.55"></div>
<div style="position:absolute;right:-50px;top:-30px;width:240px;aspect-ratio:1;background:var(--sky);border-radius:50%;opacity:.7"></div>
<div style="position:absolute;right:8%;bottom:-50px;width:200px;aspect-ratio:1;border-radius:50%;background-image:radial-gradient(var(--blue) 36%,transparent 38%);background-size:12px 12px;opacity:.3"></div>
"""


def topbar(w_pad, brand_size, pill, pill_size):
    return f"""
<div class="top" style="position:absolute;left:{w_pad}px;right:{w_pad}px;top:{int(w_pad*0.7)}px;display:flex;justify-content:space-between;align-items:center">
  <div class="brand" style="font-size:{brand_size}px">{LEAD}<span>NextAiBreakout</span></div>
  <div class="pill" style="font-size:{pill_size}px"><i></i>{e(pill)}</div>
</div>
"""


def footer_bar(w_pad, y, size, width):
    return f"""
<div style="position:absolute;left:{w_pad}px;right:{w_pad}px;top:{y}px;border-top:3px solid var(--ink);padding-top:16px;font-size:{size}px;font-weight:500;color:var(--mut);width:{width}px;box-sizing:border-box">
{e(FOOTER)}
</div>
"""


def quote_size(text, canvas_w, is_og=False):
    n = len(text)
    if canvas_w >= 1200:
        if n > 200:
            return 34 if is_og else 36
        if n > 140:
            return 38 if is_og else 40
        if n > 90:
            return 42 if is_og else 44
        if n > 50:
            return 46 if is_og else 52
        return 54 if is_og else 60
    return 40


# ---- tip brand cards (same copy as the teal renders) ----
# layout: quote | bignum | compare | beforeafter
TIPS = [
    dict(slug="talk-to-one-lead-bot", layout="quote", pill="Day 1",
         quote="I don't talk to my whole Grok Bot fleet. I talk to one lead bot, and it routes work to the specialists. If everyone can ping you, you just built a louder inbox. What's your lead bot actually in charge of?",
         title="Talk to one lead bot"),
    dict(slug="quality-checker-before-it-reaches-you", layout="compare", pill="Quality",
         headline="Quality Checker in front of you",
         left_pill="Five dones", right_pill="One checked result",
         row="What I get", left="Five dones", right="One checked"),
    dict(slug="agent-to-agent-handoffs", layout="quote", pill="Teams",
         quote="Specialists don't report to me. They hand work to each other with a clear output, and the lead bot brings me one result.",
         title="Agent-to-agent handoffs"),
    dict(slug="drafts-only-approval", layout="quote", pill="Rule",
         quote="Sends, spending and sign-ins still wait for my OK.",
         title="Sends, spending and sign-ins wait for my OK"),
    dict(slug="shared-skills-across-bots", layout="quote", pill="Skills",
         quote="A skill is a reusable playbook, not a prompt I retype every morning.",
         title="Save working workflows as skills"),
    dict(slug="check-your-routine-timezone", layout="quote", pill="Routines",
         quote="Cron doesn't care what you meant. It cares what zone you set.",
         title="Check the timezone on every routine"),
    dict(slug="watch-usage-pause-routines", layout="quote", pill="Usage",
         quote="Watch the meter and pause routines before they all crash.",
         title="Watch usage, then pause routines"),
    dict(slug="blabara-in-one-day", layout="bignum", pill="Built",
         number="1 day", label="Blabara, Android voice dictation.",
         sub="Built with a Grok Bot team."),
    dict(slug="group-chat-per-project", layout="quote", pill="Teams",
         quote="One channel, one job, then close it when the work is done.",
         title="One group chat per project"),
    dict(slug="before-after-proof", layout="beforeafter", pill="Quality",
         headline="No fix without proof.",
         before=["Done.", "A bot saying it's fixed"],
         after=["Before / after", "Side by side, something I can see"]),
    dict(slug="approve-spend-and-credentials", layout="quote", pill="Approvals",
         quote="A bot can draft the step. I still press the button.",
         title="One-tap approvals for spend and credentials"),
    dict(slug="bot-drafts-checker-reviews", layout="compare", pill="Pipeline",
         headline="Fast draft, slow send.",
         left_pill="Bot drafts", right_pill="Checker reviews",
         row="The send", left="A bot's say-so", right="I approve"),
    dict(slug="scripted-brand-cards", layout="quote", pill="Visuals",
         quote="One style. Every card.",
         title="Script the cards, don't redesign every post",
         sub="Same colours, same type. No photos of people."),
    dict(slug="scheduled-pack-and-gates", layout="quote", pill="Routines",
         quote="Scheduled prompts are useful. Publishing with no gate is not.",
         title="Daily news posts go out after a gate"),
    dict(slug="open-with-a-hook-line", layout="bignum", pill="Writing",
         number="7", label="First lines rewritten.",
         sub="Days 10 to 14, and two weekly thread openers. Nov 14, 2026."),
    dict(slug="turn-lessons-into-posts", layout="compare", pill="Lessons",
         headline="A lesson becomes a post.",
         left_pill="We fixed it", right_pill="Now it's a post",
         row="What we do", left="Adopt the lesson", right="Write it up"),
    dict(slug="recheck-after-late-edits", layout="beforeafter", pill="Quality",
         headline="Re-check after late edits.",
         before=["Passed.", "A review of an older draft"],
         after=["Edited, so check again", "A pass covers only that version"]),
    dict(slug="one-job-per-bot", layout="quote", pill="Jobs",
         quote="Give each bot one job.",
         title="Give every bot one job"),
    dict(slug="write-down-checker-rules", layout="quote", pill="Quality",
         quote="Write the checker's rules down, and add one for every miss.",
         title="Write the checker's rules down"),
    dict(slug="isolate-the-app-repo", layout="quote", pill="Access",
         quote="Keep one repo off-limits to the rest of the fleet.",
         title="Keep one repo off-limits"),
    dict(slug="change-only-watches", layout="quote", pill="Quiet",
         quote="Silence is the correct output when nothing changed.",
         title="Stay quiet unless something changed"),
    dict(slug="script-before-model", layout="quote", pill="Usage",
         quote="Prefer a script over a model when the job is deterministic.",
         title="Prefer a script over a model"),
    dict(slug="human-publish-gate", layout="quote", pill="Publish",
         quote="Put a human publish gate in front of the website.",
         title="A human publish gate"),
]


def tip_body(c, w, h):
    pad = 56 if h >= 675 else 48
    brand_size = 28 if h >= 675 else 26
    pill_size = 18 if h >= 675 else 16
    foot_size = 20 if h >= 675 else 18
    foot_y = h - pad - 44
    header = topbar(pad, brand_size, c["pill"], pill_size)
    foot = footer_bar(pad, foot_y, foot_size, w - 2 * pad)
    layout = c["layout"]

    if layout == "quote":
        q = c["quote"]
        size = quote_size(q, w, is_og=(h <= 630))
        title_size = 24 if len(c["title"]) > 36 else 26
        if h <= 630:
            title_size -= 2
        sub = ""
        if c.get("sub"):
            sub = f'<p class="sub" style="margin-top:10px;font-size:{20 if h>=675 else 18}px;font-weight:500;color:var(--mut)">{e(c["sub"])}</p>'
        mark_size = 86 if h >= 675 else 76
        top = 118 if h >= 675 else 104
        paper_bottom = 28
        return header + f"""
<div class="paper" style="position:absolute;left:{pad}px;right:{pad}px;top:{top}px;bottom:{h-foot_y+paper_bottom}px;border-radius:28px 44px 24px 36px;padding:{36 if h>=675 else 28}px {44 if h>=675 else 36}px 28px;display:flex;flex-direction:column;justify-content:center">
  <div class="mark" style="font-family:Syne,sans-serif;font-weight:800;font-size:{mark_size}px;line-height:.8;color:var(--red-ink);letter-spacing:-.06em;margin:-8px 0 8px">“</div>
  <p style="font-weight:700;font-size:{size}px;line-height:1.2;letter-spacing:-.02em">{e(q)}”</p>
  <p style="margin-top:18px;font-family:Syne,sans-serif;font-weight:800;font-size:{title_size}px;line-height:1.15;letter-spacing:-.03em;color:var(--red-ink)">{e(c["title"])}</p>
  {sub}
</div>
""" + foot

    if layout == "bignum":
        num_size = 168 if h >= 675 else 148
        label_size = 42 if h >= 675 else 36
        sub_size = 24 if h >= 675 else 22
        top = 118 if h >= 675 else 104
        return header + f"""
<div style="position:absolute;left:{pad}px;right:{pad}px;top:{top}px;bottom:{h-foot_y+20}px;display:flex;flex-direction:column;justify-content:center;gap:18px">
  <div style="align-self:flex-start;background:var(--och);color:var(--ink);border:3px solid var(--ink);box-shadow:8px 8px 0 var(--ink);border-radius:28px 48px 24px 36px;padding:10px 36px 16px;font-family:Syne,sans-serif;font-weight:800;font-size:{num_size}px;line-height:.95;letter-spacing:-.05em">{e(c["number"])}</div>
  <p style="font-family:Syne,sans-serif;font-weight:800;font-size:{label_size}px;line-height:1.15;letter-spacing:-.03em;max-width:18ch">{e(c["label"])}</p>
  <p style="font-size:{sub_size}px;font-weight:500;color:var(--mut)">{e(c["sub"])}</p>
</div>
""" + foot

    if layout == "beforeafter":
        head_size = 52 if h >= 675 else 44
        val_size = 48 if h >= 675 else 40
        cap_size = 22 if h >= 675 else 20
        top = 118 if h >= 675 else 104
        bv, bl = c["before"]
        av, al = c["after"]
        return header + f"""
<div style="position:absolute;left:{pad}px;right:{pad}px;top:{top}px;bottom:{h-foot_y+20}px;display:flex;flex-direction:column;justify-content:center;gap:28px">
  <h1 style="font-family:Syne,sans-serif;font-weight:800;font-size:{head_size}px;letter-spacing:-.04em;line-height:1">{e(c["headline"])}</h1>
  <div style="display:flex;align-items:center;gap:28px">
    <div class="paper" style="flex:1;border-radius:24px;padding:28px 28px 24px">
      <p style="font-family:Syne,sans-serif;font-weight:800;font-size:{val_size}px;letter-spacing:-.04em;color:var(--mut);line-height:1">{e(bv)}</p>
      <p style="margin-top:10px;font-size:{cap_size}px;font-weight:500;color:var(--mut)">{e(bl)}</p>
    </div>
    <div style="flex:none;width:64px;height:64px;background:var(--blue);border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);border-radius:50%;display:flex;align-items:center;justify-content:center">
      <svg width="32" height="32" viewBox="0 0 32 32" aria-hidden="true"><path d="M6 16h16M16 8l8 8-8 8" fill="none" stroke="#fff" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/></svg>
    </div>
    <div style="flex:1;background:var(--och);color:var(--ink);border:3px solid var(--ink);box-shadow:7px 7px 0 var(--ink);border-radius:24px;padding:28px 28px 24px">
      <p style="font-family:Syne,sans-serif;font-weight:800;font-size:{val_size}px;letter-spacing:-.04em;line-height:1.05">{e(av)}</p>
      <p style="margin-top:10px;font-size:{cap_size}px;font-weight:500">{e(al)}</p>
    </div>
  </div>
</div>
""" + foot

    if layout == "compare":
        head_size = 48 if h >= 675 else 40
        val_size = 36 if h >= 675 else 32
        row_size = 26 if h >= 675 else 22
        top = 118 if h >= 675 else 104
        return header + f"""
<div style="position:absolute;left:{pad}px;right:{pad}px;top:{top}px;bottom:{h-foot_y+20}px;display:flex;flex-direction:column;justify-content:center;gap:22px">
  <h1 style="font-family:Syne,sans-serif;font-weight:800;font-size:{head_size}px;letter-spacing:-.04em;line-height:1.05">{e(c["headline"])}</h1>
  <div style="display:flex;justify-content:flex-end;gap:16px">
    <span class="pill" style="font-size:16px;background:var(--paper);box-shadow:3px 3px 0 var(--ink)">{e(c["left_pill"])}</span>
    <span class="pill" style="font-size:16px">{e(c["right_pill"])}</span>
  </div>
  <div class="paper" style="border-radius:24px;padding:26px 32px;display:flex;align-items:center;justify-content:space-between;gap:24px">
    <p style="font-size:{row_size}px;font-weight:600">{e(c["row"])}</p>
    <div style="display:flex;align-items:center;gap:20px">
      <span style="font-family:Syne,sans-serif;font-weight:800;font-size:{val_size}px;letter-spacing:-.03em;color:var(--mut)">{e(c["left"])}</span>
      <span style="background:var(--blue);color:#fff;border:3px solid var(--ink);box-shadow:4px 4px 0 var(--ink);border-radius:16px;padding:8px 16px;font-family:Syne,sans-serif;font-weight:800;font-size:{val_size}px;letter-spacing:-.03em;line-height:1.1">{e(c["right"])}</span>
    </div>
  </div>
</div>
""" + foot

    raise ValueError(c["layout"])


def render_tip(c, dest, w, h):
    body = shapes() + tip_body(c, w, h)
    # A small lead bot perched on the lower right of the paper, above the footer, for quote cards only — skip if it would collide.
    # Keep art in the corner shapes + brand head only, so text never fights a robot.
    page = wrap_page(w, h, body)
    screenshot(page, dest, w, h)


def render_all_tips():
    os.makedirs(TIPS_DIR, exist_ok=True)
    for c in TIPS:
        webp = os.path.join(TIPS_DIR, c["slug"] + ".webp")
        og = os.path.join(TIPS_DIR, c["slug"] + "-og.jpg")
        render_tip(c, webp, 1200, 675)
        render_tip(c, og, 1200, 630)
        print("wrote", os.path.basename(webp), os.path.basename(og))


def render_og_default(dest):
    w, h = 1200, 630
    body = shapes("og") + f"""
<div style="position:absolute;right:40px;bottom:122px">{bot(size="88px")}</div>
<div style="position:absolute;right:175px;bottom:132px">{bot(c="var(--blue)", hr=".16em", a="var(--red)", size="64px")}</div>
<div style="position:absolute;right:300px;bottom:126px">{bot(c="var(--och)", hr="50% 50% .4em .4em", a="var(--blue)", big=True, size="74px")}</div>
<div class="brand" style="position:absolute;left:64px;top:48px;font-size:30px">{LEAD}<span>NextAiBreakout</span></div>
<div style="position:absolute;left:64px;right:430px;top:150px">
  <p class="note" style="font-size:28px;transform:rotate(-1.5deg);margin-bottom:18px">Grok Bot first. One page for Claude.</p>
  <h1 style="font-family:Syne,sans-serif;font-weight:800;font-size:64px;line-height:1.02;letter-spacing:-.045em;max-width:14ch">Grok Bot tips, with the real build behind each one.</h1>
</div>
<div style="position:absolute;left:64px;right:64px;bottom:48px;border-top:3px solid var(--ink);padding-top:18px;display:flex;justify-content:space-between;align-items:center;font-size:22px;font-weight:500">
  <span style="color:var(--mut)">nextaibreakout.com</span>
  <span style="font-family:Syne,sans-serif;font-weight:800;letter-spacing:-.02em">Tips · Claude · Blog · About</span>
</div>
"""
    page = wrap_page(w, h, body)
    screenshot(page, dest, w, h)
    print("wrote", dest)


# ---- X cards, 1600x900, tip + Pros + Cons + footer ----
X_CARDS = [
    dict(day=1, title="Talk to one lead bot",
         tip="I don't talk to my whole Grok Bot fleet. I talk to one lead bot, and it routes work to the specialists.",
         pro="One inbox, clear routing.", con="If the lead bot stalls, everything waits."),
    dict(day=2, title="Quality Checker in front of you",
         tip="A Quality Checker bot reviews my bots' work before it reaches me. Public posts and anything risky get the full review; daily news posts go through an automated gate instead. I want one reviewed answer, not five versions of \"done.\"",
         pro="Fewer bad handoffs to me.", con="Another hop, and it can hold work I wanted sooner."),
    dict(day=3, title="Agent-to-agent handoffs",
         tip="Specialists don't report to me. They hand work to each other with a clear output, and the lead bot brings me one result.",
         pro="Fewer pings.", con="A sloppy handoff can stall the chain, and I see it later."),
    dict(day=4, title="Sends, spending and sign-ins wait for my OK",
         tip="Sends, spending and sign-ins still wait for my OK. My queued X tip posts go out on a schedule after my checker bot reviews them.",
         pro="No surprise posts on my account.", con="Other work waits while I'm away, even if it's ready."),
    dict(day=5, title="Save working workflows as skills",
         tip="When a workflow works, I save it as a skill and share it across bots so they don't reinvent the steps.",
         pro="Same playbook, less retyping.", con="A stale skill will be reused until you update or drop it."),
    dict(day=6, title="Check the timezone on every routine",
         tip="I had a routine on the wrong timezone. It quietly missed its slot, and I only noticed when the work didn't show up.",
         pro="One check prevents a silent miss.", con="Easy to assume the zone is already right."),
    dict(day=7, title="Watch usage, then pause routines",
         tip="Usage ran out and every routine failed at once. Now I watch the meter and pause routines before they all crash.",
         pro="You choose what stops.", con="Paused work doesn't run, so you have to restart it later."),
    dict(day=8, title="We built Blabara in one day",
         tip="On Oct 16, my brother and I built Blabara, an Android voice-dictation app, in one day with a team of Grok Bots.",
         pro="A small, directed team can finish something real.", con="You still have to direct them."),
    dict(day=9, title="One group chat per project",
         tip="When bots share a project, I put them in one group chat with clear roles, then close it when the work is done.",
         pro="Handoffs stay in one place.", con="A busy channel gets noisy if roles aren't tight."),
    dict(day=10, title="No fix without a before and after",
         tip="No bug is fixed until it's proven with a before and after. A bot saying \"done\" isn't proof.",
         pro="Fewer false dones.", con="Real fixes take longer to close."),
    dict(day=11, title="One-tap approvals for spend and credentials",
         tip="Spending and credentials stay on a one-tap approval. A bot can draft the step. I still press the button.",
         pro="Nothing spends or signs in on its own.", con="Those steps wait on me."),
    dict(day=12, title="Bot drafts the email, a checker reviews it",
         tip="I had a bot build a daily email, then a checker bot review it before anything could go out. Fast draft, slow send.",
         pro="Speed on the draft, a brake on the send.", con="Two bots, and it still waits for my yes."),
    dict(day=13, title="Script the cards, don't redesign every post",
         tip="I don't design a new image for every post. A script builds the cards in one brand style: same colours, same type, no photos of people.",
         pro="The feed stays consistent.", con="A bad template gets copied onto every card."),
    dict(day=14, title="Daily news posts go out after a gate",
         tip="Daily news posts write, pass an automated gate, and go out to the site and X on a schedule.",
         pro="News can go out on a schedule after a gate.", con="A schedule without a gate publishes mistakes on time."),
]


def tip_font(text):
    n = len(text)
    if n > 180:
        return 42
    if n > 140:
        return 46
    if n > 100:
        return 50
    return 54


def render_x_card(c, dest):
    w, h = 1600, 900
    pad = 80
    size = tip_font(c["tip"])
    body = shapes() + f"""
{topbar(pad, 32, "Day {0}".format(c["day"]), 22)}
<div style="position:absolute;left:{pad}px;right:{pad}px;top:168px;bottom:128px;display:flex;flex-direction:column">
  <p class="note" style="font-size:32px;transform:rotate(-1.2deg);align-self:flex-start">{e(c["title"])}</p>
  <p style="margin-top:18px;font-weight:700;font-size:{size}px;line-height:1.2;letter-spacing:-.02em">{e(c["tip"])}</p>
  <div style="margin-top:auto;display:flex;gap:32px;align-items:stretch">
    <div class="paper" style="flex:1;border-radius:24px;padding:28px 32px">
      <p style="font-family:Syne,sans-serif;font-weight:800;font-size:22px;letter-spacing:-.02em;color:var(--blue);text-transform:uppercase;margin-bottom:10px">Pros</p>
      <p style="font-weight:700;font-size:32px;line-height:1.25;letter-spacing:-.02em">{e(c["pro"])}</p>
    </div>
    <div class="paper" style="flex:1;border-radius:24px;padding:28px 32px">
      <p style="font-family:Syne,sans-serif;font-weight:800;font-size:22px;letter-spacing:-.02em;color:var(--red-ink);text-transform:uppercase;margin-bottom:10px">Cons</p>
      <p style="font-weight:700;font-size:32px;line-height:1.25;letter-spacing:-.02em">{e(c["con"])}</p>
    </div>
  </div>
</div>
{footer_bar(pad, 820, 24, w - 2 * pad)}
"""
    page = wrap_page(w, h, body)
    screenshot(page, dest, w, h)
    html_dest = dest.rsplit(".", 1)[0] + ".html"
    # keep the source next to day1 for later tweaks; only write for day 1 to match prior practice? write all as .html maybe noisy.
    print("wrote", dest)


def render_x_cards():
    os.makedirs(X_DIR, exist_ok=True)
    day1 = os.path.join(X_DIR, "day1.png")
    bak = os.path.join(X_DIR, "day1.png.bak-teal")
    if os.path.isfile(day1) and not os.path.isfile(bak):
        shutil.copy2(day1, bak)
        print("backed up", bak)
    for c in X_CARDS:
        dest = os.path.join(X_DIR, f"day{c['day']}.png")
        render_x_card(c, dest)
    # write day1.html in the new palette so the source stays next to the card
    # (rendered already)


def main():
    args = sys.argv[1:]
    do_tips = "--x-cards-only" not in args
    do_x = "--x-cards" in args or "--x-cards-only" in args
    if do_tips:
        render_all_tips()
        # Default OG is the photo card. Do not overwrite it with the cut-outs drawing.
        from render_og_photo import main as render_og_photo
        render_og_photo()
    if do_x:
        render_x_cards()


if __name__ == "__main__":
    main()
