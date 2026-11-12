/**
 * Retire old ranking-product paths for the Grok Bot / Claude relaunch.
 * 301 only where a real new page exists. 410 for the rest of the old prefixes.
 * Tightly scoped: this function is only invoked for the include list in _routes.json.
 * It must never handle /, /tips/*, /claude/*, /blog/*, /about, assets,
 * sitemap.xml, robots.txt, llms.txt, feed.xml, or /data.json.
 */
const TIPS = "/tips/";
const ABOUT = "/about";

const REDIRECTS = {
  "/grok-bot": TIPS,
  "/grok-bot/": TIPS,
  "/about.html": ABOUT,
};

const RETIRED = [
  "/item",
  "/daily",
  "/labs",
  "/github",
  "/huggingface",
  "/npm",
  "/pypi",
  "/breakouts",
  "/agents",
  "/models",
  "/today",
  "/frontier",
  "/archive",
];

function isRetired(path) {
  for (const pre of RETIRED) {
    if (path === pre || path === pre + "/" || path.startsWith(pre + "/")) return true;
  }
  return false;
}

function isProtected(path) {
  if (path === "/" || path === "") return true;
  const keep = [
    "/tips",
    "/claude",
    "/blog",
    "/about",
    "/sitemap.xml",
    "/robots.txt",
    "/llms.txt",
    "/data.json",
    "/feed.xml",
    "/favicon.svg",
    "/style.css",
    "/tips.css",
    "/og.png",
    "/og-default.png",
    "/fonts",
  ];
  for (const p of keep) {
    if (path === p || path === p + "/" || path.startsWith(p + "/") || path.startsWith(p + "?")) return true;
  }
  return false;
}

const GONE = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>This page was retired | NextAiBreakout</title>
<meta name="robots" content="noindex">
<meta name="color-scheme" content="dark">
<meta name="theme-color" content="#274043">
<style>
body{margin:0;background:#274043;color:#F5F1E8;font:400 18px/1.55 Archivo,Helvetica Neue,Arial,sans-serif;padding:48px 24px}
main{max-width:40rem;margin:0 auto}
h1{color:#B8A188;font-weight:800;font-size:clamp(32px,6vw,48px);line-height:1.05;margin:0 0 16px}
p{color:#D8D0C6}
a{color:#BCA68E}
</style>
</head>
<body>
<main>
<h1>This page was retired.</h1>
<p>This ranking page is gone. NextAiBreakout is now a Grok Bot tips site, with a separate page for Claude.</p>
<p><a href="/tips/">See current Grok Bot tips</a> · <a href="/">Home</a></p>
</main>
</body>
</html>`;

export async function onRequest(context) {
  const url = new URL(context.request.url);
  const path = url.pathname;

  if (isProtected(path)) return context.next();

  if (Object.prototype.hasOwnProperty.call(REDIRECTS, path)) {
    return Response.redirect(new URL(REDIRECTS[path], url.origin), 301);
  }

  if (isRetired(path)) {
    return new Response(GONE, {
      status: 410,
      headers: {
        "content-type": "text/html; charset=utf-8",
        "x-robots-tag": "noindex",
        "cache-control": "public, max-age=3600",
      },
    });
  }

  return context.next();
}
