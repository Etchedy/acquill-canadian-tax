from starlette.testclient import TestClient
from canadian_tax_mcp.server import mcp

def client():
    return TestClient(mcp.streamable_http_app(), base_url='http://localhost:8000')

def test_public_pages_including_docs_with_example_prompts():
    c = client()
    for path in ('/', '/docs', '/privacy', '/terms', '/support'):
        assert c.get(path).status_code == 200, path
    docs = c.get('/docs').text
    assert docs.count('<li>') >= 9  # six tools and at least three example prompts
    assert 'Acquill Canadian Tax' in docs and 'MCP by' not in docs

def test_openai_domain_challenge_is_plain_text_when_configured(monkeypatch):
    c = client()
    assert c.get('/.well-known/openai-apps-challenge').status_code == 404
    monkeypatch.setenv('OPENAI_APPS_CHALLENGE', 'token-123')
    r = c.get('/.well-known/openai-apps-challenge')
    assert r.status_code == 200 and r.text == 'token-123' and r.headers['content-type'].startswith('text/plain')

def test_ai_client_origins_are_not_rejected():
    body = {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 't', 'version': '1'}}}
    headers = {'accept': 'application/json, text/event-stream', 'content-type': 'application/json'}
    # The session manager runs once per process: every request goes through one client session.
    with TestClient(mcp.streamable_http_app(), base_url='http://localhost:8000') as c:
        for origin in ('https://claude.ai', 'https://chatgpt.com'):
            assert c.post('/mcp', json=body, headers={**headers, 'origin': origin}).status_code == 200, origin
        assert c.post('/mcp', json=body, headers={**headers, 'origin': 'https://evil.example'}).status_code == 403
