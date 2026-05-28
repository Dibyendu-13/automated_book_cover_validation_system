from __future__ import annotations

import re
from pathlib import Path


def extract_book_id(filename: str) -> str:
    stem = Path(filename).stem
    match = re.search(r"(97[89]\d{10}|\d{13})", stem)
    if match:
        return match.group(1)
    return stem.split()[0]

