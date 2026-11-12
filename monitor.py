"""Primary-source feed ingestion. Discovery ≠ verified legal obligation."""
import datetime as dt
import hashlib
import ipaddress
import json
import re
import socket
from urllib.parse import urlparse, urldefrag

import email.utils
import xml.etree.ElementTree as ET
import requests
from bs4 import BeautifulSoup

from catalog import CATEGORIES, TOPICS
from storage import sources, update_health, save_finding

HEADERS={'User-Agent':'ProductComplianceMonitor/2.0 (+internal compliance review)'}
HTTP_TIMEOUT=16

def host_allowed(url, official_domain):
    """Reject unrelated landing pages and unsafe URLs; allow subdomains of a source domain."""
    try:
        p=urlparse(url)
        host=(p.hostname or '').lower().rstrip('.')
        base=official_domain.lower().strip().rstrip('.')
        if p.scheme!='https' or p.username or p.password or not host or not base:
            return False
        if host!=base and not host.endswith('.'+base):
            return False
        if host in ('localhost','localhost.localdomain') or host.endswith(('.local','.internal','.test')):
            return False
        # Only intended public official domains; reject direct IP literals.
        try: ipaddress.ip_address(host); return False
        except ValueError: pass
        return True
    except (ValueError,TypeError):
        return False

def is_document_url(url, feed_url):
    """Reject the source feed itself and top-level homepages."""
    doc=urlparse(url)
    feed=urlparse(feed_url)
    return bool(doc.path.strip('/') and url.rstrip('/')!=feed_url.rstrip('/') and doc.path not in ('/','/en','/EN','/home','/index.html'))

def clean_html(html):
    soup=BeautifulSoup(html or '', 'html.parser')
    for tag in soup(['script','style','noscript','nav','footer','header']):tag.decompose()
    return re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).strip()

def classify(title, evidence):
    # Title drives detection. Evidence expands matching if it strongly mentions topics.
    title=title.lower(); evidence=evidence.lower()
    matches=[]
    for category, terms in CATEGORIES.items():
        if not terms: continue
        if any(re.search(r'(?<!\w)'+re.escape(term)+r'(?!\w)',title) for term in terms):
            matches.append(category)
        elif sum(term in evidence for term in terms)>=2:
            matches.append(category)
    topics=[topic for topic, terms in TOPICS.items() if any(term in title or term in evidence for term in terms)]
    return matches,topics

def extract_reference(title):
    # Only specific patterns; never "Act 5" / "Law 3".
    matches=[
      r'\bCELEX[:\s]*[0-9]{5}[A-Z][0-9]{4}(?:\([0-9]+\))?\b',
      r'\b(?:Regulation|Directive|Decision)\s*\((?:EU|EC|EEC)\)\s*\d{4}/\d{1,5}\b',
      r'\b(?:S\.?I\.?|S\.?R\.?)\s*(?:No\.?\s*)?\d{1,5}/\d{4}\b',
      r'\b\d{4}\s+c\.?\s*\d+\b'
    ]
    for pattern in matches:
        found=re.search(pattern,title,flags=re.I)
        if found:return found.group(0)
    return None

def retrieved_document(url,domain):
    """Fetch the exact item and verify redirect remains on allowed domain."""
    if not host_allowed(url,domain):return '',False,'Off-domain or non-HTTPS link'
    try:
        # Requests may follow redirects; inspect every redirect target before relying on it.
        r=requests.get(url,timeout=HTTP_TIMEOUT,headers=HEADERS,allow_redirects=False)
        redirects=0
        while 300<=r.status_code<400 and redirects<4:
            target=requests.compat.urljoin(r.url,r.headers.get('Location',''))
            if not host_allowed(target,domain):return '',False,'Redirect off official domain'
            r=requests.get(target,timeout=HTTP_TIMEOUT,headers=HEADERS,allow_redirects=False)
            redirects+=1
        if r.status_code>=400:return '',False,'HTTP '+str(r.status_code)
        ctype=r.headers.get('Content-Type','').lower()
        if 'pdf' in ctype or urlparse(r.url).path.lower().endswith('.pdf'):
            return '',False,'PDF document: text extraction not configured; manual review required'
        if not any(x in ctype for x in ('html','xml','text')):
            return '',False,'Unsupported content type'
        text=clean_html(r.text)
        return text[:16000],bool(len(text)>=150),'' if len(text)>=150 else 'Insufficient retrieved document text'
    except requests.RequestException as exc:
        return '',False,exc.__class__.__name__

