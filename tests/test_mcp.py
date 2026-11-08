import json
from canadian_tax_mcp.server import mcp

async def test_tool_contract():
    tools=await mcp.list_tools()
    assert {t.name for t in tools}=={'search_tax','get_document','get_cra_passages','get_legislation_section','check_coverage','get_cra_publication'}
    for t in tools:
        assert t.title and t.annotations.readOnlyHint and not t.annotations.destructiveHint
        assert t.meta['securitySchemes']==[{'type':'noauth'}]
    assert not await mcp.list_prompts()

async def test_mcp_tool_execution():
    content=await mcp.call_tool('search_tax',{'query':'capital cost allowance','source':'cra'})
    structured=json.loads(content[0].text)
    assert structured['query']=='capital cost allowance'
