from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ScreenObservation:
    """Combined browser/screen perception snapshot.

    OCR is best-effort because pixel-perfect interpretation is not guaranteed across fonts,
    scaling, animations, and browser rendering differences. DOM and accessibility text are
    preferred because they are deterministic when available.
    """

    url: str
    title: str
    dom_text: str
    accessibility_text: str
    screenshot_path: str | None = None
    ocr_text: str = ""
    warnings: list[str] = field(default_factory=list)

    @property
    def combined_text(self) -> str:
        parts = [self.title, self.dom_text, self.accessibility_text, self.ocr_text]
        return "\n".join(part for part in parts if part).strip()


class BrowserScreenReader:
    """Reads a browser page using DOM text, accessibility tree, screenshot, and optional OCR."""

    def __init__(self, screenshot_dir: str = "runs/screens", enable_ocr: bool = True):
        self.screenshot_dir = Path(screenshot_dir)
        self.enable_ocr = enable_ocr

    def read(self, page: Any, name: str = "screen") -> ScreenObservation:
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        warnings: list[str] = []
        screenshot_path = self.screenshot_dir / f"{self._safe_name(name)}.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        dom_text = self._read_dom_text(page, warnings)
        accessibility_text = self._read_accessibility_text(page, warnings)
        ocr_text = self._read_ocr(screenshot_path, warnings) if self.enable_ocr else ""
        return ScreenObservation(
            url=getattr(page, "url", ""),
            title=self._safe_call(page, "title", warnings),
            dom_text=dom_text,
            accessibility_text=accessibility_text,
            screenshot_path=str(screenshot_path),
            ocr_text=ocr_text,
            warnings=warnings,
        )

    def _read_dom_text(self, page: Any, warnings: list[str]) -> str:
        try:
            return page.locator("body").inner_text(timeout=2_000).strip()
        except Exception as exc:
            warnings.append(f"dom_text_unavailable: {exc}")
            return ""

    def _read_accessibility_text(self, page: Any, warnings: list[str]) -> str:
        try:
            snapshot = page.accessibility.snapshot(interesting_only=False)
        except Exception as exc:
            warnings.append(f"accessibility_unavailable: {exc}")
            return ""
        texts: list[str] = []
        self._collect_accessibility_text(snapshot, texts)
        return "\n".join(texts)

    def _collect_accessibility_text(self, node: Any, texts: list[str]) -> None:
        if not isinstance(node, dict):
            return
        for key in ("name", "value", "description"):
            value = node.get(key)
            if isinstance(value, str) and value.strip():
                texts.append(value.strip())
        for child in node.get("children", []) or []:
            self._collect_accessibility_text(child, texts)

    def _read_ocr(self, screenshot_path: Path, warnings: list[str]) -> str:
        try:
            from PIL import Image
            import pytesseract
        except Exception as exc:
            warnings.append(f"ocr_unavailable: {exc}")
            return ""
        try:
            return pytesseract.image_to_string(Image.open(screenshot_path)).strip()
        except Exception as exc:
            warnings.append(f"ocr_failed: {exc}")
            return ""

    def _safe_call(self, obj: Any, method: str, warnings: list[str]) -> str:
        try:
            value = getattr(obj, method)()
            return str(value) if value is not None else ""
        except Exception as exc:
            warnings.append(f"{method}_unavailable: {exc}")
            return ""

    def _safe_name(self, value: str) -> str:
        return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)[:80] or "screen"
