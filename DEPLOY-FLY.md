# Deploying to Fly.io (tax.acquill.com)

acquill.com already runs on Fly.io (app `acquill-web`) with DNS at Cloudflare, so the connector uses the same
provider. This has not been launched yet: it needs the Fly account that owns `acquill-web`, and a spending
decision (the website's notes cap hosting spend).

Cost (Fly's published prices, 2026-11): the 512 MB shared-cpu-1x machine is $3.69/month if it ran all month
(Toronto may be slightly higher); it stops when idle, and a stopped machine costs only its root filesystem
($0.15/GB-month). The 1 GB index volume is $0.15/month. The shared IPv4 address and the first 10 certificates are
free; outbound data is $0.02/GB. So about $0.50-$1.50/month at light use, at most about $4/month. Don't add a
dedicated IPv4 ($2/month); it isn't needed.

`fly.toml` and `Dockerfile.fly` are ready. `Dockerfile.fly` exists because Fly mounts volumes owned by root: the
container hands `/app/data` to the service user, then runs the server without root. It has not been run on Fly
yet; the same image steps run locally under `Dockerfile`.

## Steps (about 10 minutes, by whoever holds the Fly account)

1. Install flyctl and sign in: `winget install Fly-io.flyctl`, then `fly auth login`.
2. From this folder: `fly launch --copy-config --no-deploy` (keep the app name `acquill-tax`, region `yyz`).
3. Create the index volume: `fly volumes create tax_data --region yyz --size 1`.
4. The public contact on the privacy, terms and support pages is `support@acquill.com` (`SUPPORT_EMAIL` in
   `fly.toml`). acquill.com's mail goes through Cloudflare Email Routing: check that `support@` is routed to a
   mailbox someone reads.
5. Deploy: `fly deploy`. On first start the server answers at once and builds its CRA index in the background
   (about 3 minutes, around 150 publications); it rebuilds it every 30 days (`INDEX_REFRESH_DAYS`).
6. Add the domain: `fly certs add tax.acquill.com`, then in Cloudflare DNS add the record Fly prints
   (a CNAME `tax` -> `acquill-tax.fly.dev`, DNS only/grey cloud until the certificate is issued).
7. Check: `https://tax.acquill.com/health`, `/docs`, `/privacy`, `/terms`, `/support`, and
   `python scripts/smoke.py --url https://tax.acquill.com/mcp`.
8. For OpenAI's domain check, set the token from the plugin dashboard:
   `fly secrets set OPENAI_APPS_CHALLENGE=<token>` (served at `/.well-known/openai-apps-challenge`).

Don't put a Cloudflare WAF rule or bot challenge in front of `/mcp`: Claude's connector traffic comes from
`160.79.104.0/21` and must not be blocked.
