from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .helpers import extract_book_id
from .validators import CoverPayload, CoverValidator
from .vision import VisionAnalysis


@dataclass
class EvaluationResult:
    total: int
    correct: int
    accuracy: float
    details: list[dict]


def evaluate_folder(folder: str, truth_path: str) -> EvaluationResult:
    root = Path(folder)
    truth = json.loads(Path(truth_path).read_text(encoding="utf-8"))
    validator = CoverValidator()
    details: list[dict] = []
    correct = 0
    image_paths = sorted(list(root.glob("*.png")) + list(root.glob("*.jpg")) + list(root.glob("*.jpeg")))
    for path in image_paths:
        expected = truth.get(path.name)
        if expected is None:
            continue
        result = validator.validate(
            CoverPayload(
                file_path=str(path),
                book_id=extract_book_id(path.name),
                author_name="Unknown Author",
                elements=[],
            ),
            vision=None,
        )
        actual = result.status.value
        is_correct = actual == expected
        correct += 1 if is_correct else 0
        details.append({
            "file": path.name,
            "expected": expected,
            "actual": actual,
            "correct": is_correct,
        })
    total = len(details)
    accuracy = round((correct / total) * 100, 2) if total else 0.0
    return EvaluationResult(total=total, correct=correct, accuracy=accuracy, details=details)

