"""Scheduled ingestion; persists public candidate snapshots for Streamlit deployment."""
import os
from storage import init_db, import_snapshot, export_snapshot
from monitor import scan_all

if __name__ == '__main__':
    init_db()
    import_snapshot()
    for name, count, error in scan_all(limit=int(os.getenv('SCAN_ITEM_LIMIT','60'))):
        print(f'{name}: {count} matching records; {error or "fetch succeeded"}')
    print('Snapshot findings:',export_snapshot())
