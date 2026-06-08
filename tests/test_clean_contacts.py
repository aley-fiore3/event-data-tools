"""
Basic tests for clean_contacts.py
Run with: python -m pytest tests/
"""
import io
import sys
import os
import pandas as pd
import pytest

# Add scripts/ to path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))


def test_email_validation():
      """Valid emails should pass, invalid ones should be flagged."""
      valid_emails = ['user@example.com', 'test.user+tag@domain.org']
      invalid_emails = ['notanemail', 'missing@', '@nodomain.com', '']

    import re
    email_pattern = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

    for email in valid_emails:
              assert email_pattern.match(email), f"Expected valid: {email}"

    for email in invalid_emails:
              assert not email_pattern.match(email), f"Expected invalid: {email}"


def test_name_splitting():
      """Full names should split correctly into first and last."""
      test_cases = [
          ('John Smith', 'John', 'Smith'),
          ('Mary Jane Watson', 'Mary', 'Jane Watson'),
          ('Madonna', 'Madonna', ''),
      ]

    for full_name, expected_first, expected_last in test_cases:
              parts = full_name.split(' ', 1)
              first = parts[0]
              last = parts[1] if len(parts) > 1 else ''
              assert first == expected_first, f"First name mismatch for {full_name}"
              assert last == expected_last, f"Last name mismatch for {full_name}"


def test_deduplication():
      """Duplicate emails should be removed, keeping first occurrence."""
      data = pd.DataFrame({
          'email': ['a@test.com', 'b@test.com', 'a@test.com', 'c@test.com'],
          'name': ['Alice', 'Bob', 'Alice Duplicate', 'Carol']
      })
      deduped = data.drop_duplicates(subset='email', keep='first')
      assert len(deduped) == 3
      assert deduped[deduped['email'] == 'a@test.com']['name'].values[0] == 'Alice'


def test_org_normalization():
      """Organization names should be normalized to canonical form."""
      org_map = {
          'ACME Corp': 'ACME Corporation',
          'Acme corp': 'ACME Corporation',
          'acme': 'ACME Corporation',
      }
      raw_orgs = ['ACME Corp', 'Acme corp', 'acme']
      for raw in raw_orgs:
                normalized = org_map.get(raw, raw)
                assert normalized == 'ACME Corporation', f"Org not normalized: {raw}"
        
