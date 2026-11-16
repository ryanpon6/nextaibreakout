#!/usr/bin/env python3
"""Step 2: turn the AI-written spec into a finished news post in the Bot Cut-outs design.

Input  story-DATE.json (fetch.py) + spec-DATE.json (written by the routine's agent; format in README.md).
Output blog/posts/DATE-slug.md (kind: news, status: published, per-post share card),
       static/images/news/DATE-slug.png (1200x630 OG / X summary card, also shown at the top of the post),
       $NAB_NEWS_STATE/cards/DATE-slug-x.png (1600x900 card attached to the X post),
       $NAB_NEWS_STATE/xpayload-DATE.json (main post text, card, alt, reply link) for publish.py.
The page goes through blog.py like every other post, so it gets the design, /blog/ listing, homepage
"Latest posts", sitemap.xml, feed.xml, llms.txt, Article + Breadcrumb schema and the share card.
x_main and body_md must already open with a hook line (G13); this script does not invent one.
--site-only (lessons only): page only. Writes the post md, the OG card and the catalog entry; writes NO X card and NO
       xpayload, so publish.py has nothing to post. Without --story it builds the lesson story from the spec in memory
       (nothing is written to $NAB_NEWS_STATE). Use it to put a QC-passed lesson on the site without an X post: commit the
       outputs and ship them with the normal site release. The new post also trips lessons.already_posted(), so the same
       slug can never be posted to X later from lessons/.
Lesson Sources line (lesson_sources_md): the spec's internal "sources"/"evidence" notes are never printed.
       public_sources (list of QC-passed public lines) wins; else the fixed queued-drafts line, only when the body really
       quotes "- Before:"/"- After:" lines and the evidence includes our x-drafts file; else "- NOTE No outside posts are cited."
Usage  make_post.py [--date YYYY-MM-DD] [--spec PATH] [--story PATH] [--site-only]"""
import argparse, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import nc
sys.path.insert(0, nc.ROOT); sys.path.insert(0, os.path.join(nc.ROOT, "brand"))
import render_cutouts as R

REPLY_FMT = "Full story + sources: {url}"   # same wording as xpost.py
REQ = ("slug", "title", "description", "body_md", "related_tips", "x_main", "card_headline", "card_points", "image_alt", "note")
DRAFTS_LINE = "- Every before and after line is quoted word for word from our own queued X drafts for @ryanpon."

def lesson_sources_md(spec, story=None):
    """Sources list for a lesson page (a lesson cites no X posts). The fixed drafts line is printed only when it is true."""
    pub = [str(x).strip() for x in (spec.get("public_sources") or []) if str(x).strip()]
    if pub: return "\n".join(x if x.startswith("- ") else "- " + x for x in pub)
    body = spec.get("body_md") or ""
    ba = re.search(r"(?im)^\s*[-*]\s*Before:\s*\S", body) and re.search(r"(?im)^\s*[-*]\s*After:\s*\S", body)
    ev = [e if isinstance(e, str) else (e or {}).get("file") or (e or {}).get("path") or "" for e in (spec.get("evidence") or (story or {}).get("evidence") or [])]
    if ba and any(os.path.basename(str(e)).startswith("x-drafts") for e in ev): return DRAFTS_LINE
    note = str(spec.get("note") or "").strip()
    if not note: return ""
    return f"- {note if note[-1] in '.!' else note + '.'} No outside posts are cited."

def q(s): return '"' + str(s).replace("\\", "").replace('"', '\\"') + '"'

def card_html(w, h, spec, story, date):
    posts = story.get("posts") or []
    src = next((p for p in posts if p["id"] == str(spec.get("card_source", ""))), posts[0] if posts else None)
    if src:
        credit = f"Source: @{R.e(src['user'])} on X"
    else:
        credit = "Source: lessons we learned"
    big = w >= 1600; pad = 80 if big else 60
    hs = 76 if big else 54
    pts = "".join(f'<li style="margin:0 0 {14 if big else 8}px">{R.e(p)}</li>' for p in spec["card_points"][:3])
    body = R.shapes("og" if not big else "default") + R.topbar(pad, 32 if big else 26, "Claude news" if (story.get("topic")=="claude" or story.get("kind")=="claude") else ("Lessons we learned" if story.get("source")=="lesson" or story.get("topic")=="lesson" else "Grok Bot news"), 22 if big else 18) + f"""
<div style="position:absolute;right:{pad}px;bottom:{170 if big else 118}px">{R.bot(size="96px" if big else "70px")}</div>
<div style="position:absolute;right:{pad + (150 if big else 110)}px;bottom:{176 if big else 124}px">{R.bot(c="var(--och)", hr="50% 50% .4em .4em", a="var(--blue)", big=True, size="78px" if big else "58px")}</div>
<div style="position:absolute;left:{pad}px;right:{360 if big else 280}px;top:{170 if big else 120}px">
  <p class="note" style="font-size:{32 if big else 26}px;transform:rotate(-1.2deg);margin-bottom:{18 if big else 10}px">{R.e(spec["note"])}</p>
  <h1 style="font-family:Syne,sans-serif;font-weight:800;font-size:{hs}px;line-height:1.02;letter-spacing:-.045em">{R.e(spec["card_headline"])}</h1>
  <ul class="paper" style="list-style:none;margin-top:{28 if big else 18}px;border-radius:22px;padding:{24 if big else 16}px {30 if big else 22}px {12 if big else 8}px;font-weight:700;font-size:{34 if big else 24}px;line-height:1.2;letter-spacing:-.02em;display:inline-block">{pts}</ul>
</div>
<div style="position:absolute;left:{pad}px;right:{pad}px;bottom:{44 if big else 36}px;border-top:3px solid var(--ink);padding-top:16px;display:flex;justify-content:space-between;font-size:{24 if big else 19}px;font-weight:500">
  <span style="color:var(--mut)">{credit}</span><span style="font-family:Syne,sans-serif;font-weight:800">nextaibreakout.com</span>
</div>"""
    return R.wrap_page(w, h, body)

