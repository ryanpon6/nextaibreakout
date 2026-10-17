// nab-refresh-watchdog: if the live site is stale, ask GitHub Actions to run hourly-refresh now.
// Dry-run (logs only) when GH_DISPATCH_TOKEN is not set, which is always the case in local `wrangler dev`.
export default {
  async scheduled(controller, env, ctx) {
    const r = await fetch(`${env.SITE}/data.json?cb=${Date.now()}`, { headers: { "cache-control": "no-cache", "user-agent": "nab-watchdog/1" } });
    let gen = null, age = Infinity;
    try { gen = (await r.json()).generated; age = (Date.now() - Date.parse(gen)) / 60000; } catch (e) { /* unreadable -> treat as stale */ }
    const stale = !(age < Number(env.MAX_AGE_MIN));
    console.log(JSON.stringify({ cron: controller.cron, status: r.status, generated: gen, age_min: Math.round(age), stale }));
    if (!stale) return;
    if (!env.GH_DISPATCH_TOKEN) { console.log(`DRY RUN: would POST workflow_dispatch ${env.GH_REPO}/${env.GH_WORKFLOW} (ref main)`); return; }
    const d = await fetch(`https://api.github.com/repos/${env.GH_REPO}/actions/workflows/${env.GH_WORKFLOW}/dispatches`, {
      method: "POST", body: JSON.stringify({ ref: "main" }),
      headers: { authorization: `Bearer ${env.GH_DISPATCH_TOKEN}`, accept: "application/vnd.github+json", "user-agent": "nab-watchdog/1", "x-github-api-version": "2022-11-28" } });
    console.log(`dispatch -> ${d.status}`);
    if (d.status !== 204) throw new Error(`dispatch failed ${d.status}`);  // shows as a failed Cron Event in the dashboard
  },
  async fetch() { return new Response("nab-refresh-watchdog: cron only", { status: 404 }); },
};
