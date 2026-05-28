from __future__ import annotations

import os
import struct


def read_png_dimensions(path: str) -> tuple[int, int]:
    with open(path, "rb") as f:
        header = f.read(24)
    if len(header) < 24 or header[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a PNG file")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def file_quality_signal(path: str) -> dict[str, float]:
    size_bytes = os.path.getsize(path)
    try:
        width, height = read_png_dimensions(path)
    except Exception:
        width, height = 0, 0
    pixel_count = max(1, width * height)
    bytes_per_pixel = size_bytes / pixel_count
    if width >= 1500 and height >= 2400:
        resolution_score = 100.0 if bytes_per_pixel >= 0.01 else 85.0
    else:
        resolution_score = min(100.0, max(0.0, (size_bytes / 500_000.0) * 100.0))
    return {
        "file_size_kb": size_bytes / 1024.0,
        "resolution_score": resolution_score,
    }
