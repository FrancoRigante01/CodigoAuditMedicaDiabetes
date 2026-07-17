"""
Service for receiving, storing, and tracking renewal documents.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from werkzeug.datastructures import FileStorage

from .renewal_models import RenewalSolicitud, SolicitudStatus, UploadedDocument, RenewalValidationResult


def _generate_id(prefix: str = "id") -> str:
    """Generate a short unique identifier."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


class RenewalUploadService:
    """Handles file reception and storage for renewal requests."""

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg"}

    def __init__(self, base_storage_path: str = "uploads"):
        self.base_storage_path = Path(base_storage_path)
        self.base_storage_path.mkdir(parents=True, exist_ok=True)

    def create_solicitud(self, affiliate_id: Optional[str] = None) -> RenewalSolicitud:
        """Create a new renewal request in BORRADOR state."""
        solicitud = RenewalSolicitud(
            solicitud_id=_generate_id("sol"),
            affiliate_id=affiliate_id,
            procedure_code="RENOVACION_DIABETES",
            status=SolicitudStatus.BORRADOR,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self._ensure_solicitud_dir(solicitud.solicitud_id)
        return solicitud

    def _ensure_solicitud_dir(self, solicitud_id: str) -> Path:
        solicitud_dir = self.base_storage_path / solicitud_id
        solicitud_dir.mkdir(parents=True, exist_ok=True)
        return solicitud_dir

    def allowed_file(self, filename: str) -> bool:
        """Check whether the file extension is allowed."""
        return Path(filename).suffix.lower() in self.ALLOWED_EXTENSIONS

    def store_document(
        self,
        solicitud: RenewalSolicitud,
        requirement_id: str,
        upload_file: FileStorage,
    ) -> UploadedDocument:
        """Store an uploaded file and return its metadata."""
        document_id = _generate_id("doc")
        solicitud_dir = self._ensure_solicitud_dir(solicitud.solicitud_id)

        extension = Path(upload_file.filename or "document.bin").suffix.lower()
        stored_filename = f"{document_id}{extension}"
        stored_path = solicitud_dir / stored_filename

        with stored_path.open("wb") as buffer:
            shutil.copyfileobj(upload_file.stream, buffer)

        document = UploadedDocument(
            document_id=document_id,
            requirement_id=requirement_id,
            filename=upload_file.filename or "document.bin",
            stored_path=str(stored_path),
            uploaded_at=datetime.utcnow(),
        )

        solicitud.documents.append(document)
        solicitud.status = SolicitudStatus.DOCS_EN_CARGA
        solicitud.updated_at = datetime.utcnow()
        return document

    def remove_document(self, solicitud: RenewalSolicitud, document_id: str) -> bool:
        """Remove a document from storage and from the request."""
        for index, doc in enumerate(solicitud.documents):
            if doc.document_id == document_id:
                try:
                    os.remove(doc.stored_path)
                except FileNotFoundError:
                    pass
                solicitud.documents.pop(index)
                solicitud.updated_at = datetime.utcnow()
                return True
        return False

    def mark_submitted(
        self,
        solicitud: RenewalSolicitud,
        validation_result: RenewalValidationResult,
    ) -> None:
        """Mark the request as submitted only if validation allows it.

        This is the gatekeeper that prevents incomplete or invalid requests from
        reaching the auditing instance. Any caller must provide a current
        ``RenewalValidationResult`` and the result must have ``can_submit=True``.
        """
        if not validation_result.can_submit:
            raise ValueError(
                "No se puede enviar la solicitud: existen problemas de "
                "documentación que bloquean el envío."
            )
        if solicitud.submitted_at is None:
            solicitud.submitted_at = datetime.utcnow()
        solicitud.updated_at = datetime.utcnow()
        # The status change to EN_AUDITORIA is intentionally kept outside this
        # service (the API layer sets it after a successful call). This method
        # only records the submission timestamp, forcing every transition path
        # to validate the request first.
