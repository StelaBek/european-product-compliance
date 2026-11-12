import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from monitor import host_allowed,is_document_url,extract_reference,classify,process_entry,parse_feed,item_date

def test_host_validation():
    assert host_allowed('https://eur-lex.europa.eu/eli/reg/2023/988/oj','eur-lex.europa.eu')
    assert not host_allowed('https://eur-lex.europa.eu.evil.com/act','eur-lex.europa.eu')
    assert not host_allowed('http://eur-lex.europa.eu/act','eur-lex.europa.eu')

def test_no_homepage_as_document():
    feed='https://www.legislation.gov.uk/new/data.feed'
    assert not is_document_url('https://www.legislation.gov.uk/',feed)
    assert not is_document_url(feed,feed)
    assert is_document_url('https://www.legislation.gov.uk/uksi/2026/123/contents',feed)

def test_references():
    assert extract_reference('Law 3 — Waste/EPR') is None
    assert extract_reference('Act 5 — Packaging') is None
    assert extract_reference('Regulation (EU) 2025/40 on packaging') == 'Regulation (EU) 2025/40'

def test_unrelated_regulation_not_reach():
    cats,_=classify('Regulation (EU) 1286/2014 on packaged retail investment products','Financial disclosure to investors')
    assert 'Chemicals & materials' not in cats

def test_chemical_classification():
    cats,_=classify('Amendment to REACH restriction of phthalates','')
    assert 'Chemicals & materials' in cats

def test_offsite_feed_item_rejected(monkeypatch):
    src=dict(id=1,url='https://eur-lex.europa.eu/EN/display-feed.rss?rssId=165',official_domain='eur-lex.europa.eu',country='European Union')
    assert process_entry(src,{'title':'REACH updated','link':'https://unrelated.example.com/document'}) is None


def test_rss_exact_item_link_and_date():
    feed=b"<rss version='2.0'><channel><item><title>New toy safety rules</title><link>https://www.legislation.gov.uk/uksi/2026/99/contents</link><description>Safety measures for toys</description><pubDate>Thu, 12 Nov 2026 10:00:00 GMT</pubDate></item></channel></rss>"
    entry=parse_feed(feed)[0]
    assert entry['link'].endswith('/uksi/2026/99/contents')
    assert item_date(entry)=='2026-11-12'

def test_atom_exact_item_link():
    xml=b"<feed xmlns='http://www.w3.org/2005/Atom'><entry><title>Packaging obligation</title><link rel='alternate' href='https://eur-lex.europa.eu/eli/reg/2025/40/oj'/><updated>2026-11-12T00:00:00Z</updated></entry></feed>"
    entry=parse_feed(xml)[0]
    assert entry['link']=='https://eur-lex.europa.eu/eli/reg/2025/40/oj'
