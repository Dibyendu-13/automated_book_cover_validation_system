from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    google_service_account_json: str
    google_drive_folder_id: str
    airtable_api_key: str
    airtable_base_id: str
    airtable_table_name: str
    sendgrid_api_key: str
    sendgrid_from_email: str
    sendgrid_reply_to_email: str | None = None
    openai_api_key: str | None = None
    app_env: str = "development"
    log_level: str = "info"
    dry_run: bool = True


def load_dotenv(path: str = ".env") -> None:
    env_path = Path(path)
    if not env_path.exists():
        return
    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_settings() -> Settings:
    load_dotenv()
    required = [
        "GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_DRIVE_FOLDER_ID",
        "AIRTABLE_API_KEY",
        "AIRTABLE_BASE_ID",
        "AIRTABLE_TABLE_NAME",
        "SENDGRID_API_KEY",
        "SENDGRID_FROM_EMAIL",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
    return Settings(
        google_service_account_json=os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"],
        google_drive_folder_id=os.environ["GOOGLE_DRIVE_FOLDER_ID"],
        airtable_api_key=os.environ["AIRTABLE_API_KEY"],
        airtable_base_id=os.environ["AIRTABLE_BASE_ID"],
        airtable_table_name=os.environ["AIRTABLE_TABLE_NAME"],
        sendgrid_api_key=os.environ["SENDGRID_API_KEY"],
        sendgrid_from_email=os.environ["SENDGRID_FROM_EMAIL"],
        sendgrid_reply_to_email=os.getenv("SENDGRID_REPLY_TO_EMAIL"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        app_env=os.getenv("APP_ENV", "development"),
        log_level=os.getenv("LOG_LEVEL", "info"),
        dry_run=os.getenv("DRY_RUN", "true").lower() in {"1", "true", "yes", "on"},
    )
