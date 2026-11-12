"""SQLite persistence with idempotent imports and audit-friendly immutable source fields."""
import os, sqlite3, json, datetime
from contextlib import contextmanager
from catalog import STARTER_SOURCES

DB_PATH = os.getenv('COMPLIANCE_DB_PATH','compliance_v2.sqlite3')

@contextmanager
def connection():
    con=sqlite3.connect(DB_PATH, timeout=25)
    con.row_factory=sqlite3.Row
    try:
        yield con
        con.commit()
    finally:
        con.close()

def init_db():
    with connection() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS sources (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, country TEXT NOT NULL,
          kind TEXT NOT NULL, url TEXT NOT NULL UNIQUE, official_domain TEXT NOT NULL,
          enabled INTEGER NOT NULL DEFAULT 1, checked_at TEXT, last_ok_at TEXT,
          last_error TEXT, last_items INTEGER DEFAULT 0);
        CREATE TABLE IF NOT EXISTS findings (
          id TEXT PRIMARY KEY, source_id INTEGER NOT NULL, title TEXT NOT NULL,
          country TEXT NOT NULL, document_url TEXT NOT NULL, evidence_url TEXT NOT NULL,
          legal_reference TEXT, published_at TEXT, first_seen TEXT NOT NULL,
          last_seen TEXT NOT NULL, text_excerpt TEXT NOT NULL,
          categories TEXT NOT NULL, topics TEXT NOT NULL, summary TEXT NOT NULL,
          business_action TEXT NOT NULL, verification TEXT NOT NULL,
          review_status TEXT NOT NULL DEFAULT 'Needs review',
          notes TEXT NOT NULL DEFAULT '',
          FOREIGN KEY(source_id) REFERENCES sources(id));
        CREATE TABLE IF NOT EXISTS directory_bookmarks (
          id INTEGER PRIMARY KEY, country TEXT NOT NULL, name TEXT NOT NULL,
          url TEXT NOT NULL, added_at TEXT NOT NULL,
          UNIQUE(country,url));
        CREATE TABLE IF NOT EXISTS scan_log (
          id INTEGER PRIMARY KEY, source_id INTEGER NOT NULL,
          scanned_at TEXT NOT NULL, result TEXT NOT NULL, items INTEGER NOT NULL,
          error TEXT NOT NULL DEFAULT '');
        ''')
        for s in STARTER_SOURCES:
            con.execute('INSERT OR IGNORE INTO sources(name,country,kind,url,official_domain) VALUES(?,?,?,?,?)',tuple(s[k] for k in ('name','country','kind','url','official_domain')))

def add_source(name,country,kind,url,official_domain):
    with connection() as con:
        con.execute('INSERT INTO sources(name,country,kind,url,official_domain) VALUES(?,?,?,?,?)',(name,country,kind,url,official_domain))

def sources():
    with connection() as con:
        return [dict(r) for r in con.execute('SELECT * FROM sources ORDER BY country,name')]

def set_source_enabled(source_id, enabled):
    with connection() as con:
        con.execute('UPDATE sources SET enabled=? WHERE id=?',(int(enabled),source_id))

def update_health(source_id, ok, count=0, error=''):
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with connection() as con:
        con.execute('UPDATE sources SET checked_at=?, last_ok_at=CASE WHEN ? THEN ? ELSE last_ok_at END,last_error=?,last_items=? WHERE id=?',(now,int(ok),now,error,count,source_id))
        con.execute('INSERT INTO scan_log(source_id,scanned_at,result,items,error) VALUES(?,?,?,?,?)',(source_id,now,'ok' if ok else 'failed',count,error))

def save_finding(f):
    with connection() as con:
        con.execute('''INSERT INTO findings(id,source_id,title,country,document_url,evidence_url,legal_reference,published_at,first_seen,last_seen,text_excerpt,categories,topics,summary,business_action,verification)
         VALUES(:id,:source_id,:title,:country,:document_url,:evidence_url,:legal_reference,:published_at,:first_seen,:last_seen,:text_excerpt,:categories,:topics,:summary,:business_action,:verification)
         ON CONFLICT(id) DO UPDATE SET last_seen=excluded.last_seen,
           text_excerpt=excluded.text_excerpt, categories=excluded.categories,
           topics=excluded.topics, summary=excluded.summary,
           business_action=excluded.business_action,
           verification=excluded.verification''', f)

def findings():
    with connection() as con:
        rows=[dict(x) for x in con.execute('SELECT f.*,s.name as source_name FROM findings f JOIN sources s ON f.source_id=s.id ORDER BY COALESCE(f.published_at,f.first_seen) DESC')]
    for r in rows:
        r['categories']=json.loads(r['categories']);r['topics']=json.loads(r['topics'])
    return rows

def update_review(fid,status,notes):
    with connection() as con:
        con.execute('UPDATE findings SET review_status=?,notes=? WHERE id=?',(status,notes,fid))

def logs(limit=200):
    with connection() as con:
        return [dict(x) for x in con.execute('SELECT l.*,s.name AS source_name FROM scan_log l JOIN sources s ON s.id=l.source_id ORDER BY l.id DESC LIMIT ?', (limit,))]


def add_bookmark(country,name,url):
    """Save a portal as a research bookmark, never as an active feed."""
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    with connection() as con:
        con.execute('INSERT OR IGNORE INTO directory_bookmarks(country,name,url,added_at) VALUES(?,?,?,?)',
                    (country,name,url,now))


def bookmarks(country=None):
    with connection() as con:
        if country is None:
            rows=con.execute('SELECT * FROM directory_bookmarks ORDER BY country,name')
        else:
            rows=con.execute('SELECT * FROM directory_bookmarks WHERE country=? ORDER BY name',(country,))
        return [dict(r) for r in rows]


def remove_bookmark(bookmark_id):
    with connection() as con:
        con.execute('DELETE FROM directory_bookmarks WHERE id=?',(bookmark_id,))
