import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from catalog import COUNTRIES
from source_directory import directory_for, DIRECTORY, directory_counts

def test_all_countries_represented_without_fabricated_feeds():
    assert set(directory_counts()) == set(COUNTRIES)
    assert all(e['country'] in COUNTRIES for e in DIRECTORY)
    assert all(e['connector'] in {'feed','portal'} for e in DIRECTORY)

def test_only_two_feed_connectors_and_portals_not_feeds():
    feeds=[e for e in DIRECTORY if e['connector']=='feed']
    assert len(feeds)==2
    assert all(e['kind'] in ('rss','atom') for e in feeds)
    assert all(e['kind'] is None for e in DIRECTORY if e['connector']=='portal')

def test_country_directory_and_nordic_portals():
    finland=directory_for('Finland')
    assert any('finlex.fi' in e['url'] for e in finland)
    assert all(e['country']=='Finland' for e in finland)
    assert any('lovdata.no' in e['url'] for e in directory_for('Norway'))

def test_bookmark_persistence_uses_separate_table(tmp_path,monkeypatch):
    import storage
    monkeypatch.setattr(storage,'DB_PATH',str(tmp_path/'test.sqlite3'))
    storage.init_db()
    storage.add_bookmark('Finland','Finlex','https://www.finlex.fi/en')
    storage.add_bookmark('Finland','Finlex','https://www.finlex.fi/en')
    assert len(storage.bookmarks('Finland'))==1
    assert all(s['country']!='Finland' for s in storage.sources())
    storage.remove_bookmark(storage.bookmarks('Finland')[0]['id'])
    assert storage.bookmarks('Finland')==[]
