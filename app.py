# flask backend for legalaudit
# run with: python app.py

import os
import sys
import uuid
import io
import logging
import traceback
from datetime import datetime

from flask import Flask, request, jsonify, render_template, send_file
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("legalaudit.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("legalaudit.app")

# import our other modules, bail out if any are missing
try:
    from ocr_processor import extract_text
except ImportError as e:
    log.critical("FATAL: Could not import ocr_processor , %s", e)
    sys.exit(1)

try:
    from inference_engine import analyse
except ImportError as e:
    log.critical("FATAL: Could not import inference_engine , %s", e)
    sys.exit(1)

try:
    from pdf_report import generate_pdf_report
except ImportError as e:
    log.critical("FATAL: Could not import pdf_report , %s", e)
    sys.exit(1)

# config
app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "bmp", "tiff", "tif", "txt"}
MAX_FILE_SIZE_MB = 16
MAX_TEXT_LENGTH = 500_000   # chars, prevents absurdly large pastes
MIN_TEXT_LENGTH = 50        # chars, rejects near-empty submissions
VALID_DOC_TYPES = ("employment", "tenancy")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE_MB * 1024 * 1024

try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError as e:
    log.critical("Cannot create upload folder '%s' , %s", UPLOAD_FOLDER, e)
    sys.exit(1)


# small helpers
def _err(message: str, code: int = 400, detail: str = None) -> tuple:
    """Return a consistent JSON error envelope."""
    payload = {"error": message}
    if detail:
        payload["detail"] = detail
    log.warning("HTTP %s , %s%s", code, message, f" | {detail}" if detail else "")
    return jsonify(payload), code


def _allowed_file(filename: str) -> bool:
    return (
        bool(filename)
        and "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def _safe_doc_type(raw) -> str:
    if isinstance(raw, str):
        cleaned = raw.strip().lower()
        if cleaned in VALID_DOC_TYPES:
            return cleaned
    return None


def _cleanup(filepath: str):
    """Delete a temp file, swallowing errors so callers never crash on cleanup."""
    try:
        if filepath and os.path.exists(filepath):
            os.remove(filepath)
    except OSError as e:
        log.warning("Could not remove temp file '%s': %s", filepath, e)


# error handlers
@app.errorhandler(400)
def bad_request(e):
    return _err("Bad request , the server could not understand your submission.", 400, str(e))


@app.errorhandler(404)
def not_found(e):
    return _err("Endpoint not found. Check the URL and try again.", 404)


@app.errorhandler(405)
def method_not_allowed(e):
    allowed = ", ".join(e.valid_methods or [])
    return _err(f"Method not allowed. This endpoint accepts: {allowed}.", 405)


@app.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    return _err(
        f"File too large. Maximum allowed size is {MAX_FILE_SIZE_MB} MB.", 413
    )


@app.errorhandler(500)
def internal_error(e):
    log.error("Unhandled 500: %s\n%s", e, traceback.format_exc())
    return _err(
        "An unexpected server error occurred. Check legalaudit.log for details.", 500
    )


@app.errorhandler(Exception)
def unhandled_exception(e):
    log.error("Unhandled exception: %s\n%s", e, traceback.format_exc())
    return _err(
        "An unexpected error occurred. The server team has been notified.", 500, str(e)
    )


# routes
@app.route("/")
def index():
    try:
        return render_template("index.html")
    except Exception as e:
        log.error("Failed to render index.html: %s", e)
        return _err("Could not load the application page.", 500, str(e))


@app.route("/analyse", methods=["POST"])
def analyse_document():
    request_id = uuid.uuid4().hex[:8]
    log.info("[%s] /analyse , content-type=%s", request_id, request.content_type)

    filepath = None  # tracked so we can always clean it up
    body = None      # holds the JSON body if this was a text submission

    try:

        # reject requests that try to send both a file and a JSON body
        if "file" in request.files and request.is_json:
            return _err("Send either a file or JSON text, not both.")

        if request.is_json:
            try:
                body = request.get_json(silent=False)
            except Exception as e:
                return _err(
                    "Invalid JSON body. Please send valid JSON.",
                    400,
                    str(e)
                )

            if not isinstance(body, dict):
                return _err("JSON body must be an object, not a list or primitive.")

        # Branch: file upload
        if "file" in request.files:
            # Validate doc_type for file upload
            raw_doc_type = request.form.get("doc_type")
            doc_type = _safe_doc_type(raw_doc_type)

            if doc_type is None:
                return _err(
                    "Invalid document type. Must be 'employment' or 'tenancy'."
                )

            log.info("[%s] doc_type=%s", request_id, doc_type)
            file = request.files["file"]

            if not file or not file.filename:
                return _err("No file selected. Please choose a file to upload.")

            if not _allowed_file(file.filename):
                ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "(none)"
                return _err(
                    f"Unsupported file type '.{ext}'. "
                    f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}."
                )

            safe_name = secure_filename(file.filename)
            if not safe_name:
                return _err(
                    "The filename contains only special characters and cannot be made safe. "
                    "Please rename your file and try again."
                )

            filename = f"{uuid.uuid4().hex}_{safe_name}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

            try:
                file.save(filepath)
                log.info("[%s] Saved upload: %s", request_id, filename)
            except OSError as e:
                _cleanup(filepath)
                log.error("[%s] Could not save uploaded file: %s", request_id, e)
                return _err(
                    "Could not save the uploaded file. "
                    "The server may be out of disk space or permissions are incorrect.",
                    500, str(e)
                )

            # Validate file is not empty
            try:
                size = os.path.getsize(filepath)
                if size == 0:
                    _cleanup(filepath)
                    return _err("The uploaded file is empty (0 bytes). Please upload a valid document.")
                log.info("[%s] File size: %s bytes", request_id, f"{size:,}")
            except OSError as e:
                _cleanup(filepath)
                return _err("Could not verify the uploaded file.", 500, str(e))
            try:
                ocr_result = extract_text(filepath)
            except Exception as e:
                log.error("[%s] Crash in extract_text: %s\n%s",
                          request_id, e, traceback.format_exc())
                _cleanup(filepath)
                filepath = None
                return _err("Text extraction crashed unexpectedly.", 500, str(e))
            finally:
                _cleanup(filepath)
                filepath = None
            if not isinstance(ocr_result, dict):
                return _err("Text extraction returned an invalid internal response.", 500)

            if ocr_result.get("error"):
                return _err(
                    f"Could not extract text from your file: {ocr_result['error']}",
                    422
                )

            text = ocr_result.get("text", "")
            if not isinstance(text, str):
                return _err("Extracted text is not a valid string , internal error.", 500)

            extraction_info = {
            "method": ocr_result.get("method", "unknown"),
            "pages": ocr_result.get("pages", 0),
            "characters_extracted": len(text)
            }
        # Branch: JSON text
        elif body is not None:
            text = body.get("text")

            if text is None:
                return _err(
                    "JSON body must include a 'text' field with the contract text."
                )
            if not isinstance(text, str):
                return _err("The 'text' field must be a string.")
            if len(text) > MAX_TEXT_LENGTH:
                return _err(
                    f"Pasted text is too long ({len(text):,} characters). "
                    f"Maximum is {MAX_TEXT_LENGTH:,} characters."
                )

            raw_doc_type = body.get("doc_type")
            doc_type = _safe_doc_type(raw_doc_type)

            if doc_type is None:
                return _err(
                    "Invalid document type. Must be 'employment' or 'tenancy'."
                )

            log.info("[%s] doc_type=%s", request_id, doc_type)

            extraction_info = {
                "method": "Plain text (pasted)",
                "pages": 1,
                "characters_extracted": len(text)
            }

        # No input
        else:
            return _err(
                "No input provided. Either upload a file or send JSON with 'text'."
            )

        # Common validation
        stripped = text.strip()
        if len(stripped) < MIN_TEXT_LENGTH:
            return _err(
                f"The document text is too short ({len(stripped)} characters)."
            )

        # Inference
        if not doc_type:
            return _err("Document type could not be determined.", 400)
        report = analyse(text, doc_type)

        if not isinstance(report, dict):
            return _err("The analysis engine returned an invalid response.", 500)

        if report.get("error"):
            return _err(report["error"], 422)

        for key in ("summary", "findings"):
            if key not in report:
                return _err(f"Analysis report is missing '{key}'.", 500)

        log.info("[%s] Analysis done , %d findings", request_id, len(report.get("findings", [])))

        return jsonify({
            "extraction_info": extraction_info,
            "summary":         report["summary"],
            "findings":        report["findings"],
            "passed_rules":    report.get("passed_rules", []),
            "doc_type":        doc_type
        })

    except Exception as e:
        _cleanup(filepath)
        log.error("[%s] Unhandled error: %s\n%s",
                  request_id, e, traceback.format_exc())
        return _err(
            "An unexpected error occurred while processing your document.",
            500, str(e)
        )


