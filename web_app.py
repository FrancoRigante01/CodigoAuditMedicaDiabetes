"""Simple web interface for the medical document audit demo.

Allows the user to select/upload a document (PDF or image), runs the audit
pipeline, and displays the resulting JSON below.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT upload or process real patient data.
"""

import json
import os
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template, request, flash

# Load environment variables from .env file
load_dotenv()

from src.processor import MedicalDocumentProcessor
from src.renewal_api import register_renewal_blueprint

app = Flask(__name__)
app.secret_key = "demo-inseguro-cambiar-en-produccion"

# Register renewal endpoints for immediate validation and submission control.
register_renewal_blueprint(app)

# Configure upload settings
UPLOAD_FOLDER = Path(tempfile.gettempdir()) / "doc_audit_uploads"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

# Initialize processor: use FRIDA for both extraction and auditing
processor = MedicalDocumentProcessor(use_ocr=True, mock_mode=False)
app.config["DOCUMENT_PROCESSOR"] = processor


def allowed_file(filename: str) -> bool:
    """Check whether the uploaded file has an allowed extension."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@app.route("/", methods=["GET", "POST"])
def index():
    result_json = None
    filename = None
    error = None

    if request.method == "POST":
        if "document" not in request.files:
            flash("No se seleccionó ningún archivo", "error")
            return render_template("index.html")

        uploaded_file = request.files["document"]
        if uploaded_file.filename == "":
            flash("No se seleccionó ningún archivo", "error")
            return render_template("index.html")

        if not allowed_file(uploaded_file.filename):
            flash(
                "Formato no permitido. Subir PDF, PNG, JPG o JPEG.",
                "error"
            )
            return render_template("index.html")

        # Save uploaded file with a unique name
        ext = Path(uploaded_file.filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = UPLOAD_FOLDER / unique_name
        uploaded_file.save(save_path)
        filename = uploaded_file.filename

        try:
            result = processor.process_document(save_path)
            result_json = json.dumps(
                result.model_dump(),
                indent=2,
                ensure_ascii=False
            )
        except Exception as exc:
            error = str(exc)
            app.logger.exception("Error al procesar el documento")
        finally:
            # Remove temporary file
            try:
                os.remove(save_path)
            except OSError:
                pass

    return render_template(
        "index.html",
        result_json=result_json,
        filename=filename,
        error=error
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
