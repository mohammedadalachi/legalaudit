"""
ocr_processor.py

Handles text extraction for LegalAudit: digital PDFs, scanned PDFs,
images (jpg/png/bmp/tiff), and plain text files.

This module never raises on its own - every function returns a result
dict so the Flask layer doesn't have to wrap every call in a try/except.
"""

import os
import re
import logging
import traceback

log = logging.getLogger("legalaudit.ocr")


def _result(text: str = "", method: str = "none",
            pages: int = 0, error: str = None) -> dict:
    """Builds the standard return shape used everywhere in this module."""
    return {
        "text": text if isinstance(text, str) else "",
        "method": method if isinstance(method, str) else "none",
        "pages": pages if isinstance(pages, int) else 0,
        "error": error
    }


# main entry point
def extract_text(file_path: str) -> dict:
    """
    Entry point - figures out the file type and sends it to the right
    extractor. Returns {"text", "method", "pages", "error"}.
    """
    # basic sanity checks before we even look at the extension
    if not file_path or not isinstance(file_path, str):
        return _result(error="No file path provided.")

    if not os.path.exists(file_path):
        return _result(error=f"File not found: '{file_path}'.")

    if not os.path.isfile(file_path):
        return _result(error=f"Path is not a file: '{file_path}'.")

    try:
        size = os.path.getsize(file_path)
        if size == 0:
            return _result(error="The file is empty (0 bytes).")
        log.info("Extracting text from '%s' (%s bytes)", file_path, f"{size:,}")
    except OSError as e:
        return _result(error=f"Cannot read file metadata: {e}")

    # Route by extension
    try:
        ext = os.path.splitext(file_path)[1].lower()
    except Exception as e:
        return _result(error=f"Could not determine file extension: {e}")

    if ext == ".pdf":
        return _extract_from_pdf(file_path)
    elif ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"):
        return _extract_from_image(file_path)
    elif ext == ".txt":
        return _extract_from_txt(file_path)
    else:
        return _result(
            error=(
                f"Unsupported file type '{ext}'. "
                "Supported: PDF, JPG, PNG, BMP, TIFF, TXT."
            )
        )


# pdf extraction
def _extract_from_pdf(file_path: str) -> dict:
    """
    Multi-layer PDF text extraction:
      Layer 1 , PyMuPDF sorted blocks  (handles most digital PDFs)
      Layer 2 , pdfplumber             (catches tables / tricky layouts)
      Layer 3 , Tesseract OCR          (scanned / image-only PDFs)

    The layer that extracts the most text wins.
    """
    # Check PyMuPDF is available
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return _result(
            error="PyMuPDF is not installed. Run: pip install pymupdf"
        )

    # Open document
    try:
        doc = fitz.open(file_path)
    except fitz.FileDataError:
        return _result(
            error=(
                "This PDF appears to be corrupted or is not a valid PDF file. "
                "Try re-saving or re-exporting the document."
            )
        )
    except fitz.PasswordError:
        return _result(
            error=(
                "This PDF is password-protected. "
                "Please remove the password before uploading."
            )
        )
    except Exception as e:
        return _result(
            error=(
                f"Could not open PDF: {e}. "
                "The file may be corrupted or in an unsupported format."
            )
        )

    try:
        pages = len(doc)
        if pages == 0:
            doc.close()
            return _result(error="The PDF has no pages.")

        log.info("PDF opened: %d page(s)", pages)

        # Layer 1: PyMuPDF
        fitz_text = ""
        try:
            for page in doc:
                try:
                    blocks = page.get_text("blocks", sort=True)
                    for block in blocks:
                        block_text = block[4].strip() if len(block) > 4 else ""
                        if block_text:
                            fitz_text += block_text + "\n"
                    fitz_text += "\n"
                except Exception as e:
                    log.warning("Error reading page %d with PyMuPDF: %s", page.number, e)
            fitz_text = _clean_text(fitz_text)
            log.info("Layer 1 (PyMuPDF): %d chars", len(fitz_text))
        except Exception as e:
            log.warning("PyMuPDF layer failed: %s", e)
            fitz_text = ""

        # Layer 2: pdfplumber
        plumber_text = ""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    try:
                        page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                        if page_text:
                            plumber_text += page_text + "\n"
                    except Exception as e:
                        log.warning("pdfplumber error on page %d: %s", page.page_number, e)
            plumber_text = _clean_text(plumber_text)
            log.info("Layer 2 (pdfplumber): %d chars", len(plumber_text))
        except ImportError:
            log.info("pdfplumber not installed , skipping Layer 2")
        except Exception as e:
            log.warning("pdfplumber layer failed: %s", e)

        # Pick whichever layer extracted more text
        if len(plumber_text) > len(fitz_text):
            best_text = plumber_text
            method    = "pdfplumber (digital PDF)"
        else:
            best_text = fitz_text
            method    = "PyMuPDF (digital PDF)"

        # Layer 3: Tesseract OCR for scanned PDFs
        if len(best_text.strip()) < 200:
            log.info("Fewer than 200 chars extracted , attempting OCR (scanned PDF)")
            doc.close()
            return _ocr_pdf_with_tesseract(file_path, pages)

        doc.close()
        return _result(text=best_text, method=method, pages=pages)

    except Exception as e:
        try:
            doc.close()
        except Exception:
            pass
        log.error("Unexpected error in _extract_from_pdf: %s\n%s", e, traceback.format_exc())
        return _result(
            error=(
                f"An unexpected error occurred while reading the PDF: {e}. "
                "The file may be corrupted or in an unsupported format."
            )
        )


