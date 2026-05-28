import os

os.environ["DRY_RUN"] = "true"

from bookleaf_validation.cli import batch_validate

raise SystemExit(batch_validate("validation_book_covers"))

