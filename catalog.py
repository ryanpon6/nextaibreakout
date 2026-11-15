"""Dated listing catalog for nextaibreakout.com.

This is the source of truth for homepage latest-N strips and the dated
Grok / Claude tip lists. Tip *bodies* still live in tips.py (and the
Claude notes on /claude/); news auto-posts should append here so those
lists update on the next build. See CATALOG.md.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re

from common import ROOT

PATH = os.path.join(ROOT, "catalog.json")
KINDS = {"grok", "claude"}
TYPES = {"tip", "news"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

_cache = None


class CatalogError(ValueError):
    pass


def _load_raw():
    data = json.load(open(PATH, encoding="utf-8"))
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise CatalogError("catalog.json must have an 'entries' list")
    return entries


def validate(entries=None):
    """Raise CatalogError if required fields are missing or duplicated."""
    entries = _load_raw() if entries is None else entries
    seen_ids, seen_urls = set(), set()
    for i, raw in enumerate(entries):
        loc = f"entries[{i}]"
        if not isinstance(raw, dict):
            raise CatalogError(f"{loc} is not an object")
        for key in ("id", "date", "title", "url", "kind", "type"):
            val = raw.get(key)
            if not val or not isinstance(val, str) or not val.strip():
                raise CatalogError(f"{loc} is missing {key}")
        if not DATE_RE.match(raw["date"]):
            raise CatalogError(f"{loc} date must be YYYY-MM-DD, got {raw['date']!r}")
        try:
            dt.date.fromisoformat(raw["date"])
        except ValueError as exc:
            raise CatalogError(f"{loc} invalid date {raw['date']!r}") from exc
        if raw["kind"] not in KINDS:
            raise CatalogError(f"{loc} kind must be grok or claude, got {raw['kind']!r}")
        if raw["type"] not in TYPES:
            raise CatalogError(f"{loc} type must be tip or news, got {raw['type']!r}")
        if not raw["url"].startswith("/"):
            raise CatalogError(f"{loc} url must be a site path starting with /, got {raw['url']!r}")
        if raw["id"] in seen_ids:
            raise CatalogError(f"{loc} duplicate id {raw['id']!r}")
        if raw["url"] in seen_urls:
            raise CatalogError(f"{loc} duplicate url {raw['url']!r}")
        seen_ids.add(raw["id"])
        seen_urls.add(raw["url"])
        seq = raw.get("seq", 0)
        if not isinstance(seq, int):
            raise CatalogError(f"{loc} seq must be an integer if present")
    return entries


def entries():
    """All entries, newest first (date desc, then seq desc, then id)."""
    global _cache
    if _cache is None:
        raw = validate()
        _cache = tuple(
            sorted(
                raw,
                key=lambda e: (e["date"], e.get("seq", 0), e["id"]),
                reverse=True,
            )
        )
    return list(_cache)


def filter_entries(kind=None, type=None):
    out = entries()
    if kind is not None:
        out = [e for e in out if e["kind"] == kind]
    if type is not None:
        out = [e for e in out if e["type"] == type]
    return out


def latest(n, kind=None, type=None):
    """Up to n entries, newest first. Shorter than n if fewer exist. Never pads."""
    if n < 0:
        raise CatalogError("latest() n must be >= 0")
    return filter_entries(kind=kind, type=type)[:n]


def by_url(url):
    for e in entries():
        if e["url"] == url:
            return e
    return None


def by_id(eid):
    for e in entries():
        if e["id"] == eid:
            return e
    return None


def nice(date):
    """'Nov 12, 2026' from YYYY-MM-DD, matching blog.py."""
    return dt.date.fromisoformat(date).strftime("%b %d, %Y").replace(" 0", " ")


def newest_date(kind=None, type=None):
    rows = filter_entries(kind=kind, type=type)
    return rows[0]["date"] if rows else None


def append(entry, path=None):
    """Add or replace an entry by id and write catalog.json. Returns the entry.

    The daily news pipeline should call this (or edit catalog.json the same
    way) after a post is written, then rebuild the site. Does not deploy.
    """
    path = path or PATH
    data = json.load(open(path, encoding="utf-8"))
    rows = list(data.get("entries") or [])
    incoming = dict(entry)
    if "type" not in incoming:
        incoming["type"] = "tip"
    # If seq is omitted, put the new item after any same-date, same-kind rows.
    if "seq" not in incoming:
        same = [r.get("seq", 0) for r in rows if r.get("date") == incoming.get("date") and r.get("kind") == incoming.get("kind")]
        incoming["seq"] = (max(same) + 1) if same else 1
    validate(rows + [incoming] if incoming.get("id") not in {r.get("id") for r in rows} else [
        incoming if r.get("id") == incoming.get("id") else r for r in rows
    ])
    ids = [r.get("id") for r in rows]
    if incoming["id"] in ids:
        rows[ids.index(incoming["id"])] = incoming
    else:
        rows.append(incoming)
    validate(rows)
    data["entries"] = rows
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    global _cache
    _cache = None
    return incoming


def reset_cache():
    global _cache
    _cache = None


def item_list(name, rows, order="descending"):
    """schema.org ItemList for a dated listing, newest first by default."""
    order_url = {
        "descending": "https://schema.org/ItemListOrderDescending",
        "ascending": "https://schema.org/ItemListOrderAscending",
    }[order]
    return {
        "@type": "ItemList",
        "name": name,
        "itemListOrder": order_url,
        "numberOfItems": len(rows),
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i,
                "name": e["title"],
                "url": "https://nextaibreakout.com" + e["url"],
            }
            for i, e in enumerate(rows, 1)
        ],
    }


def listing_html(rows, extra_class=""):
    """List markup using the existing .posts treatment (phone-first, one column). Sorted by catalog date; the date stays in a hidden <time datetime>."""
    from html import escape as e
    if not rows:
        return ""
    cls = "posts" + ((" " + extra_class) if extra_class else "")
    items = []
    for row in rows:
        summary = row.get("summary") or ""
        span = f"<span>{e(summary)}</span>" if summary else ""
        items.append(
            f'<li><a href="{e(row["url"])}">'
            f'<time class="vh" datetime="{e(row["date"])}"></time>'
            f'<b>{e(row["title"])}</b>{span}'
            f'<i aria-hidden="true">→</i></a></li>'
        )
    return f'<ul class="{cls}">{"".join(items)}</ul>'


if __name__ == "__main__":
    rows = validate()
    print(f"catalog OK: {len(rows)} entries")
    for e in entries():
        print(f"{e['date']} seq={e.get('seq', 0)} {e['kind']} {e['type']} {e['url']}")
