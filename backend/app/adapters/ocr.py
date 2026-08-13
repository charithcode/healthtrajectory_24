"""OCR extension point; providers are intentionally optional for the MVP."""

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class OCRResult:
    text: str
    success: bool
    provider: str
    warnings: list[str]


class OCRProvider(Protocol):
    name: str

    def extract_text(self, file_path: str | Path) -> OCRResult: ...


class UnavailableOCRProvider:
    """Safe default used until Tesseract or PaddleOCR is deliberately configured."""

    name = "unconfigured"

    def extract_text(self, file_path: str | Path) -> OCRResult:
        return OCRResult(
            text="",
            success=False,
            provider=self.name,
            warnings=["OCR is not configured. Install and configure one provider to process scanned PDFs."],
        )