def _ocr_pdf_with_tesseract(file_path: str, pages: int) -> dict:
    """Convert scanned PDF pages to images and OCR each page with Tesseract."""
    try:
        import fitz
    except ImportError:
        return _result(error="PyMuPDF is not installed. Run: pip install pymupdf")

    try:
        import pytesseract
    except ImportError:
        return _result(
            error=(
                "pytesseract is not installed. "
                "Run: pip install pytesseract  "
                "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
            )
        )

    try:
        from PIL import Image
        import io as _io
    except ImportError:
        return _result(error="Pillow is not installed. Run: pip install pillow")

    # Verify Tesseract binary is reachable
    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return _result(
            error=(
                "Tesseract OCR executable was not found. "
                "Install Tesseract and ensure it is on your PATH. "
                "Guide: https://github.com/tesseract-ocr/tesseract"
            )
        )
    except Exception as e:
        log.warning("Could not verify Tesseract version: %s", e)

    try:
        doc = fitz.open(file_path)
    except Exception as e:
        return _result(error=f"Could not reopen PDF for OCR: {e}")

    full_text = ""
    failed_pages = []

    try:
        for page in doc:
            try:
                mat      = fitz.Matrix(300 / 72, 300 / 72)  # 300 DPI
                pix      = page.get_pixmap(matrix=mat)
                img_data = pix.tobytes("png")
                img      = Image.open(_io.BytesIO(img_data))
                page_text = pytesseract.image_to_string(img, lang="eng")
                full_text += page_text + "\n"
                log.info("OCR page %d: %d chars", page.number + 1, len(page_text))
            except Exception as e:
                log.warning("OCR failed on page %d: %s", page.number + 1, e)
                failed_pages.append(page.number + 1)

        doc.close()

        cleaned = _clean_text(full_text)

        if not cleaned.strip():
            msg = "Tesseract OCR could not extract any text from this document."
            if failed_pages:
                msg += f" Failed pages: {failed_pages}."
            return _result(error=msg)

        if failed_pages:
            log.warning("OCR completed with failures on pages: %s", failed_pages)

        return _result(
            text=cleaned,
            method=f"Tesseract OCR (scanned PDF)",
            pages=pages
        )

    except Exception as e:
        try:
            doc.close()
        except Exception:
            pass
        log.error("Unexpected error in Tesseract OCR: %s\n%s", e, traceback.format_exc())
        return _result(error=f"OCR failed unexpectedly: {e}")


