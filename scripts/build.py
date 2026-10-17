#!/usr/bin/env python3
"""Deterministic offline build: python3 scripts/build.py. Network jobs are separate."""
import argparse
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch-covers', action='store_true', help='Explicitly opt into the independent network image job')
    parser.add_argument('--dist', action='store_true', help='Also export the public file allowlist to dist/')
    args = parser.parse_args()
    if args.fetch_covers:
        subprocess.run([sys.executable, str(ROOT/'scripts/fetch_covers.py')], cwd=ROOT, check=True)
    for script in ['build_catalog.py','build_essen.py','normalize_catalog.py','split_details.py','build_pages.py','validate_site.py']:
        subprocess.run([sys.executable,str(ROOT/'scripts'/script)],cwd=ROOT,check=True)
    if args.dist:
        subprocess.run([sys.executable,str(ROOT/'scripts/export_dist.py')],cwd=ROOT,check=True)
if __name__ == '__main__': main()
