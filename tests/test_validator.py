from __future__ import annotations

import unittest

from bookleaf_validation.models import DetectedElement, Rect, Status
from bookleaf_validation.validators import CoverPayload, CoverValidator


class ValidatorTests(unittest.TestCase):
    def test_badge_overlap_is_flagged(self):
        validator = CoverValidator()
        payload = CoverPayload(
            file_path="sample_cover.png",
            book_id="123",
            elements=[DetectedElement("author", Rect(100, 2140, 800, 120), 0.99)],
        )
        result = validator.validate(payload)
        self.assertEqual(result.status, Status.REVIEW_NEEDED)
        self.assertTrue(any(i.issue_type == "award_badge_overlap" for i in result.issues))

    def test_safe_cover_can_pass(self):
        validator = CoverValidator()
        payload = CoverPayload(
            file_path="sample_cover.png",
            book_id="123",
            elements=[DetectedElement("author", Rect(100, 150, 800, 120), 0.99)],
        )
        result = validator.validate(payload)
        self.assertIn(result.status, {Status.PASS, Status.REVIEW_NEEDED})


if __name__ == "__main__":
    unittest.main()