def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument("--date", default=nc.today()); ap.add_argument("--spec"); ap.add_argument("--story")
    ap.add_argument("--site-only", action="store_true", help="lessons only: page, OG card and catalog entry; no X card, no xpayload (nothing for publish.py to post)")
    a = ap.parse_args(argv)
    spec = nc.load(a.spec or nc.path("spec", a.date))
    miss = [k for k in REQ if not spec.get(k)]
    if miss: print("SPEC MISSING: " + ", ".join(miss)); return 2
    slug = re.sub(r"[^a-z0-9-]", "", spec["slug"].lower()).strip("-")[:70]
    if a.site_only and spec.get("source") != "lesson": print("SITE-ONLY: only for lesson specs (source: lesson)"); return 2
    if a.site_only and not a.story:
        story = {"key": slug, "topic": "lesson", "source": "lesson", "posts": [],
                 "kind": "claude" if str(spec.get("kind") or "").lower() == "claude" else "grok", "evidence": spec.get("evidence") or []}
    else:
        story = nc.load(a.story or nc.path("story", a.date))
    import tips as T
    allt = {t["slug"]: t["title"] for t in T.TIPS}
    rel = [s for s in spec["related_tips"] if s in allt][:3]
    if len(rel) < 2: print("SPEC: need 2 related_tips that exist in tips.TIPS"); return 2
    base = f"{a.date}-{slug}"
    img_rel = f"/images/news/{base}.png"
    os.makedirs(nc.NEWS_IMG, exist_ok=True)
    og = os.path.join(nc.NEWS_IMG, f"{base}.png")
    R.screenshot(card_html(1200, 630, spec, story, a.date), og, 1200, 630)
    xc = None
    if not a.site_only:
        xdir = os.path.join(nc.STATE, "cards"); os.makedirs(xdir, exist_ok=True); xc = os.path.join(xdir, f"{base}-x.png")
        R.screenshot(card_html(1600, 900, spec, story, a.date), xc, 1600, 900)
    lesson = story.get("source") == "lesson" or story.get("topic") == "lesson" or spec.get("source") == "lesson"
    cited = [p for p in (story.get("posts") or []) if p.get("url") and p["url"] in spec["body_md"]]
    if not cited and not lesson: print("SPEC: body_md must link at least one verified post URL"); return 2
    import datetime as dt
    when = lambda p: dt.datetime.fromisoformat(p["created_at"].replace("Z", "+00:00")).astimezone(nc.MT).strftime("%b %-d, %Y")
    src_md = "\n".join(f"- [{p.get('name') or p['user']} (@{p['user']}) on X]({p['url']}), {when(p)}" for p in cited)
    if story.get("news_url"): src_md += f"\n- [X's news summary of the story]({story['news_url']})"
    if lesson and not src_md.strip():   # rule 19: never ship an empty Sources section
        src_md = lesson_sources_md(spec, story)
    if not src_md.strip(): print("SPEC: Sources section would be empty"); return 2
    rel_md = "\n".join(f"- [{allt[s]}](/tips/{s}/)" for s in rel)
    fm = {"title": spec["title"], "description": spec["description"], "date": a.date, "status": "published", "slug": slug, "kind": "news",
          "story_key": story["key"], "image": img_rel, "image_alt": spec["image_alt"],
          "sources": ", ".join(p["url"] for p in cited)}
    for k in ("seo_title", "seo_description", "keywords"):
        if spec.get(k): fm[k] = spec[k]
    md = "---\n" + "\n".join(f"{k}: {q(v)}" for k, v in fm.items()) + "\n---\n\n" + spec["body_md"].strip() + \
         f"\n\n## Sources\n\n{src_md}\n\n## Related Grok Bot tips\n\n{rel_md}\n"
    os.makedirs(nc.POSTS, exist_ok=True)
    mdp = os.path.join(nc.POSTS, f"{base}.md"); open(mdp, "w", encoding="utf-8").write(md)
    url = f"{nc.SITE}/blog/{slug}/"
    if a.site_only:
        import entries_hook
        ef = entries_hook.register(a.date, spec["title"], slug, "claude" if story.get("kind") == "claude" else "grok", ["lessons we learned"], spec["description"])
        print(f"WROTE {mdp}\nWROTE {og}\nSITE-ONLY: no X card, no xpayload (publish.py has nothing to post)\nENTRIES {ef}\nURL {url}")
        return 0
    pay = {"date": a.date, "slot": nc.slot(a.date), "slug": slug, "url": url, "post_md": mdp, "og_image": og, "x_card": xc,
           "main": {"text": spec["x_main"].strip(), "card": xc, "alt": spec["image_alt"]},
           "reply": {"text": REPLY_FMT.format(url=url)}}
    import entries_hook   # tips-index integration point (homepage strips, /tips/, Claude index)
    if lesson:
        kind_topic = "claude" if str(story.get("kind") or "").lower() == "claude" else "grok"
        sources = ["lessons we learned"]  # don't put internal evidence paths in the committed catalog entry
    else:
        kind_topic = story["topic"]
        sources = [p["url"] for p in cited]
    ef = entries_hook.register(a.date, spec["title"], slug, kind_topic, sources, spec["description"])
    pay["entries_file"] = ef
    nc.save(nc.path("xpayload", a.date), pay)
    print(f"WROTE {mdp}\nWROTE {og}\nWROTE {xc}\nWROTE {nc.path('xpayload', a.date)}\nURL {url}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
