#!/usr/bin/env python3
"""
Platform Reconciler
Compare exports from two event platforms and find mismatches.

Usage:
    python reconcile_platforms.py \\
        --source1 examples/sample_award_force.csv --name1 "Award Force" \\
        --source2 examples/sample_cvent.csv --name2 "Cvent" \\
        --output examples/reconciliation.csv
"""

import pandas as pd
import argparse
import sys
from datetime import datetime


# ---------------------------------------------------------------------------
# Terminal colors
# ---------------------------------------------------------------------------
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        for attr in ['GREEN', 'YELLOW', 'RED', 'CYAN', 'BOLD', 'DIM', 'END']:
            setattr(cls, attr, '')


if not sys.stdout.isatty():
    Color.disable()


def info(msg):
    print(f"  {Color.CYAN}→{Color.END} {msg}")

def success(msg):
    print(f"  {Color.GREEN}✓{Color.END} {msg}")

def warn(msg):
    print(f"  {Color.YELLOW}⚠{Color.END} {msg}")

def error(msg):
    print(f"  {Color.RED}✗{Color.END} {msg}")


# ---------------------------------------------------------------------------
# Column detection
# ---------------------------------------------------------------------------

def find_email_column(df):
    """Auto-detect the email column."""
    for col in df.columns:
        if 'email' in col.lower():
            return col
    return None


def find_name_columns(df):
    """Auto-detect name column(s). Returns (full_name_col, first_col, last_col)."""
    full = None
    first = None
    last = None
    for col in df.columns:
        low = col.lower().replace('_', ' ')
        if low in ['name', 'full name', 'contact name']:
            full = col
        elif low in ['first name', 'first']:
            first = col
        elif low in ['last name', 'last']:
            last = col
    return full, first, last


def normalize(series):
    """Normalize a string series for matching."""
    return series.astype(str).str.strip().str.lower()


# ---------------------------------------------------------------------------
# Core reconciliation
# ---------------------------------------------------------------------------

