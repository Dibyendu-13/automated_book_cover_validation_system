from __future__ import annotations

import json
import sys
import csv
from pathlib import Path

from .integrations import AirtableClient, EmailClient
from .helpers import extract_book_id
from .models import DetectedElement, Rect
from .settings import get_settings
from .workflow import CoverWorkflow
from .validators import CoverPayload, CoverValidator
from .vision import OpenAIVisionClient
from .evaluation import evaluate_folder


def demo() -> int:
    settings = get_settings()
    validator = CoverValidator()
    sample = CoverPayload(
        file_path="sample_cover.png",
        book_id="1234567890123",
        author_name="Ojal Jain",
        elements=[
            DetectedElement("author", Rect(120, 2120, 900, 160), 0.98),
            DetectedElement("body_text", Rect(20, 400, 1200, 300), 0.95),
        ],
    )
    result = validator.validate(sample)
    airtable = AirtableClient(settings).create_or_update(result, email="author@example.com")
    email = EmailClient(settings, from_email=settings.sendgrid_from_email).compose(sample.author_name or "Author", result)
    print(json.dumps({
        "loaded_settings": {
            "google_service_account_json": settings.google_service_account_json,
            "google_drive_folder_id": settings.google_drive_folder_id,
            "airtable_base_id": settings.airtable_base_id,
            "airtable_table_name": settings.airtable_table_name,
            "app_env": settings.app_env,
            "log_level": settings.log_level,
            "openai_api_key_set": bool(settings.openai_api_key),
        }
    }, indent=2))
    print(json.dumps(result.to_dict(), indent=2))
    print(json.dumps(airtable.fields, indent=2))
    print(email)
    return 0


def process_one() -> int:
    settings = get_settings()
    workflow = CoverWorkflow(settings, from_email=settings.sendgrid_from_email)
    sample = CoverPayload(
        file_path="sample_cover.png",
        book_id="1234567890123",
        author_name="Ojal Jain",
        elements=[
            DetectedElement("author", Rect(120, 2120, 900, 160), 0.98),
            DetectedElement("body_text", Rect(20, 400, 1200, 300), 0.95),
        ],
    )
    outcome = workflow.process(sample, author_email="author@example.com")
    print(json.dumps(outcome.__dict__, indent=2))
    return 0


def batch_validate(folder: str = "validation_book_covers") -> int:
    settings = get_settings()
    validator = CoverValidator()
    vision_client = OpenAIVisionClient(settings.openai_api_key) if settings.openai_api_key else None
    root = Path(folder)
    if not root.exists():
        print(f"Folder not found: {folder}")
        return 2

    results = []
    image_paths = sorted(list(root.glob("*.png")) + list(root.glob("*.jpg")) + list(root.glob("*.jpeg")))
    for path in image_paths:
        book_id = extract_book_id(path.name)
        payload = CoverPayload(
            file_path=str(path),
            book_id=book_id,
            author_name="Unknown Author",
            elements=[],
        )
        vision = vision_client.analyze(str(path)) if vision_client and not settings.dry_run else None
        result = validator.validate(payload, vision=vision)
        results.append({
            "file": path.name,
            "book_id": book_id,
            "status": result.status.value,
            "confidence": result.confidence_score,
            "issues": [i.issue_type for i in result.issues],
            "vision": vision.__dict__ if vision else None,
        })

    report = {
        "folder": str(root),
        "count": len(results),
        "pass": sum(1 for r in results if r["status"] == "PASS"),
        "review_needed": sum(1 for r in results if r["status"] == "REVIEW NEEDED"),
        "results": results,
    }
    metrics = {
        "total": report["count"],
        "pass_rate": round((report["pass"] / report["count"]) * 100, 2) if report["count"] else 0.0,
        "review_rate": round((report["review_needed"] / report["count"]) * 100, 2) if report["count"] else 0.0,
        "advisory_low_resolution_only": sum(1 for r in results if r["issues"] == ["low_resolution"]),
    }
    report_path = root / "batch_report.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    csv_path = root / "batch_report.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "book_id", "status", "confidence", "issues"])
        writer.writeheader()
        for row in results:
            writer.writerow({k: row.get(k, "") for k in ["file", "book_id", "status", "confidence", "issues"]})
    metrics_path = root / "accuracy_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Saved report to {report_path}")
    print(f"Saved CSV to {csv_path}")
    print(f"Saved metrics to {metrics_path}")
    return 0


def evaluate(folder: str = "validation_book_covers", truth_path: str = "validation_book_covers/ground_truth.json") -> int:
    result = evaluate_folder(folder, truth_path)
    payload = {
        "total": result.total,
        "correct": result.correct,
        "accuracy": result.accuracy,
        "details": result.details,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else "demo"
    try:
        if command == "demo":
            return demo()
        if command == "process":
            return process_one()
        if command == "batch":
            folder = sys.argv[2] if len(sys.argv) > 2 else "validation_book_covers"
            return batch_validate(folder)
        if command == "evaluate":
            folder = sys.argv[2] if len(sys.argv) > 2 else "validation_book_covers"
            truth_path = sys.argv[3] if len(sys.argv) > 3 else "validation_book_covers/ground_truth.json"
            return evaluate(folder, truth_path)
        print("Usage: bookleaf-validate [demo|process]")
        return 1
    except RuntimeError as exc:
        print(f"Runtime error: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
