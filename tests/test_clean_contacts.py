"""
Tests for event data cleaning logic.
Run with: pytest tests/ -v
"""
import re
import pytest


# ── Helpers (inline implementations for testability) ─────────────────────────

EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

def is_valid_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email.strip()))


def split_name(full_name: str) -> tuple:
    parts = full_name.strip().split()
    if len(parts) == 0:
        return ('', '')
    elif len(parts) == 1:
        return (parts[0], '')
    else:
        return (parts[0], ' '.join(parts[1:]))


def deduplicate(records: list, key: str) -> list:
    seen = set()
    result = []
    for r in records:
        val = r.get(key, '').lower().strip()
        if val not in seen:
            seen.add(val)
            result.append(r)
    return result


def normalize_org(name: str, org_map: dict) -> str:
    return org_map.get(name.strip().lower(), name.strip())


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_email_validation_valid():
    valid = ['user@example.com', 'test.user+tag@domain.org', 'a@b.io']
    for email in valid:
        assert is_valid_email(email), f"Expected valid: {email}"


def test_email_validation_invalid():
    invalid = ['notanemail', 'missing@', '@nodomain.com', '', '   ']
    for email in invalid:
        assert not is_valid_email(email), f"Expected invalid: {email}"


def test_name_splitting_full():
    first, last = split_name('John Smith')
    assert first == 'John'
    assert last == 'Smith'


def test_name_splitting_three_parts():
    first, last = split_name('Mary Jane Watson')
    assert first == 'Mary'
    assert last == 'Jane Watson'


def test_name_splitting_single():
    first, last = split_name('Madonna')
    assert first == 'Madonna'
    assert last == ''


def test_deduplication_removes_duplicates():
    records = [
        {'email': 'a@example.com', 'name': 'Alice'},
        {'email': 'b@example.com', 'name': 'Bob'},
        {'email': 'A@EXAMPLE.COM', 'name': 'Alice Duplicate'},
    ]
    result = deduplicate(records, 'email')
    assert len(result) == 2
    assert result[0]['name'] == 'Alice'


def test_deduplication_preserves_order():
    records = [
        {'email': 'z@example.com'},
        {'email': 'a@example.com'},
        {'email': 'z@example.com'},
    ]
    result = deduplicate(records, 'email')
    assert result[0]['email'] == 'z@example.com'
    assert result[1]['email'] == 'a@example.com'


def test_org_normalization():
    org_map = {
        'acme corp': 'ACME Corporation',
        'ibm': 'IBM',
    }
    assert normalize_org('acme corp', org_map) == 'ACME Corporation'
    assert normalize_org('IBM', org_map) == 'IBM'
    assert normalize_org('Unknown Co', org_map) == 'Unknown Co'


def test_org_normalization_strips_whitespace():
    org_map = {'ibm': 'IBM'}
    assert normalize_org('  ibm  ', org_map) == 'IBM'
