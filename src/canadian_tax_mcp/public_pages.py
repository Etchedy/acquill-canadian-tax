"""Public information pages. Operator must review against the actual hosting configuration."""
import html
import os
from .core import NAME

def render(page):
    contact=html.escape(os.getenv('SUPPORT_EMAIL',''))
    support=f'<a href="mailto:{contact}">{contact}</a>' if contact else 'Support contact not yet configured.'
    draft='' if contact and os.getenv('PUBLIC_URL') else '<p><strong>Development preview. This service is not publicly launched.</strong></p>'
    pages={
      'home':('Canadian tax sources, together', '''<p>Search selected CRA guidance, federal legislation, and Canadian court decisions supplied by A2AJ. Read source passages with citations and coverage information.</p>
      <p>This is a public research connector by Acquill. It is not affiliated with the Canada Revenue Agency, Justice Canada, the courts, OpenAI, Anthropic, or A2AJ.</p>
      <p>The remote MCP endpoint is <code>/mcp</code>. No sign-in or API key is required. Six tools search sources, retrieve documents and CRA passages, read known CRA publication URLs and current statutory sections, and check coverage.</p>
      <p>CRA coverage is selected English HTML publications. Official section retrieval covers current English Income Tax Act and Excise Tax Act text. A2AJ supplies unofficial court and legislative copies; coverage varies. The connector does not resolve historical law, verify subsequent judicial treatment, or guarantee complete research.</p>
      <p>Example: “Find CRA guidance, legislation and tax cases about interest deductibility. Read the relevant passages, cite sources, and identify coverage and tax-year limitations.”</p>'''),
      'privacy':('Privacy', f'''<p>Acquill operates this public-source research connector. Contact: {support}</p>
      <p>The connector receives tool arguments sent by your AI client, including searches, citations, filters and selected passages. It does not require an account and does not access CRA taxpayer accounts, returns or payment information. Do not send social insurance numbers, confidential taxpayer details or other sensitive personal information.</p>
      <p>Search terms and requested citations are sent to A2AJ when using its search and document tools. Requests to CRA and Justice Canada retrieve public materials. Those services and your AI client process data under their own policies.</p>
      <p>The application stores a local index of public CRA content. It does not intentionally persist users' tool arguments or conversations. An in-memory cache holds upstream request parameters and responses; entries stop being reused after their TTL, normally one hour (30 minutes for official statutory sections), and are removed on later eviction or process restart. This is not a promise of immediate deletion at expiry.</p>
      <p>Network and hosting providers can process IP addresses and operational/security metadata. Their retention and geographic processing depend on the deployment. Your ChatGPT or Claude conversation is managed by that provider, independently of this connector. Contact Acquill for the deployed service's hosting and retention details and privacy requests.</p>'''),
      'terms':('Terms of use', f'''<p>Canadian Tax MCP by Acquill provides public-source research tools, not individualized tax, accounting or legal advice. Users remain responsible for checking facts, authoritative texts, applicable dates, amendments and subsequent case treatment.</p>
      <p>Coverage may be incomplete and services may be unavailable. CRA statements are administrative guidance. A2AJ copies are unofficial; original sources and source-specific licence restrictions remain applicable. Access through this service does not grant rights to republish or commercially exploit third-party materials.</p>
      <p>Use the service lawfully. Do not submit confidential taxpayer information, attempt unauthorized access, or overload the service. Acquill may limit access to preserve availability. No guarantee of accuracy, availability, completeness or fitness for a particular purpose is made, to the extent permitted by applicable law.</p>
      <p>Questions: {support}</p>'''),
      'support':('Support', f'<p>Contact Acquill: {support}</p><p>For a problem, include the tool name, approximate time, and public citation or source URL. Omit confidential taxpayer details. Report incorrect extraction, outdated coverage, licensing concerns and security issues through this contact.</p>'),
    }
    title,body=pages[page]
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)} — {NAME}</title>
    <style>body{{font:17px/1.65 system-ui,sans-serif;max-width:780px;margin:4rem auto;padding:0 24px;color:#16352d}}nav a{{margin-right:20px;color:#136650}}h1{{line-height:1.2}}small{{color:#596760}}</style>
    <header><strong>{NAME}</strong><nav><a href="/">About</a><a href="/privacy">Privacy</a><a href="/terms">Terms</a><a href="/support">Support</a></nav></header><main>{draft}<h1>{html.escape(title)}</h1>{body}</main></html>'''
