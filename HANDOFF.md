# Handoff: Acquill Canadian Tax (formerly "Canadian Tax MCP by Acquill")

## User's intended result

A public connector listed in both ChatGPT and Claude directories, named **Acquill Canadian Tax** (renamed 2026-11-08 to meet OpenAI naming rules; see MARKETPLACES.md), accessing CRA guidance, legislation and A2AJ court decisions. The user wants AI to write and finish the implementation. Do not require them to code. Do not add a companion skill or change the final goal to a custom-only connector.

## Current state

The server and source package are implemented. Six read-only tools expose selected CRA search plus direct CRA HTML retrieval, A2AJ court/federal-law search and retrieval, current official ITA/ETA sections, and coverage reporting. Behavioural improvements live in server code and MCP instructions. A2AJ is called through its documented API; a nested MCP is unnecessary.

Unit/contract checks, live Streamable HTTP integration, and portable manifest schema validation have been run. See `verification/`. Docker was unavailable in the build environment, so the provided Docker/Compose configuration has not been executed. ChatGPT and Claude host-client testing has not been performed. Nothing is publicly deployed, submitted or listed.

Remote Desktop Commander was reachable, but the user's only registered laptop was offline. Do not infer access to the user's machine, DNS, hosting, publisher accounts or Acquill email. No public domain or monitored publisher contact was supplied. The package generator requires real values instead of inventing them.

## Finish in this order

1. Read README, DATA_SOURCES and MARKETPLACES. Preserve the public-directory goal and no-skill requirement.
2. Obtain the actual Acquill domain/subdomain, hosting account and monitored support email from the user or their authorized environment. Do not register paid resources, create recurring bills or accept publisher contracts without the user's authorization.
3. Confirm the intended public/commercial data use is permitted by CRA, Justice and A2AJ's upstream source terms. Preserve attribution and licence metadata. The source package contains no bulk public-document database.
4. Run the supplied crawler to populate the deployment's CRA index. The build tested a sizeable live index, but it is intentionally regenerated from original sources on deployment. Review the ingestion report and any failed pages; do not describe an empty index as complete.
5. Build and test Docker Compose on the actual host. Point DNS to it, configure `.env`, deploy HTTPS, apply platform per-client rate limiting and monitoring, and retain the database volume. Configure an index-refresh job after confirming the host's scheduling mechanism. No scheduler is currently installed.
6. Finalize the included public privacy/terms/support pages to match the real operator and host: contact, jurisdiction, processors, geography and log retention. The included text is a starting draft, not a certified legal policy.
7. Run the live smoke script externally against the public `/mcp`. Test the six tools in both ChatGPT and Claude and capture the actual results. The protocol smoke check does not substitute for client testing. Claude explicitly requires temporary custom-connection testing before a public connector submission.
8. Run `scripts/package_marketplaces.py` with real URLs/contact and a real demonstration recording. Validate the resulting ZIP in OpenAI's dashboard; the checked portable JSON schema does not validate every OpenAI extension or eligibility rule.
9. Complete publisher verification, submit the ChatGPT plugin and Claude remote MCP connector, and resolve review feedback. Do not state that it is available in either marketplace until approved and published. No listing IDs exist yet.

## Useful implementation details

- Python package under `src/canadian_tax_mcp`; `pyproject.toml` provides install/CLI entry points.
- `core.py`: restricted HTTP retrieval, cache, HTML extraction, SQLite FTS index and conservative paragraph parsing.
- `service.py`: source routing, filters, explicit failure/gap statuses and bounded retrieval.
- `server.py`: tool schemas/annotations, MCP instructions, public routes and Streamable HTTP.
- `ingest.py`: operator-only, robots-aware bounded CRA crawler. No crawler/admin mutation is exposed as a model tool.
- `scripts/smoke.py --start-server`: starts a local server and exercises all tools using the MCP SDK and live upstream services.
- `scripts/package_marketplaces.py`: creates the portable ChatGPT package and a Claude worksheet. No companion skill or fake review credentials.
- `assets/`: original geometric starter mark; replace if the user has existing Acquill branding.

## Scope boundaries to preserve

CRA search covers selected English HTML publications, not every CRA page. Direct retrieval can read known English/French CRA HTML URLs. PDFs and private CRA accounts are unsupported. Official section lookup is current English ITA/ETA, not historical/as-of law. A2AJ date filters are document dates, not effective-date or tax-year filters. Case subsequent treatment is unverified. Paragraph extraction refuses ambiguous numbering rather than inventing precise citations. Source failures, missing results and coverage gaps remain separate statuses.

The next work is deployment and publication, plus any review-driven fixes. Do not start by rewriting the connector or adding a companion skill.
