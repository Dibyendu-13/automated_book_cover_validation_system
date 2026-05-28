from __future__ import annotations

from dataclasses import dataclass, asdict, field
from enum import Enum


class Status(str, Enum):
    PASS = "PASS"
    REVIEW_NEEDED = "REVIEW NEEDED"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class Rect:
    x: float
    y: float
    w: float
    h: float

    def intersects(self, other: "Rect") -> bool:
        return not (
            self.x + self.w <= other.x
            or other.x + other.w <= self.x
            or self.y + self.h <= other.y
            or other.y + other.h <= self.y
        )

    def expanded(self, pad: float) -> "Rect":
        return Rect(self.x - pad, self.y - pad, self.w + 2 * pad, self.h + 2 * pad)


@dataclass(frozen=True)
class DetectedElement:
    label: str
    bbox: Rect
    confidence: float = 1.0


@dataclass
class ValidationIssue:
    issue_type: str
    severity: Severity
    message: str
    confidence: float
    annotations: list[Rect] = field(default_factory=list)


@dataclass
class ValidationResult:
    book_id: str
    status: Status
    confidence_score: float
    issues: list[ValidationIssue]
    correction_instructions: list[str]
    revision_tracking: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "book_id": self.book_id,
            "status": self.status.value,
            "confidence_score": round(self.confidence_score, 2),
            "issues": [
                {
                    "issue_type": i.issue_type,
                    "severity": i.severity.value,
                    "message": i.message,
                    "confidence": round(i.confidence, 2),
                    "annotations": [asdict(a) for a in i.annotations],
                }
                for i in self.issues
            ],
            "correction_instructions": self.correction_instructions,
            "revision_tracking": self.revision_tracking,
        }

