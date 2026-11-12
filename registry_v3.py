"""Country-level source registry. 'candidate' sources are never active by default.

Exact endpoints below have been identified in public publisher documentation,
but scan health must be observed in the deployed environment. A source is not
proof of comprehensive jurisdictional coverage.
"""
from catalog import COUNTRIES
from source_directory import DIRECT_PORTALS

OFFICIAL_FEEDS = [
 dict(country='European Union',name='EUR-Lex — Official Journal L',url='https://eur-lex.europa.eu/EN/display-feed.rss?rssId=165',official_domain='eur-lex.europa.eu',kind='rss',scope='EU legal acts',documentation='https://eur-lex.europa.eu/homepage.html'),
 dict(country='United Kingdom',name='UK legislation — latest',url='https://www.legislation.gov.uk/new/data.feed',official_domain='legislation.gov.uk',kind='atom',scope='UK statutory legislation',documentation='https://www.legislation.gov.uk/'),
 dict(country='Germany',name='Gesetze im Internet — Aktualitätendienst',url='https://www.gesetze-im-internet.de/aktuDienst-rss-feed.xml',official_domain='gesetze-im-internet.de',kind='rss',scope='Federal law publication updates',documentation='https://www.gesetze-im-internet.de/aktuDienst.html'),
 # The Lovdata feed is for news, NOT a statutory gazette; keep it optional.
 dict(country='Norway',name='Lovdata — news articles (supplemental)',url='https://lovdata.no/feed?data=newArticles&type=RSS',official_domain='lovdata.no',kind='rss',scope='Supplemental news, not complete legislation',documentation='https://lovdata.no/'),
]

def registry_rows():
    by_country={c:[] for c in COUNTRIES}
    for feed in OFFICIAL_FEEDS:
        by_country[feed['country']].append({**feed,'connector':'feed','status':'available_to_configure'})
    for country, portals in DIRECT_PORTALS.items():
        for name,url,domain in portals:
            by_country[country].append(dict(country=country,name=name,url=url,official_domain=domain,connector='portal',status='research_only',scope='Portal; not an automated connector'))
    return by_country


def registry_summary(configured):
    result=[]
    for country, links in registry_rows().items():
        enabled=[s for s in configured if s['country']==country and s['enabled']]
        ok=[s for s in enabled if s.get('last_ok_at') and not s.get('last_error')]
        status=('Last scan successful — partial source coverage' if ok else
                'Configured — scan unverified/failed' if enabled else
                'Not configured — source directory only')
        result.append(dict(country=country,status=status,connected=len(enabled),healthy=len(ok),
                           suggested_feeds=sum(x['connector']=='feed' for x in links),
                           official_portals=sum(x['connector']=='portal' for x in links),
                           last_success=max([s['last_ok_at'] for s in ok],default='')))
    return result
