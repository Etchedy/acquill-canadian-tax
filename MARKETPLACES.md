# ChatGPT and Claude directory release

The product is designed for public directories, using one hosted MCP server. A developer connection used during testing is not the final distribution method. No companion skill is required or included.

Status: no public host, no publisher identity verification, no directory submissions, and no approval claims. The source package is not itself a ready-to-submit hosted service.

## Produce listing materials

After deployment and policy review, run with the actual domain and contact:

```sh
python scripts/package_marketplaces.py \
  --base-url https://YOUR_REAL_DOMAIN \
  --support-email YOUR_MONITORED_EMAIL \
  --demo-url https://YOUR_REAL_VIDEO_URL
```

The script generates a ChatGPT ZIP with `plugin.json`, `mcp.json`, an original icon and five positive/three negative review scenarios. It also generates a Claude submission worksheet and icon. It does not invent publisher accounts, submit forms or claim tests have been completed. The optional demo URL must refer to a recording of the actual deployed service. The starter icon is replaceable if Acquill has existing brand assets.

## ChatGPT

The current OpenAI flow accepts a portable Agent Plugins package with one remote MCP server. Use the generated ZIP; do not upload the entire Python source archive as the directory package. The package intentionally contains no skills.

1. Use the organization/project that should own the service and complete the required publisher verification for Acquill.
2. Upload the ZIP and verify the real endpoint/domain and public metadata pages in the developer dashboard.
3. Run the included scenarios against the hosted service in ChatGPT; record observed behaviour and resolve scan findings. Do not treat Python protocol tests as ChatGPT review completion.
4. Provide the real demonstration video and any requested review information. This is a no-auth public data service, so no private reviewer credentials are necessary unless requirements change.
5. Submit for review and publish only after the platform's approval process. Marketplace acceptance is not guaranteed.

Official guide checked during build: https://developers.openai.com/plugins/deploy/submission

## Claude

1. Open https://claude.ai/directory/manage under the appropriate Acquill publisher account and choose a remote MCP connector submission.
2. Use the deployed HTTPS `/mcp` endpoint, Streamable HTTP, and no authentication for the public-data tools.
3. Supply the generated worksheet's listing text, documentation/privacy URLs, support contact and icon.
4. Claude's published checklist requires testing every tool in Claude via a temporary developer/custom connection before submission. This is a test step; the final goal remains a public directory connector. Do not claim it has happened until it has.
5. Complete the portal review, and monitor feedback and ongoing service availability.

Official guide checked during build: https://claude.com/docs/connectors/building/submission

## Before either submission

Confirm permitted public-service use of each upstream source, final deployment privacy/retention details, a monitored support contact, HTTPS availability, CRA index population, rate limiting, and tested backups/refreshes. These are outstanding release tasks, not completed checks. No user accounts, filing, payments, marketing messages or other writes are implemented by the MCP tools.
