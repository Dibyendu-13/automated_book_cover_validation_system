from pathlib import Path
from bookleaf_validation.settings import get_settings
from bookleaf_validation.workflow import CoverWorkflow
from bookleaf_validation.validators import CoverPayload

settings = get_settings()
workflow = CoverWorkflow(settings, from_email=settings.sendgrid_from_email)

path = sorted(Path("validation_book_covers").glob("*.png"))[0]
payload = CoverPayload(
    file_path=str(path),
    book_id=path.stem,
    author_name="Unknown Author",
    elements=[],
)

try:
    outcome = workflow.process(payload, author_email="dibyendu9974@gmail.com")
    print(outcome.result)
    print(outcome.airtable_fields)
    print(outcome.email_body)
except Exception as e:
    print("Run failed:", e)