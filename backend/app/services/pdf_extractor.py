"""PyMuPDF text extraction and Tesseract OCR for uploaded health-report PDFs."""

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import fitz
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

TESSERACT_EXE_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


@dataclass(frozen=True)
class PdfPageText:
    page_number: int
    text: str


@dataclass(frozen=True)
class PdfExtractionResult:
    extracted_text: str
    page_count: int
    extraction_success: bool
    extraction_method: str
    warnings: list[str] = field(default_factory=list)
    pages: list[PdfPageText] = field(default_factory=list)


def get_tesseract_path() -> str | None:
    """Retrieve the Tesseract OCR executable path if available."""
    # 1. Check if on system PATH
    tesseract_bin = shutil.which("tesseract")
    if tesseract_bin:
        return tesseract_bin
    # 2. Check default Windows path
    if Path(TESSERACT_EXE_PATH).exists():
        return TESSERACT_EXE_PATH
    return None


def is_tesseract_installed() -> bool:
    """Check if Tesseract is installed and accessible."""
    return get_tesseract_path() is not None


# Configure pytesseract path if Tesseract is found
_tesseract_path = get_tesseract_path()
if _tesseract_path:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_path


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """Apply generic preprocessing steps to improve OCR results.

    Steps:
    1. Convert to grayscale.
    2. Enhance contrast.
    3. Apply sharpening.
    """
    # Grayscale
    gray = image.convert("L")
    # Enhance contrast (factor of 2.0)
    enhancer = ImageEnhance.Contrast(gray)
    contrast = enhancer.enhance(2.0)
    # Sharpen
    sharpened = contrast.filter(ImageFilter.SHARPEN)
    return sharpened


def _run_ocr_for_pdf(file_path: Path) -> list[dict[str, object]]:
    """Render all PDF pages and perform Tesseract OCR on each."""
    if not is_tesseract_installed():
        raise RuntimeError("Tesseract OCR is not installed or not found on the system path.")

    results = []
    with fitz.open(file_path) as document:
        for index, page in enumerate(document):
            page_number = index + 1
            # Render page to high quality (300 DPI) using fitz.Matrix
            zoom = 300 / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert to Pillow Image
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Preprocess the rendered page image
            preprocessed = preprocess_image_for_ocr(image)
            
            # Run OCR to extract text
            text = pytesseract.image_to_string(preprocessed).strip()
            
            results.append({
                "page_number": page_number,
                "text": text,
            })
            
    return results


def extract_text_from_pdf(file_path: str | Path) -> PdfExtractionResult:
    """Extract PDF text using Tesseract OCR for every page."""
    path = Path(file_path)

    if not is_tesseract_installed():
        return PdfExtractionResult(
            extracted_text="",
            page_count=0,
            extraction_success=False,
            extraction_method="none",
            warnings=[
                "Tesseract OCR is not installed or not accessible. Please install Tesseract-OCR for Windows from https://github.com/UB-Mannheim/tesseract/wiki and ensure it is located at C:\\Program Files\\Tesseract-OCR\\tesseract.exe or added to your system PATH."
            ]
        )

    try:
        ocr_results = _run_ocr_for_pdf(path)
    except (fitz.FileDataError, OSError, RuntimeError, pytesseract.TesseractError) as error:
        logger.error("OCR failed for %s: %s", path, error)
        return PdfExtractionResult(
            extracted_text="",
            page_count=0,
            extraction_success=False,
            extraction_method="none",
            warnings=[f"OCR failed to process PDF: {error}"],
        )

    pages = [
        PdfPageText(
            page_number=int(page_data["page_number"]),
            text=str(page_data["text"]),
        )
        for page_data in ocr_results
    ]

    extracted_text = "\n\n".join(page.text for page in pages if page.text).strip()
    warnings: list[str] = []

    if not extracted_text:
        logger.warning("OCR returned no text for %s", path)
        warnings.append("OCR returned no text for the PDF. The document may be blank or poor quality.")

    return PdfExtractionResult(
        extracted_text=extracted_text,
        page_count=len(pages),
        extraction_success=True,
        extraction_method="ocr",
        warnings=warnings,
        pages=pages,
    )
