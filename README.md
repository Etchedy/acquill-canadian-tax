# Acquill Canadian Tax

A read-only remote MCP server for Canadian tax research. One HTTPS `/mcp` endpoint serves ChatGPT and Claude. No companion skill, model API key, CanLII key, or taxpayer account is required.

This source release is implemented and locally tested. It has **not** been deployed, submitted to either directory, or approved for listing. See `HANDOFF.md` for the remaining release work.

## What is implemented

| Tool | Behaviour |
| --- | --- |
| `search_tax` | Searches selected CRA publications and A2AJ cases/federal laws; returns bounded excerpts, source IDs, dates and citations. |
| `get_document` | Retrieves a selected result with character continuation; judgments support numbered paragraphs plus adjacent context when numbering is available. |
| `get_cra_passages` | Retrieves CRA passage blocks with surrounding context. |
| `get_cra_publication` | Reads a known CRA HTML URL directly, including publications outside the search index. |
| `get_legislation_section` | Reads an official current Income Tax Act or Excise Tax Act section from Justice Canada. |
| `check_coverage` | Reports the actual CRA index and live A2AJ dataset date ranges. |

Default court search covers TCC, FCA, FC and SCC. Specify other dataset codes from `check_coverage` when needed. A2AJ is accessed through its documented REST API; there is no dependency on a second MCP installation.

The server enforces query/window limits, deduplication, source distinctions, supported filters, source failure reporting, restricted outbound hosts, no redirects, capped retrieval sizes, bounded HTTP concurrency, retry/backoff and a bounded in-memory cache. CRA search prioritizes passages containing all terms before broadening; known tax abbreviations expand when needed. `thorough` mode adds expanded A2AJ queries. Embedded MCP instructions guide reading, citations and checking contrary interpretations. Those instructions guide the client model; they cannot force the model to obey or independently prove that all relevant authorities were considered.

## Local setup (Python 3.11+)

```sh
python -m venv .venv
.venv/bin/pip install -e '.[test]'
.venv/bin/canadian-tax-index --max-pages 150
.venv/bin/canadian-tax-mcp
```

On Windows use `.venv\Scripts\python.exe` and the corresponding Scripts executables. The server listens on `http://127.0.0.1:8000/mcp`. `GET /health` reports index state. An empty CRA index is reported explicitly, not silently represented as no relevant guidance.

In a second terminal:

```sh
.venv/bin/pytest -q
.venv/bin/python scripts/smoke.py
```

Alternatively `python scripts/smoke.py --start-server` starts and stops the server itself. Live checks require network access and a populated CRA index. `verification/` contains results from this build; it does not prove deployment or host-client review.

## HTTPS deployment

Requires Docker Compose, a public host, and a domain whose DNS points to that host. Review the public policy pages and upstream data permissions before public release.

1. Copy `.env.example` to `.env` and set the real domain, support email, and certificate email.
2. `docker compose build`
3. `docker compose run --rm app canadian-tax-index --db /app/data/cra.sqlite3 --max-pages 150`
4. `docker compose up -d`
5. Verify `https://YOUR_DOMAIN/health`, `/privacy`, `/terms`, `/support`, and the MCP endpoint `/mcp`.
6. Run `python scripts/smoke.py --url https://YOUR_DOMAIN/mcp` from a machine outside the host.

Caddy provisions TLS. The app is unprivileged and only the reverse proxy exposes public ports. The database persists in `tax-data`. Add platform/WAF per-client rate limits and monitoring before directory launch. No OAuth is needed for this public-data-only implementation; private taxpayer integrations would need a separate authenticated design.

Refresh the index by rerunning step 3. Configure a host scheduler for weekly refreshes if desired; none is activated by this source package. The crawler respects robots.txt, limits pages/depth and spaces requests. It records an ingestion report alongside the database; monitor failures. Existing documents are retained on failed refreshes with their original retrieval dates. They are not silently described as fresh. Removed pages are not automatically deleted from the index.

## Coverage and limitations

- CRA: selected **English HTML** income-tax folios plus GST/HST registrant, business/professional income and rental-income guides. Not all CRA content, rulings, technical interpretations, forms or PDFs. See ingestion seeds and actual coverage. French CRA search explicitly reports outside coverage.
- Legislation search: A2AJ federal legislation/regulations. Official section lookup: current English ITA/ETA only. **No historical/as-of version resolver.** Document date filters are not tax-year filters.
- Courts: A2AJ's actual current dataset coverage, without a hardcoded 2003 cutoff. Results are unofficial copies with source/licence metadata. No citator, certified completeness, or automatic determination that a decision remains good law. A2AJ search exposes no documented pagination; narrow queries/dates instead.
- Query language can be English or French for A2AJ; coverage varies. CRA passages use synthetic block indices, not official paragraph numbers.
- Source text remains untrusted evidence. The server never executes retrieved instructions, but a client model still needs its normal prompt-injection defences.
- Public clients and upstream services receive the search text necessary for their work. Do not send SINs, tax returns, or confidential client facts.

## Publishing

Run `scripts/package_marketplaces.py` with real publisher URLs to generate the ChatGPT upload ZIP and Claude submission worksheet. There is no skills directory. Read `MARKETPLACES.md` before submitting. Public directory acceptance is a separate review process and is not guaranteed.

No public source-code licence has been selected on Acquill's behalf; third-party judgments, legislation and CRA content retain their own terms. The release archive intentionally contains no bulk source-text database. Review `DATA_SOURCES.md` before operating a public or commercial service.
