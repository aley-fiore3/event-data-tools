# Event Data Tools

> Python scripts for cleaning, migrating, and reconciling event data across platforms.
> Built for Cvent, Award Force, Asana, and spreadsheet-heavy workflows.

[![Tests](https://github.com/aley-fiore3/event-data-tools/actions/workflows/tests.yml/badge.svg)](https://github.com/aley-fiore3/event-data-tools/actions/workflows/tests.yml)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/aley-fiore3/event-data-tools/blob/main/demo_clean_contacts.ipynb)

---

## The Problem

Event teams manually export data from one platform, paste it into Excel, clean it, and re-import it into another. This takes hours per cycle, introduces errors, and is basically impossible to audit.

This toolset was built to replace that workflow. It handles deduplication, cross-platform reconciliation, and badge generation — automatically, repeatably, and with a clear output report.

---

## What's In Here

| Script | What It Does | Time Saved |
|---|---|---|
| [`clean_contacts.py`](scripts/clean_contacts.py) | Deduplicate, validate emails, split names, normalize org names | 2-3 hours per data migration |
| [`reconcile_platforms.py`](scripts/reconcile_platforms.py) | Find mismatches between two platform exports (e.g. Cvent vs Award Force) | 3-5 hours per event cycle |
| [`generate_badges.py`](scripts/generate_badges.py) | Build badge-print-ready data from registration exports | 1-2 hours per event |

---

## Quick Start

```bash
pip install -r requirements.txt
```

**Clean a contact list:**
```bash
python scripts/clean_contacts.py data/raw_export.csv --output data/cleaned.csv --format cvent
```

**Reconcile Award Force + Cvent:**
```bash
python scripts/reconcile_platforms.py \
    --source1 data/award_force_export.csv \
    --source2 data/cvent_export.csv \
    --match-on email \
    --output data/reconciliation_report.csv
```

**Generate badge data:**
```bash
python scripts/generate_badges.py data/registration.csv --template templates/badge_template.csv
```

---

## Folder Structure

```
event-data-tools/
├── scripts/          # Core Python scripts
├── data/             # Sample input/output files
│   ├── raw/          # Example raw exports
│   └── cleaned/      # Expected clean outputs
├── templates/        # Platform import templates
│   ├── badge_template.csv
│   ├── cvent_import_template.csv
│   └── org_name_map.csv
├── tests/            # pytest test suite
│   └── test_clean_contacts.py
└── examples/         # Sample walkthroughs
```

---

## Templates

| Template | Purpose |
|---|---|
| `badge_template.csv` | Column structure for badge printing vendors |
| `cvent_import_template.csv` | Cvent's expected import format |
| `org_name_map.csv` | Organization name standardization mappings |

---

## How It Was Deployed

This toolset was built while managing a real event migration: 250+ contacts across Award Force and Cvent with zero data loss tolerance.

The workflow:
1. Client exports CSV from platform A
2. `clean_contacts.py` runs deduplication and validation
3. `reconcile_platforms.py` surfaces mismatches before import
4. Clean file imports into platform B
5. Report generated for audit trail

---

## Requirements

- Python 3.8+
- pandas
- pytest (for tests)

```bash
pip install -r requirements.txt
```

---

## Tests

```bash
pytest tests/
```

The test suite covers email validation, name splitting, deduplication logic, and org name normalization.

---

---

## Related Work

- **[claude-prompt-library](https://github.com/aley-fiore3/claude-prompt-library)** — Prompt library documenting how these scripts are paired with Claude in real engagements
- **[fiore3-automation-demos](https://github.com/aley-fiore3/fiore3-automation-demos)** — Automation demos and case studies showing this toolset deployed in real workflows
- **[event-reconciliation-dashboard](https://github.com/aley-fiore3/event-reconciliation-dashboard)** — No-code Streamlit UI built on top of this same cleaning and reconciliation logic

---

## License

MIT — use it, adapt it, ship it.

Built by [Alessandra Desiderio](https://alessandradesiderio.com)
