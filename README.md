# European Product Compliance Monitor v3

An open-source **prototype**, not an authoritative legal alert service. Product relevance is a keyword-based *suggestion*. The system does not prove a legal change, application date or a country's comprehensive legal coverage. Never make testing, blocking or launch decisions from a candidate record without reviewing the underlying legal instrument.

## What's new from v2.1

- Jurisdiction-by-jurisdiction source registry for **all countries in `catalog.COUNTRIES`**. Entries distinguish **actual feed endpoints** from **reference-only legislative portals**.
- Three initially configured official feeds: **EUR-Lex, UK legislation, Germany**. A supplemental Norway Lovdata news feed is available as an optional connector; it is **not** a statutory law feed.
- A source listing only becomes **last scan successful (partial coverage)** after a successful retrieval, not because it is included in the directory.
- Daily GitHub Actions scan with a committed public `data/snapshot.json` for use by Streamlit Community Cloud. You can also run manually using Actions > Scan official source feeds > Run workflow.
- Persistent public *candidate findings* via GitHub snapshots. A review decision recorded in Streamlit's local SQLite database is **not persistent across restarts**. Do **not** add confidential notes to `data/snapshot.json`.
- Exact document links (where supplied by publisher), conservative excerpt-backed summaries, a human verification queue, and product taxonomy.

## How to deploy

1. Create a new GitHub repository (or upload and overwrite your existing app's files) with all project files **at the repository root**. Ensure the hidden `.github/workflows/scan.yml` file is uploaded; the web uploader may hide folders beginning with a dot. If needed create it in GitHub using Add file > Create new file and path `.github/workflows/scan.yml`.
2. In GitHub, open **Settings > Actions > General > Workflow permissions** and choose **Read and write permissions** to permit committing the public snapshot. Your organisation may restrict this option.
3. Open **Actions > Scan official source feeds > Run workflow**. Check logs for source errors. This workflow is also scheduled once daily; scheduled GitHub Actions can run late or be disabled in inactive repositories.
4. Connect the repository to Streamlit Community Cloud at https://share.streamlit.io and set main file to `app.py`. No API key is required.
5. In **Country source directory**, enable suggested feeds where available. Only repository-configured seeds participate in automated daily GitHub Actions scans unless you also edit `catalog.STARTER_SOURCES`. **Adding a feed in the Streamlit UI is local and will not configure it for GitHub Actions**.
6. Check **Source coverage** after a completed scan. Inspect source errors and open exact source documents. Do not interpret `healthy` as exhaustive coverage.

## Local development

```bash
pip install -r requirements.txt
streamlit run app.py
# in another terminal:
python scan.py
pytest -q
```

## Critical limitations

- The current automated connectors cover only EU-wide, UK and German legal publication feeds. A country directory entry does **not** mean the country is monitored.
- RSS/Atom feeds are not exhaustive even for the three configured jurisdictions. Country-specific product regulator sources and primary-document APIs are still needed.
- We have not performed live integration testing from the deployment environment. Source endpoint availability must be checked in GitHub Actions logs.
- HTML/PDF full legal-text parsing, advanced deduplication, amendment comparison, native-language classification, and machine-verifiable applicability dates remain future work.
- SQLite reviews, manually added feeds, and bookmarks in the Streamlit UI are temporary on Community Cloud. Use a hosted database (e.g. managed Postgres) for durable reviewer data before production.
- Github snapshot JSON is committed to the repository; therefore **never put confidential commercial data or notes in it**.
- An RSS item can link to a landing page, even if it is a deep URL. The app does not treat that as verified amendment evidence.

## Initial country feed references

- EU: `https://eur-lex.europa.eu/EN/display-feed.rss?rssId=165`
- UK: `https://www.legislation.gov.uk/new/data.feed`
- Germany: `https://www.gesetze-im-internet.de/aktuDienst-rss-feed.xml` — [publisher documentation](https://www.gesetze-im-internet.de/aktuDienst.html).
- Norway (optional *supplemental news*): `https://lovdata.no/feed?data=newArticles&type=RSS` (not a legal gazette feed).

Always test feed URL availability in the deployment environment before relying on the resulting status.
