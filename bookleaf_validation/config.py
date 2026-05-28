from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoverSpec:
    width_in: float = 5.0
    height_in: float = 8.0
    dpi: int = 300
    margin_mm: float = 3.0
    badge_reserved_bottom_mm: float = 9.0

    @property
    def width_px(self) -> int:
        return int(self.width_in * self.dpi)

    @property
    def height_px(self) -> int:
        return int(self.height_in * self.dpi)

    @property
    def margin_px(self) -> float:
        return self.margin_mm / 25.4 * self.dpi

    @property
    def badge_height_px(self) -> float:
        return self.badge_reserved_bottom_mm / 25.4 * self.dpi

    @property
    def safe_area(self):
        return {
            "left": self.margin_px,
            "right": self.width_px - self.margin_px,
            "top": self.margin_px,
            "bottom": self.height_px - self.margin_px - self.badge_height_px,
        }

