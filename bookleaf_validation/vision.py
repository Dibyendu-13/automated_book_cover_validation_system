from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from urllib import error, request


@dataclass(frozen=True)
class VisionAnalysis:
    author_name_present: bool
    likely_badge_overlap: bool
    low_quality: bool
    notes: list[str]


class OpenAIVisionClient:
    def __init__(self, api_key: str, model: str = "gpt-4.1-mini"):
        self.api_key = api_key
        self.model = model

    def analyze(self, image_path: str) -> VisionAnalysis:
        image_bytes = Path(image_path).read_bytes()
        data_url = "data:image/png;base64," + base64.b64encode(image_bytes).decode("ascii")
        payload = {
            "model": self.model,
            "input": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Analyze this book cover for layout validation. "
                                "Return strict JSON with keys: author_name_present (bool), "
                                "likely_badge_overlap (bool), low_quality (bool), notes (array of strings). "
                                "Focus on whether the author name appears too close to the bottom badge area, "
                                "whether text is near borders, and whether the image appears pixelated or blurred."
                            ),
                        },
                        {"type": "input_image", "image_url": data_url, "detail": "high"},
                    ],
                }
            ],
        }
        req = request.Request(
            "https://api.openai.com/v1/responses",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
        )
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with request.urlopen(req, timeout=60) as resp:
                response_text = resp.read().decode("utf-8").strip()
        except error.HTTPError as exc:
            raise RuntimeError(f"OpenAI vision request failed: {exc.code} {exc.reason}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenAI vision request failed: {exc.reason}") from exc

        if not response_text:
            raise RuntimeError("OpenAI vision returned an empty response")

        try:
            raw = json.loads(response_text)
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OpenAI vision returned non-JSON output: {response_text[:200]}") from exc

        text = raw.get("output_text") or ""
        if not text and raw.get("output"):
            chunks = []
            for item in raw["output"]:
                for content in item.get("content", []):
                    if content.get("type") in {"output_text", "text"}:
                        chunks.append(content.get("text", ""))
            text = "".join(chunks)
        if not text.strip():
            raise RuntimeError("OpenAI vision output did not contain usable text")
        data = json.loads(text)
        return VisionAnalysis(
            author_name_present=bool(data.get("author_name_present")),
            likely_badge_overlap=bool(data.get("likely_badge_overlap")),
            low_quality=bool(data.get("low_quality")),
            notes=[str(x) for x in data.get("notes", [])],
        )
