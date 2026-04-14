#!/usr/bin/env python3
"""
Email List Cleaner
Deduplicates, validates, normalizes, and reformats contact lists.
Built for migrating data between event platforms (Award Force, Cvent, etc.)

Usage:
    python email_list_cleaner.py examples/sample_messy_list.csv --format cvent
    python email_list_cleaner.py input.csv --output cleaned.csv --format cvent --org-map org_map.csv
"""

import pandas as pd
import re
import argparse
import sys


# ---------------------------------------------------------------------------
# Terminal colors (degrades gracefully if not supported)
# ---------------------------------------------------------------------------
class Color:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

    @classmethod
    def disable(cls):
        cls.GREEN = cls.YELLOW = cls.RED = cls.CYAN = cls.BOLD = cls.END = ''


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
# Core functions
# ---------------------------------------------------------------------------

def load_data(filepath):
    """Load CSV with flexible encoding handling."""
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            return pd.read_csv(filepath, encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Could not read {filepath} with any standard encoding")


def normalize_email(email):
    """Clean and normalize email addresses."""
    if pd.isna(email):
        return None
    email = str(email).strip().lower()
    email = re.sub(r'^mailto:', '', email)
    return email if '@' in email and len(email.split('@')[1]) > 1 else None


def validate_email(email):
    """
    Validate an email address. Returns 'valid' or a pipe-separated list of issues.
    """
    if email is None or (isinstance(email, float)) or not str(email).strip():
        return 'missing'

    email = str(email)
    issues = []

    if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
        issues.append('invalid_format')

    typo_domains = {
        '.cmo': '.com', '.con': '.com', '.coom': '.com',
        '.og': '.org', '.rog': '.org',
        '.edi': '.edu', '.eud': '.edu',
        'gmial.com': 'gmail.com', 'gmal.com': 'gmail.com',
        'yahooo.com': 'yahoo.com', 'yaho.com': 'yahoo.com',
        'outlok.com': 'outlook.com',
    }
    for typo, correction in typo_domains.items():
        if email.endswith(typo) or typo in email:
            issues.append(f'possible_typo:{typo}->{correction}')

    disposable = [
        'tempmail.com', 'throwaway.email', 'guerrillamail.com',
        'mailinator.com', 'yopmail.com', 'sharklasers.com',
    ]
    domain = email.split('@')[-1] if '@' in email else ''
    if domain in disposable:
        issues.append('disposable')

    return '|'.join(issues) if issues else 'valid'


def split_name(full_name):
    """
    Split a full name into (first, last), stripping prefixes and suffixes.

    >>> split_name('Dr. Maria Santos')
    ('Maria', 'Santos')
    >>> split_name('Ben Taylor III')
    ('Ben', 'Taylor')
    >>> split_name(None)
    (None, None)
    """
    if pd.isna(full_name) or not str(full_name).strip():
        return None, None

    name = str(full_name).strip()

    prefixes = ['Dr.', 'Dr', 'Prof.', 'Prof', 'Mr.', 'Mr', 'Mrs.', 'Mrs', 'Ms.', 'Ms']
    for prefix in sorted(prefixes, key=len, reverse=True):
        if name.startswith(prefix + ' '):
            name = name[len(prefix):].strip()
            break

    suffixes = ['Ph.D.', 'PhD', 'M.D.', 'MD', 'Jr.', 'Jr', 'Sr.', 'Sr', 'III', 'II', 'IV']
    for suffix in sorted(suffixes, key=len, reverse=True):
        if name.endswith(' ' + suffix):
            name = name[:-(len(suffix) + 1)].strip()
            break

    parts = name.split(' ', 1)
    first = parts[0].title() if parts[0] else None
    last = parts[1].title() if len(parts) > 1 else None

    return first, last


def normalize_organization(org, org_map=None):
    """
    Standardize an organization name using an optional mapping dict.

    >>> normalize_organization('TAMU')
    'Texas A&M University'
    >>> normalize_organization('CU Boulder')
    'University of Colorado Boulder'
    """
    if pd.isna(org) or not str(org).strip():
        return None

    org = str(org).strip()

    default_map = {
        'tamu': 'Texas A&M University',
        'texas a & m': 'Texas A&M University',
        'texas a&m': 'Texas A&M University',
        'texas a&m university': 'Texas A&M University',
        'cu boulder': 'University of Colorado Boulder',
        'uc boulder': 'University of Colorado Boulder',
        'csu': 'Colorado State University',
        'colo state': 'Colorado State University',
        'notre dame': 'University of Notre Dame',
        'nd': 'University of Notre Dame',
        'udel': 'University of Delaware',
        'u of delaware': 'University of Delaware',
        'univ of delaware': 'University of Delaware',
    }

    if org_map:
        default_map.update({k.lower(): v for k, v in org_map.items()})

    key = org.lower()
    if key in default_map:
        return default_map[key]

    return org


def deduplicate(df, email_col='email_clean'):
    """
    Deduplicate on *email_col*, keeping the record with the fewest NaN values
    (i.e. the most complete row). Returns (unique_df, duplicate_df).
    """
    if email_col not in df.columns:
        return df, pd.DataFrame()

    working = df.copy()
    working['_completeness'] = working.notna().sum(axis=1)
    working = working.sort_values('_completeness', ascending=False)

    unique = working.drop_duplicates(subset=email_col, keep='first').copy()
    all_dupes = working[working.duplicated(subset=email_col, keep='first')].copy()

    unique.drop(columns=['_completeness'], inplace=True)
    all_dupes.drop(columns=['_completeness'], inplace=True)

    return unique, all_dupes


PLATFORM_MAPS = {
    'cvent': {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'email_clean': 'Email Address',
        'organization': 'Company',
    },
    'constant_contact': {
        'email_clean': 'Email',
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'organization': 'Company Name',
    },
    'mailchimp': {
        'email_clean': 'Email Address',
        'first_name': 'First Name',
        'last_name': 'Last Name',
    },
}


def format_for_platform(df, platform):
    """Rename columns to match a destination platform's import template."""
    column_map = PLATFORM_MAPS.get(platform, {})
    return df.rename(columns={k: v for k, v in column_map.items() if k in df.columns})


# ---------------------------------------------------------------------------
# Auto-detect helpers
# ---------------------------------------------------------------------------

def _find_column(df, candidates):
    """Return the first column whose lowered name is in *candidates*, or None."""
    for col in df.columns:
        if col.lower() in candidates:
            return col
    return None


def find_email_column(df):
    for col in df.columns:
        if 'email' in col.lower():
            return col
    return None


def find_name_column(df):
    return _find_column(df, ['name', 'full name', 'full_name', 'contact name'])


def find_org_column(df):
    return _find_column(df, ['organization', 'org', 'company', 'institution', 'school'])


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def clean_list(input_file, output_file=None, platform=None, org_map_file=None):
    """Run the full cleaning pipeline and save results."""
    print(f"\n{Color.BOLD}Email List Cleaner{Color.END}")
    print(f"{'─' * 40}")

    # Load
    info(f"Loading {input_file}")
    df = load_data(input_file)
    original_count = len(df)
    success(f"{original_count} records loaded")

    # Detect columns
    email_col = find_email_column(df)
    name_col = find_name_column(df)
    org_col = find_org_column(df)

    if not email_col:
        error("No email column found — expected a column with 'email' in the name.")
        raise SystemExit(1)

    info(f"Email column: '{email_col}'"
         + (f"  |  Name column: '{name_col}'" if name_col else '')
         + (f"  |  Org column: '{org_col}'" if org_col else ''))

    # Clean emails
    print(f"\n{Color.BOLD}Cleaning emails{Color.END}")
    df['email_clean'] = df[email_col].apply(normalize_email)
    df['email_status'] = df['email_clean'].apply(validate_email)

    valid_mask = df['email_status'] == 'valid'
    missing_mask = df['email_status'] == 'missing'
    flagged_mask = ~valid_mask & ~missing_mask

    success(f"{valid_mask.sum()} valid")
    if missing_mask.any():
        warn(f"{missing_mask.sum()} missing / empty")
    if flagged_mask.any():
        warn(f"{flagged_mask.sum()} flagged (typos, disposable, invalid format)")

    # Split names
    if name_col:
        print(f"\n{Color.BOLD}Splitting names{Color.END}")
        df[['first_name', 'last_name']] = df[name_col].apply(
            lambda x: pd.Series(split_name(x))
        )
        success("Names split into first_name / last_name")

    # Normalize orgs
    if org_col:
        print(f"\n{Color.BOLD}Normalizing organizations{Color.END}")
        org_map = None
        if org_map_file:
            org_map = (pd.read_csv(org_map_file, header=None, names=['variant', 'standard'])
                       .set_index('variant')['standard'].to_dict())
            info(f"Loaded {len(org_map)} custom mappings from {org_map_file}")

        before_unique = df[org_col].nunique()
        df['organization'] = df[org_col].apply(lambda x: normalize_organization(x, org_map))
        after_unique = df['organization'].nunique()
        success(f"{before_unique} unique orgs → {after_unique} after normalization")

    # Deduplicate
    print(f"\n{Color.BOLD}Deduplicating{Color.END}")
    clean_df, dupes = deduplicate(df)
    if len(dupes):
        warn(f"{len(dupes)} duplicate rows removed (kept most complete record)")
    success(f"{len(clean_df)} unique records remain")

    # Format for platform
    if platform:
        print(f"\n{Color.BOLD}Formatting for {platform}{Color.END}")
        clean_df = format_for_platform(clean_df, platform)
        success(f"Columns renamed for {platform} import")

    # Save
    print(f"\n{Color.BOLD}Saving{Color.END}")
    output_file = output_file or input_file.replace('.csv', '_cleaned.csv')
    clean_df.to_csv(output_file, index=False)
    success(f"Clean list → {output_file}")

    review_df = pd.concat([
        df[~valid_mask],
        dupes,
    ]).drop_duplicates()

    if len(review_df) > 0:
        review_file = input_file.replace('.csv', '_needs_review.csv')
        review_df.to_csv(review_file, index=False)
        warn(f"{len(review_df)} records need human review → {review_file}")

    # Summary
    print(f"\n{Color.BOLD}{'─' * 40}")
    print(f"  Summary{Color.END}")
    print(f"  Input:    {original_count} records")
    print(f"  Output:   {Color.GREEN}{len(clean_df)} clean{Color.END}")
    removed = original_count - len(clean_df)
    if removed:
        print(f"  Removed:  {Color.YELLOW}{removed} duplicates{Color.END}")
    flagged_total = len(review_df) if len(review_df) > 0 else 0
    if flagged_total:
        print(f"  Flagged:  {Color.YELLOW}{flagged_total} for review{Color.END}")
    print()

    return clean_df


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Clean and deduplicate contact lists for platform migration',
        epilog='Example: python email_list_cleaner.py examples/sample_messy_list.csv --format cvent',
    )
    parser.add_argument('input', help='Input CSV file')
    parser.add_argument('--output', '-o', help='Output CSV file (default: input_cleaned.csv)')
    parser.add_argument('--format', '-f', choices=['cvent', 'constant_contact', 'mailchimp'],
                        help='Format output for specific platform')
    parser.add_argument('--org-map', help='CSV mapping org name variants → standard names')

    args = parser.parse_args()
    clean_list(args.input, args.output, args.format, args.org_map)
