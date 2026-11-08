# Deploying to Cloudflare (tax.acquill.com), free plan

The hosted connector is the Cloudflare Worker in `worker/` (same six tools, inputs, outputs and public pages as the
Python server, which Acquill still runs locally). The CRA index lives in a Cloudflare D1 database; a GitHub
Actions job rebuilds it monthly.

## What it costs: nothing at this scale
Cloudflare's free plan, no card needed: Workers 100,000 requests a day; D1 5 GB storage (the index is about 10 MB),
5 million rows read and 100,000 rows written a day. The monthly refresh writes only changed publications. GitHub
Actions minutes for the private repo come from the free 2,000 a month (the refresh takes about 5).

**One limit to watch:** the free plan allows about 10 ms of CPU per request. Search and the indexed CRA reads use
D1 and need almost none, but reading a very large page live (`get_cra_publication` on a 1 MB CRA guide, or a long
statute section) parses the whole page and may exceed it; such a request then fails with an error rather than
slowing down. If that shows up in testing, the Workers Paid plan (US$5/month, 30 s CPU) removes it.

## Steps (about 15 minutes)
1. Sign in to the Cloudflare account that holds acquill.com (its DNS is already on Cloudflare), from `worker/`:
   `npx wrangler login`.
2. Create the database and put its id into `wrangler.jsonc` (`database_id`):
   `npx wrangler d1 create acquill-tax-cra`
3. Create the tables and load the index (build `data/cra.sqlite3` first with `python -m canadian_tax_mcp.ingest`
   if it is missing; the first load writes about 20,000 rows, a fifth of a day's free writes):
   `npx wrangler d1 execute acquill-tax-cra --remote --file schema.sql`
   `python ../scripts/export_d1.py --db ../data/cra.sqlite3 --out build/cra.sql`
   `npx wrangler d1 execute acquill-tax-cra --remote --file build/cra.sql`
4. Deploy: `npm run deploy`. It answers at `https://acquill-tax.<account>.workers.dev` straight away.
5. Custom domain: uncomment the `routes` line in `wrangler.jsonc` (`tax.acquill.com`, `custom_domain: true`) and
   deploy again; Cloudflare creates the DNS record and certificate itself. This needs acquill.com in the same
   Cloudflare account. Until then, set `PUBLIC_URL` to the workers.dev address.
6. Check: `node test/smoke.mjs https://tax.acquill.com` (calls every tool live and checks the pages).
7. Monthly refresh: in the GitHub repo's Settings, Secrets and variables, Actions, add `CLOUDFLARE_ACCOUNT_ID`
   and `CLOUDFLARE_API_TOKEN` (a token with D1 Edit for this account). Run "Refresh CRA index" once by hand to
   confirm it, then it runs on the 1st of each month.
8. For OpenAI's domain check: `npx wrangler secret put OPENAI_APPS_CHALLENGE` with the token from the plugin
   dashboard (served at `/.well-known/openai-apps-challenge`).

Don't put a Cloudflare WAF rule, bot fight mode or a challenge in front of `/mcp`: Claude's connector traffic
comes from `160.79.104.0/21` and ChatGPT's from OpenAI's ranges, and both must reach it.

## Testing locally (no Cloudflare account)
From `worker/`: `npm install`, then
`npx wrangler d1 execute acquill-tax-cra-local --env local --local --file schema.sql`,
`python ../scripts/export_d1.py --db ../data/cra.sqlite3 --out build/cra.sql`,
`npx wrangler d1 execute acquill-tax-cra-local --env local --local --file build/cra.sql`,
`npm run dev`, and in another terminal `npm run smoke`. `test/compare_python.py` (run from the repo root with the
Worker running) checks that the Worker extracts exactly the same text as the Python server from live pages.
