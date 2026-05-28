# Runbook

## Local Checks

Run the unit tests:

```bash
python3 -m unittest discover -s tests
```

Run the strict batch validator in dry-run mode:

```bash
python3 - <<'PY'
import os
os.environ['DRY_RUN'] = 'true'
from bookleaf_validation.cli import batch_validate
raise SystemExit(batch_validate('validation_book_covers'))
PY
```

Run the one-file smoke test:

```bash
python3 test_cover_flow.py
```

## Environment

Required `.env` keys:

- `GOOGLE_SERVICE_ACCOUNT_JSON`
- `GOOGLE_DRIVE_FOLDER_ID`
- `AIRTABLE_API_KEY`
- `AIRTABLE_BASE_ID`
- `AIRTABLE_TABLE_NAME`
- `SENDGRID_API_KEY`
- `SENDGRID_FROM_EMAIL`
- `SENDGRID_REPLY_TO_EMAIL`
- `OPENAI_API_KEY` optional

## Outputs

Batch validation writes:

- `validation_book_covers/batch_report.json`
- `validation_book_covers/batch_report.csv`
- `validation_book_covers/accuracy_metrics.json`

