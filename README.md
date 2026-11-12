# European Product Compliance Monitor v2

An independent **Streamlit** starter application for monitoring official European legislation feeds and reviewing possible product-compliance developments.

## What's included

- Clean dashboard, candidate findings cards, country/category/search filters, CSV export.
- Exact legal-document links from RSS/Atom items (no homepage substitution).
- Separate **retrieval** and **human verification** statuses; no ungrounded legal conclusions.
- A manual review queue that requires rationale before confirming relevance.
- Source-health reporting and 47+ country/jurisdiction coverage register (not a claim of active monitoring).
- Broad e-commerce taxonomy: furniture, toys, chemicals, general safety, machinery, electrical, packaging, textiles and more.
- Two starter official feeds: EUR-Lex Official Journal L and UK legislation new acts.
- Unit tests for the wrong-regulation / generic-reference / off-domain URL cases.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit, then click **Scan configured feeds**. Internet access is required. A source may block requests or provide only abstracts; the app will expose scan errors instead of inventing findings. The app does not require API keys.

For command-line scanning:

```bash
python scan.py
pytest -q
```

## Deploy on Streamlit Community Cloud

1. Create a **new GitHub repository**, upload all files (including `catalog.py`, `monitor.py`, `storage.py`, `app.py`, `requirements.txt`).
2. In Streamlit Community Cloud select that repository and `app.py` as the entry point.
3. Start the app and scan. **Important:** SQLite on ephemeral cloud storage may reset after deployment/restarts. Use persistent PostgreSQL or external managed storage before production use; do not commit the live SQLite file to a public repository.
4. Set a private deployment or add authentication before uploading confidential product data. The starter does not implement user accounts.

## Limitations — read before using operationally

**This is a functioning prototype, not a complete European regulatory-monitoring service.** It registers jurisdictions but initially scans **only two** official feeds. To cover countries comprehensively, add and maintain country-specific official connectors, official gazette feeds, regulators, product recall services and notification systems. Feed-only monitoring can miss amendments, guidance and entries not published through those feeds. No application can guarantee detection of all European regulatory developments.

- A successfully retrieved page is **not** equivalent to proof that a legal requirement changed. A reviewer must read and assess the actual legal text and implementation rules.
- Summaries quote or describe **only the source title and feed excerpt**. The app deliberately does not hallucinate specific obligations, deadlines or affected SKUs. For high-quality actionable summaries, add an evidence-grounded structured extraction pipeline and reviewer approval.
- Product categories and topics are **heuristic suggestions**, not legal applicability decisions. Search for and classify all categories relevant to each item.
- Direct links point to the feed's individual item; some publishers link to summary pages rather than article-level sections. An exact article/PDF-page deep link requires a publisher-specific connector.
- The app does not use arbitrary web search as evidence of a legislative amendment. Feed retrieval failures are logged.
- The default database is SQLite and the UI has no login. This is suited to a single-user local prototype.
- Source URLs must be HTTPS and stay on their registered domain. Add sources only from official regulators; for hosted multiuser versions, enforce server-side network allowlists to prevent SSRF.

## Project files

- `app.py`: UI and review workflow
- `monitor.py`: feed retrieval, document-level links, conservative product-category matches
- `catalog.py`: geographic register, taxonomy, official starter feeds
- `storage.py`: SQLite persistence
- `scan.py`: optional headless scan
- `tests/test_monitor.py`: source and classification tests

## Future production roadmap

Add feed-source-specific document ID validation and legislative version comparison, national-language translation grounded to source spans, reviewer authentication, PostgreSQL persistence, background scheduling, full official-source coverage, change-event detection and measurement of false positives/false negatives against manually curated legislation.