def parse_feed(text):
    """Parse standard RSS 2.0 / Atom 1.0 feeds without a search engine."""
    try: root=ET.fromstring(text)
    except ET.ParseError as exc: raise ValueError('Not valid feed XML') from exc
    items=[]
    if root.tag.lower().endswith('rss') or root.find('channel') is not None:
        for node in root.findall('.//channel/item'):
            get=lambda name: (node.findtext(name) or '').strip()
            items.append(dict(title=get('title'),link=get('link'),summary=get('description'),published_at=get('pubDate')))
    else:
        ns='{http://www.w3.org/2005/Atom}'
        for node in root.findall('.//'+ns+'entry'):
            def get(name):return (node.findtext(ns+name) or '').strip()
            links=node.findall(ns+'link')
            chosen=next((n for n in links if n.attrib.get('rel','alternate')=='alternate' and n.attrib.get('href')),None)
            items.append(dict(title=get('title'),link=chosen.attrib.get('href','') if chosen is not None else '',summary=get('summary') or get('content'),published_at=get('published') or get('updated')))
    if not items: raise ValueError('No RSS or Atom entries')
    return items

def item_date(entry):
    value=entry.get('published_at','')
    if not value:return None
    try:return dt.datetime.fromisoformat(value.replace('Z','+00:00')).date().isoformat()
    except ValueError:
        try:return email.utils.parsedate_to_datetime(value).date().isoformat()
        except (ValueError,TypeError,IndexError):return None

def process_entry(source,entry):
    title=clean_html(entry.get('title',''))[:500]
    doc_url=urldefrag(entry.get('link',''))[0]
    if not title or not is_document_url(doc_url,source['url']):
        return None
    # A specific cross-domain German federal gazette is an explicitly permitted
    # document publisher, not arbitrary third-party links or portal homepages.
    doc_domain=source['official_domain']
    if source['country']=='Germany' and host_allowed(doc_url,'recht.bund.de'):
        doc_domain='recht.bund.de'
    if not host_allowed(doc_url,doc_domain):
        return None
    feed_excerpt=clean_html(entry.get('summary',''))[:3000]
    doc_text,verified,reason=retrieved_document(doc_url,doc_domain)
    # Use feed title as original title. Feed excerpt is evidence, not proof of legal effect.
    categories,topics=classify(title,feed_excerpt + ' '+doc_text[:4000])
    if not categories:return None
    # Extract a very short source-backed excerpt, never invent a "new requirement".
    excerpt=(feed_excerpt or doc_text[:550]).strip()[:850]
    if not excerpt:excerpt='The official feed supplied a title but no explanatory text.'
    status='Document retrieved — human review required' if verified else 'Retrieval incomplete — human review required'
    summary=(f'Official source entry: {title}. '+
             (f'Source excerpt: {excerpt[:360]}' if feed_excerpt else 'The feed does not explain the legal change.'))
    action='Open the exact source document; confirm what changed, which products and economic operators are affected, and the effective date before taking compliance action.'
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    # Content address by jurisdiction+source item link. Same law across distinct feeds can be reconciled later.
    fid=hashlib.sha256((source['country']+'|'+doc_url).encode()).hexdigest()[:24]
    return dict(id=fid,source_id=source['id'],title=title,country=source['country'],
        document_url=doc_url,evidence_url=doc_url,legal_reference=extract_reference(title),
        published_at=item_date(entry),first_seen=now,last_seen=now,
        text_excerpt=excerpt,categories=json.dumps(categories),topics=json.dumps(topics),
        summary=summary,business_action=action,verification=status)

def scan_source(source,limit=60):
    if not host_allowed(source['url'],source['official_domain']):
        update_health(source['id'],False,0,'Source URL is not a valid HTTPS link on the registered domain')
        return 0,'Source URL/domain mismatch'
    try:
        r=requests.get(source['url'],headers=HEADERS,timeout=HTTP_TIMEOUT)
        if not host_allowed(r.url,source['official_domain']) or any(not host_allowed(h.url,source['official_domain']) for h in r.history):
            raise ValueError('Source feed redirected off registered domain')
        r.raise_for_status()
        count=0
        for entry in parse_feed(r.content)[:limit]:
            f=process_entry(source,entry)
            if f:
                save_finding(f); count+=1
        update_health(source['id'],True,count)
        return count,None
    except (requests.RequestException,ValueError) as exc:
        msg=str(exc)[:200]
        update_health(source['id'],False,0,msg)
        return 0,msg

def scan_all(limit=60):
    result=[]
    for s in sources():
        if not s['enabled']:continue
        count,error=scan_source(s,limit)
        result.append((s['name'],count,error))
    return result