def reconcile(source1_path, source2_path, match_on='email',
              source1_name='Source 1', source2_name='Source 2'):
    """
    Compare two platform exports and generate a reconciliation report.

    Returns a dict of DataFrames keyed by mismatch category.
    """
    print(f"\n{Color.BOLD}Platform Reconciler{Color.END}")
    print(f"{'─' * 50}")

    # Load
    df1 = pd.read_csv(source1_path)
    df2 = pd.read_csv(source2_path)

    info(f"{source1_name}: {len(df1)} records  ←  {source1_path}")
    info(f"{source2_name}: {len(df2)} records  ←  {source2_path}")

    # Find match columns
    if match_on == 'email':
        col1 = find_email_column(df1)
        col2 = find_email_column(df2)
        if not col1:
            error(f"No email column found in {source1_name}")
            raise SystemExit(1)
        if not col2:
            error(f"No email column found in {source2_name}")
            raise SystemExit(1)
        info(f"Matching on: '{col1}' ↔ '{col2}'")
    else:
        col1 = col2 = match_on
        info(f"Matching on column: '{match_on}'")

    # Normalize match keys
    df1['_match_key'] = normalize(df1[col1])
    df2['_match_key'] = normalize(df2[col2])

    # Remove empty keys
    empty1 = df1['_match_key'].isin(['', 'nan', 'none']) | df1['_match_key'].isna()
    empty2 = df2['_match_key'].isin(['', 'nan', 'none']) | df2['_match_key'].isna()
    if empty1.any():
        warn(f"{empty1.sum()} records in {source1_name} have no match key — skipped")
    if empty2.any():
        warn(f"{empty2.sum()} records in {source2_name} have no match key — skipped")

    df1 = df1[~empty1].copy()
    df2 = df2[~empty2].copy()

    # Match
    print(f"\n{Color.BOLD}Matching{Color.END}")
    keys1 = set(df1['_match_key'])
    keys2 = set(df2['_match_key'])

    matched_keys = keys1 & keys2
    only_in_1 = keys1 - keys2
    only_in_2 = keys2 - keys1

    in_both_df1 = df1[df1['_match_key'].isin(matched_keys)].copy()
    in_1_not_2 = df1[df1['_match_key'].isin(only_in_1)].copy()
    in_2_not_1 = df2[df2['_match_key'].isin(only_in_2)].copy()

    success(f"{len(matched_keys)} matched across both platforms")

    if len(only_in_1):
        warn(f"{len(only_in_1)} in {source1_name} only:")
        for _, row in in_1_not_2.iterrows():
            print(f"    {Color.DIM}{row['_match_key']}{Color.END}")

    if len(only_in_2):
        warn(f"{len(only_in_2)} in {source2_name} only:")
        for _, row in in_2_not_1.iterrows():
            print(f"    {Color.DIM}{row['_match_key']}{Color.END}")

    # Check for duplicates within each source
    print(f"\n{Color.BOLD}Duplicate check{Color.END}")
    dupes_1 = df1[df1.duplicated(subset='_match_key', keep=False)]
    dupes_2 = df2[df2.duplicated(subset='_match_key', keep=False)]

    if len(dupes_1):
        warn(f"{len(dupes_1)} duplicate entries in {source1_name}")
    else:
        success(f"No duplicates in {source1_name}")

    if len(dupes_2):
        warn(f"{len(dupes_2)} duplicate entries in {source2_name}")
    else:
        success(f"No duplicates in {source2_name}")

    # Summary
    print(f"\n{Color.BOLD}{'─' * 50}")
    print(f"  Summary{Color.END}")
    print(f"  {Color.GREEN}Matched:         {len(matched_keys)}{Color.END}")
    if only_in_1:
        print(f"  {Color.YELLOW}In {source1_name} only: {len(only_in_1)}{Color.END}")
    if only_in_2:
        print(f"  {Color.YELLOW}In {source2_name} only: {len(only_in_2)}{Color.END}")
    if len(dupes_1) or len(dupes_2):
        print(f"  {Color.YELLOW}Duplicates:      {len(dupes_1)} + {len(dupes_2)}{Color.END}")
    print()

    return {
        'matched': in_both_df1,
        f'only_in_{source1_name}': in_1_not_2,
        f'only_in_{source2_name}': in_2_not_1,
        f'duplicates_{source1_name}': dupes_1,
        f'duplicates_{source2_name}': dupes_2,
    }


def save_report(results, output_path):
    """Save reconciliation results to CSV files."""
    print(f"{Color.BOLD}Saving reports{Color.END}")
    base = output_path.replace('.csv', '')

    for name, df in results.items():
        if len(df) > 0:
            clean = df.drop(columns=['_match_key'], errors='ignore')
            filepath = f"{base}_{name}.csv"
            clean.to_csv(filepath, index=False)
            success(f"{filepath} ({len(df)} records)")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Reconcile two platform exports and find mismatches',
        epilog=('Example: python reconcile_platforms.py '
                '--source1 examples/sample_award_force.csv --name1 "Award Force" '
                '--source2 examples/sample_cvent.csv --name2 "Cvent"'),
    )
    parser.add_argument('--source1', required=True, help='First CSV export')
    parser.add_argument('--source2', required=True, help='Second CSV export')
    parser.add_argument('--match-on', default='email',
                        help='Column to match on (default: email)')
    parser.add_argument('--name1', default='Source1',
                        help='Label for first source (e.g. "Award Force")')
    parser.add_argument('--name2', default='Source2',
                        help='Label for second source (e.g. "Cvent")')
    parser.add_argument('--output', '-o', default='reconciliation.csv',
                        help='Output file base name')

    args = parser.parse_args()

    results = reconcile(
        args.source1, args.source2,
        match_on=args.match_on,
        source1_name=args.name1,
        source2_name=args.name2,
    )
    save_report(results, args.output)
