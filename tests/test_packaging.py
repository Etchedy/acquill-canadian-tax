import importlib.util
from pathlib import Path
import pytest

spec=importlib.util.spec_from_file_location('package_marketplaces',Path(__file__).parents[1]/'scripts/package_marketplaces.py')
packaging=importlib.util.module_from_spec(spec);spec.loader.exec_module(packaging)

def test_manifest_has_no_skill_and_complete_review_cases():
    manifest,mcp,claude=packaging.build('https://tax.publisher.dev','support@publisher.dev')
    assert 'skills' not in manifest and 'onboardingSkill' not in manifest['extensions']['com.openai']
    interface=manifest['extensions']['com.openai']['interface']
    assert len(interface['displayName'])<=30 and len(interface['shortDescription'])<=30
    assert all(len(x)<=128 for x in interface['defaultPrompt'])
    assert list(mcp['mcpServers'])==['canadian-tax']
    cases=manifest['extensions']['com.openai']['review']['test_cases']
    assert len(cases['positive'])==5 and len(cases['negative'])==3
    assert not claude['tested_in_claude']

@pytest.mark.parametrize('url',['http://tax.publisher.dev','https://user:secret@tax.publisher.dev','https://example.com','https://localhost','https://tax.invalid'])
def test_manifest_refuses_placeholder_or_unsafe_url(url):
    with pytest.raises(ValueError):packaging.build(url,'support@publisher.dev')
