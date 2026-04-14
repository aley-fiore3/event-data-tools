# Event Data Tools

Python scripts for cleaning, migrating, and reconciling event data across platforms. Built for people who run events on Cvent, Award Force, Asana, and spreadsheets and are tired of manual data wrangling.

## Scripts

| Script | What It Does |
|--------|-------------|
| [clean_contacts.py](scripts/clean_contacts.py) | Deduplicate, validate emails, split names, normalize orgs |
| [reconcile_platforms.py](scripts/reconcile_platforms.py) | Compare exports from two platforms and find mismatches |
| [generate_badges.py](scripts/generate_badges.py) | Generate name badge data from registration exports |

## Quick Start

```bash
pip install pandas
```

### Clean a contact list
```bash
python scripts/clean_contacts.py data/raw_export.csv --output data/cleaned.csv --format cvent
```

### Reconcile Award Force + Cvent
```bash
python scripts/reconcile_platforms.py \
    --source1 data/award_force_export.csv \
    --source2 data/cvent_export.csv \
    --match-on email \
    --output data/reconciliation_report.csv
```

### Generate badge data
```bash
python scripts/generate_badges.py data/registration.csv --template templates/badge_template.csv
```

## Examples

The `examples/` folder contains sample input/output files so you can test the scripts before running on real data.

## Templates

| Template | Use |
|----------|-----|
| [badge_template.csv](templates/badge_template.csv) | Column structure for badge printing vendors |
| [cvent_import_template.csv](templates/cvent_import_template.csv) | Cvent's expected import format |
| [org_name_map.csv](templates/org_name_map.csv) | Organization name standardization mappings |

## Requirements

- Python 3.8+
- pandas

## License

MIT