# image extraction
def _extract_from_image(file_path: str) -> dict:
    """Run Tesseract OCR directly on an image file."""
    try:
        import pytesseract
    except ImportError:
        return _result(
            error=(
                "pytesseract is not installed. Run: pip install pytesseract  "
                "Also install Tesseract OCR: https://github.com/tesseract-ocr/tesseract"
            )
        )

    try:
        from PIL import Image
    except ImportError:
        return _result(error="Pillow is not installed. Run: pip install pillow")

    try:
        pytesseract.get_tesseract_version()
    except pytesseract.TesseractNotFoundError:
        return _result(
            error=(
                "Tesseract OCR executable was not found. "
                "Install Tesseract and ensure it is on your PATH."
            )
        )
    except Exception as e:
        log.warning("Could not verify Tesseract version: %s", e)

    try:
        img = Image.open(file_path)
    except FileNotFoundError:
        return _result(error=f"Image file not found: '{file_path}'.")
    except Exception as e:
        return _result(
            error=(
                f"Could not open image file: {e}. "
                "The file may be corrupted or in an unsupported image format."
            )
        )

    try:
        text = pytesseract.image_to_string(img, lang="eng")
    except pytesseract.TesseractError as e:
        return _result(error=f"Tesseract OCR failed: {e}")
    except Exception as e:
        log.error("Unexpected error in image OCR: %s\n%s", e, traceback.format_exc())
        return _result(error=f"OCR encountered an unexpected error: {e}")

    cleaned = _clean_text(text)
    if not cleaned.strip():
        return _result(
            error=(
                "OCR could not extract any text from this image. "
                "Ensure the image is clear, well-lit, and contains readable text."
            )
        )

    log.info("Image OCR: %d chars extracted", len(cleaned))
    return _result(text=cleaned, method="Tesseract OCR (image)", pages=1)


# plain text
def _extract_from_txt(file_path: str) -> dict:
    """Plain text , read directly, no extraction needed."""
    # Try UTF-8 first, then fall back to latin-1 (always succeeds for single-byte files)
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            with open(file_path, "r", encoding=encoding, errors="replace") as f:
                text = f.read()
            cleaned = _clean_text(text)
            log.info("Plain text read (%s): %d chars", encoding, len(cleaned))
            return _result(text=cleaned, method="Plain text", pages=1)
        except UnicodeDecodeError:
            continue
        except PermissionError:
            return _result(
                error=(
                    f"Permission denied reading '{file_path}'. "
                    "Check file permissions."
                )
            )
        except OSError as e:
            return _result(error=f"Could not read file: {e}")
        except Exception as e:
            log.error("Unexpected error reading text file: %s\n%s", e, traceback.format_exc())
            return _result(error=f"Unexpected error reading text file: {e}")

    return _result(
        error=(
            "Could not decode the text file. "
            "Please ensure it is saved in UTF-8 or plain ASCII encoding."
        )
    )


# cleanup
def _clean_text(text: str) -> str:
    """
    Clean up OCR/extracted text:
    - Remove null bytes and control characters
    - Normalise whitespace while preserving paragraph breaks
    - Do NOT fix l→1 / 0→O to preserve legal text exactly
    """
    if not isinstance(text, str):
        log.warning("_clean_text received non-string: %s", type(text).__name__)
        return ""
    try:
        # Remove null bytes and non-printable control chars (keep \n \t)
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Collapse multiple spaces/tabs on the same line
        text = re.sub(r"[ \t]+", " ", text)
        # Collapse more than 2 consecutive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
    except Exception as e:
        log.warning("Error in _clean_text: %s", e)
        return text.strip() if isinstance(text, str) else ""
