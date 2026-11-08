# Verification record

Build date: 2026-10-26. These records concern local implementation checks, not marketplace approval.

| Check | Result |
| --- | --- |
| Automated unit and MCP contract checks | 33 passed; see `pytest.txt` |
| Real Streamable HTTP MCP handshake and tool calls | Passed; all six tools exercised; see `live-smoke.json` |
| Live source search | CRA, A2AJ cases and A2AJ federal laws each returned results |
| Live source retrieval | CRA passages and original URL, A2AJ judgment and legislation, and official Justice ITA section 20 succeeded |
| Live judgment paragraph retrieval | Paragraphs 1–2 plus available adjacent context succeeded for 2013 FCA 122 |
| CRA ingestion | 149 distinct public HTML pages indexed locally; metadata in `cra-index-manifest.json` |
| ChatGPT package schemas | Portable plugin and MCP configuration validated against published Agent Plugins 1.0.0 schemas |
| Package generator | Successfully produced a ZIP and Claude worksheet using clearly separate test-fixture URLs; fixture output is not included in this release |
| Python packaging | Wheel built successfully with the declared build backend |
| Compose configuration | YAML parsed; Docker runtime unavailable, so image/Compose execution is unverified |
| ChatGPT and Claude conversations | Not tested in either host client |
| Public deployment and directories | Not deployed, submitted, approved or published |

The first crawler run found a stale T4002 seed (404) and a timed-out chapter-history page. The seed was corrected, the current T4002 guide chapters were ingested, and the timed-out page was successfully retried. Initial and corrective reports are retained to distinguish what happened. The supplemental guide crawl reached its own page cap; its queued links largely overlap the initial folio crawl. None of this establishes coverage of the whole CRA website.

The local CRA database is not distributed. The included metadata manifest identifies the pages used in verification. Populate the deployment's index using the provided crawler. Upstream availability and content can change; run live checks again on the hosted service.

Schema validation does not validate all platform-specific metadata or guarantee directory acceptance. Public policies remain deployment-specific drafts. Qodo tools/CLI were not available in this environment; no independent Qodo review is claimed.

`environment.txt` records installed versions from the verification environment. It is evidence, not a cross-platform dependency lock. Install from `pyproject.toml` and rerun the tests on the target host.
