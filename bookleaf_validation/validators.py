from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import CoverSpec
from .image_io import file_quality_signal, read_png_dimensions
from .models import DetectedElement, Rect, Severity, Status, ValidationIssue, ValidationResult
from .vision import VisionAnalysis


@dataclass
class CoverPayload:
    file_path: str
    book_id: str
    author_name: str | None = None
    elements: list[DetectedElement] | None = None


class CoverValidator:
    def __init__(self, spec: CoverSpec | None = None):
        self.spec = spec or CoverSpec()

    def validate(self, payload: CoverPayload, vision: VisionAnalysis | None = None) -> ValidationResult:
        path = Path(payload.file_path)
        issues: list[ValidationIssue] = []
        correction_instructions: list[str] = []
        revision_tracking = {"file_name": path.name, "format": path.suffix.lower().lstrip(".")}

        if path.suffix.lower() == ".png":
            if path.exists():
                width, height = read_png_dimensions(str(path))
                if width < self.spec.width_px or height < self.spec.height_px:
                    issues.append(ValidationIssue(
                        "low_resolution",
                        Severity.HIGH,
                        f"Image resolution is below target: {width}x{height}px",
                        0.95,
                    ))
            else:
                width, height = self.spec.width_px, self.spec.height_px
                issues.append(ValidationIssue(
                    "missing_asset",
                    Severity.LOW,
                    "Demo mode: sample PNG not found, using spec defaults.",
                    0.90,
                ))
        else:
            issues.append(ValidationIssue(
                "unsupported_format",
                Severity.MEDIUM,
                "PDF validation requires a rasterization backend in production.",
                0.70,
            ))
            width, height = self.spec.width_px, self.spec.height_px

        safe = self.spec.safe_area
        badge_zone = Rect(0, safe["bottom"], self.spec.width_px, self.spec.height_px - safe["bottom"])

        for element in payload.elements or []:
            if element.label.lower() in {"author", "author_name"}:
                if not self._within_safe_area(element.bbox):
                    issues.append(ValidationIssue(
                        "author_outside_safe_area",
                        Severity.MEDIUM,
                        "Author name extends beyond the safe area.",
                        element.confidence,
                        [element.bbox],
                    ))
                if element.bbox.intersects(badge_zone):
                    issues.append(ValidationIssue(
                        "award_badge_overlap",
                        Severity.CRITICAL,
                        "Author name overlaps the award badge zone.",
                        element.confidence,
                        [element.bbox, badge_zone],
                    ))
            if element.label.lower() in {"body_text", "back_cover_text"}:
                if element.bbox.x < self.spec.margin_px or element.bbox.y < self.spec.margin_px:
                    issues.append(ValidationIssue(
                        "border_spacing_violation",
                        Severity.MEDIUM,
                        "Text is too close to the cover border.",
                        element.confidence,
                        [element.bbox],
                    ))

        quality = file_quality_signal(str(path)) if path.exists() else {"resolution_score": 50.0}
        if quality["resolution_score"] < 40:
            issues.append(ValidationIssue(
                "image_quality_low",
                Severity.MEDIUM,
                "Low file-size signal suggests possible pixelation or compression artifacts.",
                0.60,
            ))
        if vision:
            if vision.likely_badge_overlap:
                issues.append(ValidationIssue(
                    "award_badge_overlap_vision",
                    Severity.CRITICAL,
                    "Vision analysis suggests text may overlap the award badge zone.",
                    0.92,
                ))
            if vision.low_quality:
                issues.append(ValidationIssue(
                    "image_quality_low_vision",
                    Severity.MEDIUM,
                    "Vision analysis suggests the cover is blurry or pixelated.",
                    0.90,
                ))
            if not vision.author_name_present:
                issues.append(ValidationIssue(
                    "author_not_detected",
                    Severity.MEDIUM,
                    "Vision analysis could not confidently detect the author name.",
                    0.75,
                ))
            if vision.notes:
                revision_tracking["vision_notes"] = " | ".join(vision.notes)

        score = self._confidence_score(issues)
        status = Status.PASS if not issues else Status.REVIEW_NEEDED
        if issues:
            correction_instructions.extend(self._instructions_for(issues))
        else:
            correction_instructions.append("No changes required.")

        return ValidationResult(
            book_id=payload.book_id,
            status=status,
            confidence_score=score,
            issues=issues,
            correction_instructions=correction_instructions,
            revision_tracking=revision_tracking,
        )

    def _within_safe_area(self, bbox: Rect) -> bool:
        safe = self.spec.safe_area
        return (
            bbox.x >= safe["left"]
            and bbox.y >= safe["top"]
            and bbox.x + bbox.w <= safe["right"]
            and bbox.y + bbox.h <= safe["bottom"]
        )

    def _confidence_score(self, issues: list[ValidationIssue]) -> float:
        if not issues:
            return 99.0
        critical = any(i.severity == Severity.CRITICAL for i in issues)
        base = 92.0 if not critical else 72.0
        penalty = min(30.0, sum((1.0 - i.confidence) * 20.0 for i in issues))
        return max(0.0, base - penalty)

    def _instructions_for(self, issues: list[ValidationIssue]) -> list[str]:
        steps: list[str] = []
        types = {i.issue_type for i in issues}
        if "award_badge_overlap" in types:
            steps.append("Move the author name upward so it clears the bottom 9mm award badge zone.")
        if "author_outside_safe_area" in types:
            steps.append("Keep the author name within the 3mm side and top safe margins.")
        if "border_spacing_violation" in types:
            steps.append("Increase padding around body text and keep all text away from the edge margins.")
        if "low_resolution" in types or "image_quality_low" in types:
            steps.append("Resubmit a higher-resolution export with less compression.")
        if "unsupported_format" in types:
            steps.append("Convert the PDF through the production rasterization pipeline before resubmission.")
        return steps
