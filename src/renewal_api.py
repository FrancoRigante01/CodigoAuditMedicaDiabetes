"""
Renewal API endpoints (Flask-compatible).

Provides immediate upload + validation feedback for affiliates,
and submission control (allow quality warnings, block missing/duplicates).

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from flask import Blueprint, Response, current_app, jsonify, request

from .renewal_catalog import get_catalog
from .renewal_models import RenewalSolicitud, SolicitudStatus, UploadedDocument
from .renewal_upload_service import RenewalUploadService
from .renewal_validation_service import RenewalValidationService
from .processor import MedicalDocumentProcessor

logger = logging.getLogger(__name__)

renewal_bp = Blueprint("renewal_bp", __name__, url_prefix="/api/renovacion")

# In-memory registry for demo purposes. In production use a persistent store.
SOLICITUDES: Dict[str, RenewalSolicitud] = {}

_upload_service: RenewalUploadService = None  # type: ignore
_validation_service: RenewalValidationService = None  # type: ignore


def _get_upload_service() -> RenewalUploadService:
    """Lazy-initialize the upload service using Flask app config."""
    global _upload_service
    if _upload_service is None:
        base_path = current_app.config.get("RENEWAL_UPLOAD_PATH", "uploads/renewal")
        _upload_service = RenewalUploadService(base_storage_path=base_path)
    return _upload_service


def _get_validation_service() -> RenewalValidationService:
    """Lazy-initialize the validation service reusing the app processor."""
    global _validation_service
    if _validation_service is None:
        processor = current_app.config.get("DOCUMENT_PROCESSOR")
        if processor is None:
            processor = MedicalDocumentProcessor(use_ocr=True, mock_mode=True)
        _validation_service = RenewalValidationService(processor=processor)
    return _validation_service


@renewal_bp.route("/solicitudes", methods=["POST"])
def create_solicitud():
    """Create a new renewal request (BORRADOR)."""
    data = request.get_json(silent=True) or {}
    affiliate_id = data.get("affiliate_id")
    service = _get_upload_service()
    solicitud = service.create_solicitud(affiliate_id=affiliate_id)
    SOLICITUDES[solicitud.solicitud_id] = solicitud
    return jsonify(solicitud_model=solicitud.model_dump(mode="json")), 201


@renewal_bp.route("/solicitudes/<solicitud_id>/documentos", methods=["POST"])
def upload_document(solicitud_id: str):
    """Receive a document for a given requirement and validate immediately."""
    solicitud = SOLICITUDES.get(solicitud_id)
    if not solicitud:
        return _error_response("Solicitud no encontrada.", 404)

    if "document" not in request.files:
        return _error_response("No se encontró el archivo en la solicitud.", 400)

    upload_file = request.files["document"]
    if upload_file.filename == "":
        return _error_response("No se seleccionó ningún archivo.", 400)

    if not _get_upload_service().allowed_file(upload_file.filename):
        return _error_response("Formato no permitido. Usar PDF, PNG, JPG o JPEG.", 400)

    requirement_id = request.form.get("requirement_id", request.args.get("requirement_id"))
    if not requirement_id:
        # Try to infer from document classification after upload.
        requirement_id = "__por_clasificar__"

    service = _get_upload_service()
    try:
        document = service.store_document(solicitud, requirement_id, upload_file)
    except Exception as exc:
        logger.exception("Failed to store document")
        return _error_response(f"Error al guardar el documento: {exc}", 500)

    # Run validation immediately after upload to notify the affiliate.
    validation_result = _get_validation_service().process_and_validate(solicitud)
    _reconcile_unknown_requirement(solicitud, document, validation_result)

    return jsonify(
        document=document.model_dump(mode="json"),
        validation=validation_result.model_dump(mode="json"),
    ), 200


@renewal_bp.route("/solicitudes/<solicitud_id>/validar", methods=["GET"])
def validate_solicitud(solicitud_id: str):
    """Return immediate validation result for a request."""
    solicitud = SOLICITUDES.get(solicitud_id)
    if not solicitud:
        return _error_response("Solicitud no encontrada.", 404)

    validation_result = _get_validation_service().process_and_validate(solicitud)
    return jsonify(validation_result.model_dump(mode="json")), 200


@renewal_bp.route("/solicitudes/<solicitud_id>/enviar", methods=["POST"])
def submit_solicitud(solicitud_id: str):
    """Submit the request only if there are no blocking issues."""
    solicitud = SOLICITUDES.get(solicitud_id)
    if not solicitud:
        return _error_response("Solicitud no encontrada.", 404)

    if solicitud.status == SolicitudStatus.EN_AUDITORIA:
        return _error_response("La solicitud ya fue enviada a auditoría.", 409)

    validation_result = _get_validation_service().process_and_validate(solicitud)
    if not validation_result.can_submit:
        return jsonify(
            success=False,
            reason="La solicitud tiene problemas que impiden el envío.",
            validation=validation_result.model_dump(mode="json"),
        ), 422

    service = _get_upload_service()
    service.mark_submitted(solicitud, validation_result)
    solicitud.status = SolicitudStatus.EN_AUDITORIA
    solicitud.updated_at = datetime.utcnow()

    return jsonify(
        success=True,
        message="Solicitud enviada correctamente.",
        validation=validation_result.model_dump(mode="json"),
    ), 200


@renewal_bp.route("/solicitudes/<solicitud_id>/documentos/<document_id>", methods=["DELETE"])
def delete_document(solicitud_id: str, document_id: str):
    """Remove a document from the request and re-validate."""
    solicitud = SOLICITUDES.get(solicitud_id)
    if not solicitud:
        return _error_response("Solicitud no encontrada.", 404)

    service = _get_upload_service()
    removed = service.remove_document(solicitud, document_id)
    if not removed:
        return _error_response("Documento no encontrado.", 404)

    validation_result = _get_validation_service().process_and_validate(solicitud)
    return jsonify(validation=validation_result.model_dump(mode="json")), 200


@renewal_bp.route("/catalogo/<procedure_code>", methods=["GET"])
def get_procedure_catalog(procedure_code: str):
    """Return the document catalog for a renewal procedure."""
    try:
        catalog = get_catalog(procedure_code)
        return jsonify(catalog.model_dump(mode="json")), 200
    except ValueError as exc:
        return _error_response(str(exc), 404)


def _error_response(message: str, status_code: int) -> Response:
    response = jsonify(success=False, error=message)
    response.status_code = status_code
    return response


def _reconcile_unknown_requirement(
    solicitud: RenewalSolicitud,
    document: UploadedDocument,
    validation_result,
) -> None:
    """
    When a document is uploaded without an explicit requirement (or with a
    placeholder), assign it to the most likely catalog requirement based on its
    classified type. This preserves validation integrity.
    """
    if document.requirement_id != "__por_clasificar__":
        return

    catalog = get_catalog(solicitud.procedure_code)
    type_to_req = {req.expected_document_type: req.requirement_id for req in catalog.requirements}

    detected_type = None
    if document.processing_result:
        detected_type = document.processing_result.tipo_documento

    if detected_type and detected_type in type_to_req:
        document.requirement_id = type_to_req[detected_type]
    elif validation_result.missing_requirements:
        # Assign to the first missing mandatory requirement as a best guess.
        document.requirement_id = validation_result.missing_requirements[0]
    else:
        document.requirement_id = catalog.requirements[0].requirement_id

    # Update validation to account for the reconciled requirement.
    updated = _get_validation_service().process_and_validate(solicitud)
    validation_result.status = updated.status
    validation_result.can_submit = updated.can_submit
    validation_result.issues = updated.issues
    validation_result.missing_requirements = updated.missing_requirements
    validation_result.duplicate_issues = updated.duplicate_issues
    validation_result.conflicting_duplicates = updated.conflicting_duplicates
    validation_result.quality_warnings = updated.quality_warnings
    validation_result.messages = updated.messages
    validation_result.documents = updated.documents


def register_renewal_blueprint(app):
    """Register the renewal blueprint on a Flask app."""
    app.register_blueprint(renewal_bp)
