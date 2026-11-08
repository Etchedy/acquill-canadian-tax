# Claude and ChatGPT directory submission: status

Name: **Acquill Canadian Tax**. The original name ("Canadian Tax MCP by Acquill") broke OpenAI's rules: display
names are at most 30 characters and must not add "MCP", "MCP Server" or "Plugin". Claude accepts up to 100
characters; the same name is used on both. Requirements were re-checked against the official pages on
2026-11-08 (links below).

## Done in the code

| Requirement | Platform | Where |
|---|---|---|
| Every tool has a title | Claude | `server.py` |
| `readOnlyHint`, `destructiveHint`, `openWorldHint` explicit on every tool | both | `READ` in `server.py` |
| Streamable HTTP endpoint at `/mcp`, no authentication | both | `server.py` |
| Tool names short, plain verbs, narrow accurate descriptions | both | `server.py` |
| Actionable errors (`source_unavailable` with detail, never a bare 500) | Claude | `server.py`, `service.py` |
| Documentation page with tools, limits and four example prompts (Claude asks for at least three) | both | `/docs` |
| Privacy, terms and support pages | both (terms: OpenAI) | `/privacy`, `/terms`, `/support` |
| Domain verification file | OpenAI | `/.well-known/openai-apps-challenge` (from `OPENAI_APPS_CHALLENGE`) |
| AI clients' origins accepted (an over-strict Origin check rejects Claude) | Claude | `allowed_origins` in `server.py` |
| Logo: Acquill icon, square 512 px PNG and SVG | both | `assets/icon.png`, `assets/icon.svg` |
| Five positive and three negative review cases | OpenAI | `marketplace/review-cases.json` |
| Package: `plugin.json` + `mcp.json` ZIP and a Claude worksheet | OpenAI / Claude | `scripts/package_marketplaces.py` |
| Hosting config and a self-building, self-refreshing CRA index | both | `fly.toml`, `Dockerfile.fly`, `DEPLOY-FLY.md` |
| Tests: 36 unit/contract tests; live check of all six tools against CRA, Justice Canada and A2AJ | both | `tests/`, `scripts/smoke.py` (PASS 2026-11-08, local) |

## Still needed, in order

1. **Deploy** to `https://tax.acquill.com` (see `DEPLOY-FLY.md`). Needs the Fly account behind acquill.com and a
   go-ahead on the small hosting cost.
2. **Public contact and operator: set.** Operator "Acquill", contact support@acquill.com (in `fly.toml` and the
   packaging script). Check that Cloudflare Email Routing delivers `support@` to a monitored inbox.
3. **Test in Claude**: Settings, Connectors, Add custom connector, `https://tax.acquill.com/mcp`; call every tool.
   Also `npx @modelcontextprotocol/inspector --cli https://tax.acquill.com/mcp --transport http --method tools/list`.
4. **Test in ChatGPT**: developer mode, add the custom MCP server, run all five positive and three negative cases.
5. **Record a demo video** of the deployed connector working in ChatGPT (OpenAI requires `demo_recording_url`;
   Claude does not accept video).
6. **Build the packages**:
   `python scripts/package_marketplaces.py --base-url https://tax.acquill.com --demo-url <video>`.
7. **OpenAI**: verify the individual or business in platform.openai.com organization settings; upload the ZIP
   at platform.openai.com/plugins (With MCP); put the domain token in `OPENAI_APPS_CHALLENGE`; fix scan findings;
   submit for review.
8. **Claude**: needs a paid claude.ai plan (Pro or higher; on Team/Enterprise an Owner). claude.ai/directory/manage,
   Submit new, MCP connector; paste the worksheet's fields; answer the Data handling step (see the risk below).

## Biggest review risk: third-party data

Both directories prefer services over the publisher's own APIs. OpenAI rejects "pass-through intermediary"
connectors; Claude asks whether the API is yours, proxied with permission, or a third party's. CRA, Justice
Canada and A2AJ aren't Acquill's. The listing should lead with what Acquill adds (its own CRA index and passage
search, combined search across three sources, coverage reporting, citation-safe paragraph extraction), and
`RIGHTS.md` should be settled first: Crown copyright reuse terms for CRA and Justice Laws, and A2AJ's terms for
commercial reuse. Neither directory requires a tax-advice disclaimer, but the terms and docs already say the
service is research material, not individualized advice.

## Sources

- Claude: https://claude.com/docs/connectors/building/submission, …/review-criteria, …/testing,
  …/authentication, https://claude.com/docs/directory/publish,
  https://support.claude.com/en/articles/13145358-anthropic-software-directory-policy
- OpenAI: https://developers.openai.com/plugins/deploy/submission,
  https://developers.openai.com/plugins/plugin-guidelines, https://developers.openai.com/plugins/build/plugins
