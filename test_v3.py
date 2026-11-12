import sys, json, tempfile, os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from registry_v3 import registry_rows, registry_summary
from catalog import COUNTRIES
from monitor import process_entry

def test_every_country_has_coverage_row():
    assert set(registry_rows()) == set(COUNTRIES)
    assert registry_summary([])[0]['status'].startswith('Not configured')

def test_portal_is_not_feed():
    registry=registry_rows()
    assert any(x['connector']=='portal' for x in registry['Finland'])
    assert not any(x['connector']=='feed' for x in registry['Finland'])

def test_uk_and_germany_feeds():
    assert any(x['connector']=='feed' for x in registry_rows()['Germany'])
    assert any(x['connector']=='feed' for x in registry_rows()['United Kingdom'])

def test_german_off_domain_injection_blocked():
    source=dict(id=2,country='Germany',url='https://www.gesetze-im-internet.de/aktuDienst-rss-feed.xml',official_domain='gesetze-im-internet.de')
    assert process_entry(source,{'title':'Machinery update','link':'https://attacker.example.de/doc'}) is None
