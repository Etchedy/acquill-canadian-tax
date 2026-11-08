# Source contracts and attribution

| Source | Interface | Use |
| --- | --- | --- |
| CRA | Canada.ca public HTML; crawler seeds in `ingest.py` | Local full-text index of selected English guidance |
| Justice Canada | `https://laws-lois.justice.gc.ca/eng/acts/I-3.3/section-20.html` and analogous sections | Official current ITA/ETA section lookup |
| A2AJ | `https://api.a2aj.ca/openapi.json` | `/search`, `/fetch`, `/coverage` for cases and federal laws |

The A2AJ API supplies the case data directly; this connector does not scrape CanLII or require a CanLII API key. The A2AJ API is used as a data dependency rather than nesting another MCP server. Its documented search API has no offset; this server does not invent one.

A2AJ coverage is obtained dynamically, including each dataset's dates, rather than assuming 2003 is an end date. English and French availability differ. API schema and dataset codes may change; live integration checks must run before releases.

The connector preserves `upstream_license` metadata when supplied, plus original-source URLs, citation, retrieval date and unofficial-copy labels. An absent licence value is not permission. A2AJ's open-source software licence does not automatically license every underlying judgment for every use. Some upstream source terms may restrict commercial reuse. Acquill must confirm the intended public service and redistribution comply with source terms before launch, and obtain permission where required.

The same distinction applies to Crown-copyright CRA and Justice material. Verify applicable reproduction terms, attribution and currency requirements. The source archive contains no bulk court or CRA text dataset; the operator builds the CRA index directly from the allowed original pages.

The crawler follows robots.txt and limits its scope, but robots permission alone is not a copyright licence. Refreshes retain previously indexed documents if a source fails or disappears; check the report and remove stale entries as part of maintenance. `/health` reports retrieval-date ranges; it does not claim completeness.

Reference links for the next operator:

- A2AJ project: https://github.com/ai2aj
- A2AJ live API specification: https://api.a2aj.ca/openapi.json
- CRA folio index: https://www.canada.ca/en/revenue-agency/services/tax/technical-information/income-tax/income-tax-folios-index.html
- Government website terms: https://www.canada.ca/en/transparency/terms.html
- Justice site: https://laws-lois.justice.gc.ca/

This file describes implementation dependencies and outstanding publication checks, not a legal opinion on reuse rights.
