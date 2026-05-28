from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from email.message import EmailMessage
from urllib.parse import quote
from urllib import error, request

from .models import ValidationResult
from .settings import Settings


@dataclass
class AirtableRecord:
    fields: dict


class AirtableClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def create_or_update(self, result: ValidationResult, email: str | None = None) -> AirtableRecord:
        confidence_percent = round(result.confidence_score)
        fields = {
            "ISBN": result.book_id,
            "Status": result.status.value,
            "Issues": "\n".join(f"{i.issue_type} ({i.severity.value}): {i.message}" for i in result.issues) or "None",
            "Confidence": confidence_percent,
            "Email": email or "",
        }
        table = quote(self.settings.airtable_table_name, safe="")
        url = f"https://api.airtable.com/v0/{self.settings.airtable_base_id}/{table}"
        payload = json.dumps({"fields": fields}).encode("utf-8")
        if not self.settings.dry_run:
            req = request.Request(url, data=payload, method="POST")
            req.add_header("Authorization", f"Bearer {self.settings.airtable_api_key}")
            req.add_header("Content-Type", "application/json")
            try:
                with request.urlopen(req, timeout=30) as resp:
                    resp.read()
            except error.HTTPError as exc:
                raise RuntimeError(f"Airtable request failed: {exc.code} {exc.reason}") from exc
        return AirtableRecord(fields=fields)


class EmailClient:
    def __init__(self, settings: Settings, from_email: str, from_name: str = "BookLeaf Publishing"):
        self.settings = settings
        self.from_email = from_email
        self.from_name = from_name

    def compose(self, author_name: str, result: ValidationResult) -> str:
        issues = "\n".join(f"- ❌ {i.message}" for i in result.issues) or "- No issues detected."
        instructions = "\n".join(f"{idx+1}. {step}" for idx, step in enumerate(result.correction_instructions))
        return (
            f"Hi {author_name},\n\n"
            f"Your book cover status is: {result.status.value}\n\n"
            f"Issues:\n{issues}\n\n"
            f"Correction steps:\n{instructions}\n\n"
            f"Please resubmit within 1 business day.\n"
            f"If you need help, reply to the production team.\n"
        )

    def send(self, to_email: str, author_name: str, result: ValidationResult) -> str:
        body = self.compose(author_name, result)
        payload = {
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": self.from_email, "name": self.from_name},
            "subject": f"Book cover status: {result.status.value}",
            "content": [{"type": "text/plain", "value": body}],
        }
        if self.settings.sendgrid_reply_to_email:
            payload["reply_to"] = {"email": self.settings.sendgrid_reply_to_email}
        if not self.settings.dry_run:
            req = request.Request(
                "https://api.sendgrid.com/v3/mail/send",
                data=json.dumps(payload).encode("utf-8"),
                method="POST",
            )
            req.add_header("Authorization", f"Bearer {self.settings.sendgrid_api_key}")
            req.add_header("Content-Type", "application/json")
            try:
                with request.urlopen(req, timeout=30) as resp:
                    resp.read()
            except error.HTTPError as exc:
                raise RuntimeError(f"SendGrid request failed: {exc.code} {exc.reason}") from exc
        return body


class DriveClient:
    def __init__(self, settings: Settings):
        self.settings = settings

    def validate_access(self) -> dict[str, str]:
        return {
            "folder_id": self.settings.google_drive_folder_id,
            "service_account_json": self.settings.google_service_account_json,
            "note": "Drive access is configured; service-account JWT exchange requires a cryptography backend or pre-minted token.",
        }
