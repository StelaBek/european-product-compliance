"""European Product Compliance Monitor v2 — independent Streamlit application."""
import io
import json
from urllib.parse import urlparse

import pandas as pd
import streamlit as st

from catalog import CATEGORIES, COUNTRIES, EU, OTHER_EEA, OTHER_EUROPE
from storage import init_db, findings, sources, logs, add_source, update_review, set_source_enabled
from monitor import scan_all, host_allowed

st.set_page_config(page_title='Product Compliance Monitor',page_icon='🛡️',layout='wide',initial_sidebar_state='expanded')
init_db()

st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1440px}
[data-testid="stSidebar"]{border-right:1px solid rgba(128,128,128,.18)}
h1,h2,h3{letter-spacing:-.035em}
.small-muted{color:#7b8795;font-size:.87rem}
.hero{padding:1.45rem 1.65rem;border:1px solid rgba(124,139,153,.20);border-radius:18px;
background:linear-gradient(125deg,rgba(90,112,225,.12),rgba(63,185,164,.08))}
.finding-header{font-size:1.08rem;font-weight:650;margin:.3rem 0}
.kicker{text-transform:uppercase;letter-spacing:.11em;font-size:.72rem;color:#768394;font-weight:700}
[data-testid="stMetric"]{border:1px solid rgba(120,135,150,.2);border-radius:14px;padding:14px 16px}
div[data-testid="stExpander"]{border-radius:13px;border:1px solid rgba(125,140,150,.20)}
</style>''',unsafe_allow_html=True)

PAGES=['Overview','Findings','Review queue','Source coverage','Settings & sources']
with st.sidebar:
    st.markdown('### 🛡️ Compliance Monitor')
    st.caption('European product regulation intelligence')
    page=st.radio('Navigation',PAGES,label_visibility='collapsed')
    st.divider()
    st.markdown('**Evidence policy**')
    st.caption('A retrieved official document is a candidate, not a legally verified change. Human review is required before compliance decisions.')
    if st.button('🔄 Scan configured feeds',use_container_width=True):
        with st.spinner('Retrieving configured official feeds…'):
            results=scan_all()
        if not results:st.warning('No feeds enabled.')
        else:
            for name,count,error in results:
                if error:st.error(f'{name}: {error}')
                else:st.success(f'{name}: {count} relevant candidates')

all_rows=findings()
configured=sources()
confirmed=[r for r in all_rows if r['review_status']=='Confirmed relevant']
unreviewed=[r for r in all_rows if r['review_status']=='Needs review']

if page=='Overview':
    st.markdown('''<div class="hero"><div class="kicker">Regulatory intelligence</div>
    <h1 style="margin:.2rem 0 .35rem">European Product Compliance</h1>
    <div>Monitor official legislation feeds, review evidence, and prioritise relevant changes for e-commerce products.</div></div>''',unsafe_allow_html=True)
    st.write('')
    a,b,c,d=st.columns(4)
    a.metric('Candidates found',len(all_rows))
    b.metric('Confirmed by reviewer',len(confirmed))
    c.metric('Awaiting review',len(unreviewed))
    d.metric('Healthy configured feeds',sum(bool(x['last_ok_at']) and not x['last_error'] for x in configured))
    if not all_rows:
        st.info('No findings yet. Click **Scan configured feeds** in the sidebar. Scans require internet access and may be rate-limited by official websites.')
    st.subheader('Recent reviewed findings')
    if confirmed:
        for r in confirmed[:8]:
            st.markdown(f'**{r["title"]}**  ·  {r["country"]}  ·  {r["published_at"] or "Date unconfirmed"}')
            st.write(r['summary'])
            st.link_button('Official document',r['document_url'])
            st.divider()
    else:st.caption('No confirmed findings. Review candidates before displaying regulatory alerts as confirmed.')
    st.subheader('What is covered?')
    st.markdown('The jurisdiction register contains **EU-level legislation plus European countries**. Only sources with working configured official feeds are actively monitored; other countries remain coverage gaps until connected.')
    st.caption('Monitoring a feed is not the same as comprehensive legal coverage. Results may omit relevant regulations, guidance or national amendments.')

elif page=='Findings':
    st.title('Regulatory findings')
    st.caption('Original official titles and exact item links. Categories are suggestions until a reviewer confirms applicability.')
    f1,f2,f3=st.columns(3)
    with f1: selected_countries=st.multiselect('Jurisdiction',sorted({r['country'] for r in all_rows}))
    with f2: selected_categories=st.multiselect('Product category',list(CATEGORIES))
    with f3: selected_status=st.selectbox('Review status',['All','Needs review','Confirmed relevant','Not relevant','Rejected'])
    query=st.text_input('Search legal titles, excerpts and references',placeholder='e.g., toy safety, packaging, EN 1021')
    def matches(r):
        return (not selected_countries or r['country'] in selected_countries) and (not selected_categories or bool(set(r['categories'])&set(selected_categories))) and (selected_status=='All' or r['review_status']==selected_status) and (not query or query.lower() in ' '.join([r['title'],r['summary'],r['legal_reference'] or '',r['text_excerpt']]).lower())
    displayed=[r for r in all_rows if matches(r)]
    st.caption(f'{len(displayed)} matching findings')
    for r in displayed:
        with st.container(border=True):
            st.caption(f'{r["country"]}  ·  {r["published_at"] or "Publication date unknown"}  ·  {r["source_name"]}')
            st.markdown(f'#### {r["title"]}')
            st.write(r['summary'])
            st.caption('Suggested product areas: '+(', '.join(r['categories']) or 'Not classified'))
            st.caption('Status: '+r['review_status']+'  |  Retrieval: '+r['verification'])
            c1,c2=st.columns([1,2])
            with c1:st.link_button('↗ Open exact official document',r['document_url'])
            with c2:st.write('**Legal identifier:** '+(r['legal_reference'] or 'Not independently established'))
            with st.expander('Evidence, follow-up and reviewer notes'):
                st.write('**Source excerpt:** '+r['text_excerpt'])
                st.write('**Recommended follow-up:** '+r['business_action'])
                if r['notes']:st.write('**Reviewer notes:** '+r['notes'])
    if displayed:
        csv_rows=[dict(title=r['title'],country=r['country'],published=r['published_at'],categories=', '.join(r['categories']),reference=r['legal_reference'],status=r['review_status'],document_url=r['document_url'],summary=r['summary'],notes=r['notes']) for r in displayed]
        st.download_button('Download filtered CSV',pd.DataFrame(csv_rows).to_csv(index=False).encode('utf-8-sig'),'compliance_findings.csv','text/csv')

elif page=='Review queue':
    st.title('Verification & applicability review')
    st.info('Reviewing a record verifies relevance based on your own assessment; document retrieval alone does **not** verify the legal effect of an amendment.')
    if not unreviewed:st.success('No findings awaiting review.')
    for r in unreviewed:
        with st.expander(f'{r["country"]} · {r["title"]}'):
            st.write(r['summary'])
            st.link_button('Open official document',r['document_url'])
            st.caption('Extracted reference: '+(r['legal_reference'] or 'Not identified'))
            st.caption('Source excerpt: '+r['text_excerpt'])
            with st.form('review_'+r['id']):
                decision=st.selectbox('Decision',['Needs review','Confirmed relevant','Not relevant','Rejected'],key='decision_'+r['id'])
                notes=st.text_area('Evidence and rationale (required for confirmation)',value=r['notes'],key='note_'+r['id'])
                if st.form_submit_button('Save review'):
                    if decision=='Confirmed relevant' and len(notes.strip())<20:
                        st.error('Include at least 20 characters explaining the confirmed legal change and applicability.')
                    else:
                        update_review(r['id'],decision,notes)
                        st.rerun()

elif page=='Source coverage':
    st.title('European jurisdiction coverage')
    st.caption('An enabled source is only a configured feed. Check last scan and successful response before interpreting coverage.')
    summary=[]
    for country in COUNTRIES:
        ss=[s for s in configured if s['country']==country]
        enabled=[s for s in ss if s['enabled']]
        ok=[s for s in enabled if s['last_ok_at'] and not s['last_error']]
        status='Not configured' if not enabled else ('Last scan successful (partial coverage)' if ok else 'Configured — not successfully scanned')
        summary.append(dict(Jurisdiction=country,Source_feeds=len(enabled),Last_success=max([s['last_ok_at'] for s in ok],default=''),Status=status))
    st.dataframe(pd.DataFrame(summary),hide_index=True,use_container_width=True)
    st.download_button('Export coverage CSV',pd.DataFrame(summary).to_csv(index=False).encode(),'source_coverage.csv','text/csv')
    st.subheader('Recent scan diagnostics')
    scanlogs=logs()
    if scanlogs:st.dataframe(pd.DataFrame(scanlogs),use_container_width=True,hide_index=True)
    else:st.caption('No feed scans recorded.')

elif page=='Settings & sources':
    st.title('Settings & official sources')
    st.warning('Only add officially controlled RSS/Atom feeds. Website homepages are not feed endpoints. Do not add private/internal URLs.')
    for src in configured:
        with st.container(border=True):
            left,right=st.columns([4,1])
            left.markdown(f'**{src["name"]}** · {src["country"]}')
            left.caption(src['url'])
            left.caption('Last checked: '+(src['checked_at'] or 'Never')+' · '+('Error: '+src['last_error'] if src['last_error'] else 'No recorded error'))
            enabled=right.checkbox('Enabled',value=bool(src['enabled']),key=f'enabled_{src["id"]}')
            if enabled!=bool(src['enabled']):set_source_enabled(src['id'],enabled);st.rerun()
    st.divider()
    st.subheader('Register a new official feed')
    with st.form('add_feed'):
        name=st.text_input('Name',placeholder='National official gazette — new acts')
        country=st.selectbox('Jurisdiction',COUNTRIES)
        kind=st.selectbox('Format',['rss','atom'])
        url=st.text_input('Exact RSS/Atom HTTPS URL')
        domain=st.text_input('Official domain',placeholder='example.gov.country')
        if st.form_submit_button('Add feed'):
            if not name or not host_allowed(url,domain):st.error('Enter a name and a valid HTTPS feed URL on the declared official domain.')
            else:
                try:add_source(name,country,kind,url,domain);st.success('Feed added. Run a scan to test it.');st.rerun()
                except Exception as e:st.error(f'Unable to save (duplicate feed URL?): {type(e).__name__}')
    st.caption('The taxonomy includes '+str(len(CATEGORIES))+' categories: '+', '.join(CATEGORIES)+'. Relevance matches are heuristics, not verified legal opinions.')
