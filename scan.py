"""CLI entry point for scheduled scans: python scan.py"""
from storage import init_db
from monitor import scan_all
if __name__=='__main__':
    init_db()
    for name,count,error in scan_all():
        print(f'{name}: {count} candidate records; {error or "OK"}')
