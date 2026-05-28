from __future__ import annotations

from dataclasses import dataclass

from .integrations import AirtableClient, DriveClient, EmailClient
from .helpers import extract_book_id
from .settings import Settings
from .validators import CoverPayload, CoverValidator
from .vision import OpenAIVisionClient, VisionAnalysis


@dataclass
class WorkflowOutcome:
    result: dict
    airtable_fields: dict
    email_body: str


class CoverWorkflow:
    def __init__(self, settings: Settings, from_email: str = "bookleaf@example.com"):
        self.settings = settings
        self.validator = CoverValidator()
        self.airtable = AirtableClient(settings)
        self.drive = DriveClient(settings)
        self.email = EmailClient(settings, from_email=from_email)
        self.vision = OpenAIVisionClient(settings.openai_api_key) if settings.openai_api_key else None

    def process(self, payload: CoverPayload, author_email: str) -> WorkflowOutcome:
        vision: VisionAnalysis | None = None
        if self.vision and payload.file_path.lower().endswith(".png"):
            if not self.settings.dry_run:
                try:
                    vision = self.vision.analyze(payload.file_path)
                except Exception as exc:
                    print(f"Vision fallback: {exc}")
        result = self.validator.validate(payload, vision=vision)
        airtable_record = self.airtable.create_or_update(result, email=author_email)
        email_body = self.email.send(author_email, payload.author_name or "Author", result)
        return WorkflowOutcome(
            result=result.to_dict(),
            airtable_fields=airtable_record.fields,
            email_body=email_body,
        )

    @staticmethod
    def book_id_from_filename(filename: str) -> str:
        return extract_book_id(filename)