@app.route("/download-report", methods=["POST"])
def download_report():
    request_id = uuid.uuid4().hex[:8]
    log.info("[%s] /download-report", request_id)

    try:
        if not request.is_json:
            return _err(
                "This endpoint requires Content-Type: application/json."
            )

        try:
            data = request.get_json(silent=False)
        except Exception as e:
            return _err("Could not parse JSON body.", 400, str(e))

        if not data:
            return _err("Request body is empty. Provide the report JSON data.")
        if not isinstance(data, dict):
            return _err("Report data must be a JSON object.")

        missing = [k for k in ("summary", "findings") if k not in data]
        if missing:
            return _err(
                f"Report data is missing required fields: {', '.join(missing)}."
            )

        if not isinstance(data.get("findings"), list):
            return _err("'findings' must be a list.")
        if not isinstance(data.get("summary"), dict):
            return _err("'summary' must be an object.")

        try:
            pdf_bytes = generate_pdf_report(data)
        except Exception as e:
            log.error("[%s] PDF generation failed: %s\n%s",
                      request_id, e, traceback.format_exc())
            return _err(
                "PDF generation failed. "
                "The report data may be malformed or a rendering error occurred.",
                500, str(e)
            )

        if not pdf_bytes or len(pdf_bytes) == 0:
            return _err("PDF generation produced an empty file.", 500)

        doc_type = data.get("doc_type", "employment")
        label    = "employment" if doc_type == "employment" else "tenancy"
        filename = f"legalaudit_{label}_report.pdf"

        log.info("[%s] PDF ready , %s bytes , %s", request_id, f"{len(pdf_bytes):,}", filename)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        log.error("[%s] Unhandled error in /download-report: %s\n%s",
                  request_id, e, traceback.format_exc())
        return _err(
            "An unexpected error occurred while generating the PDF report.",
            500, str(e)
        )


# health check
@app.route("/health")
def health():
    """Simple liveness check , useful for monitoring and load balancers."""
    return jsonify({
        "status":    "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "app": "LegalAudit"
    })


# entry point
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  LegalAudit , Malaysian Contract Auditor")
    print("  Running at:    http://localhost:5000")
    print("  Health check:  http://localhost:5000/health")
    print("  Log file:      legalaudit.log")
    print("=" * 60 + "\n")
    app.run(debug=True, port=5000)
