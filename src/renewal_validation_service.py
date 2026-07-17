"""
Renewal validation engine.

Performs automated checks after each document upload:
- missing required documents
- duplicate documents that cover the same requirement
- conflicting duplicates that replace missing required documents
- image/legibility quality warnings
- document type classification

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from PIL import Image

from .renewal_models import (
    DocumentRequirement,
    RenewalSolicitud,
    RenewalValidationResult,
    SolicitudStatus,
    UploadedDocument,
    ValidationIssue,
)
from .renewal_catalog import get_catalog
from .processor import MedicalDocumentProcessor

logger = logging.getLogger(__name__)


class RenewalValidationService:
    """Validates renewal requests after document upload/processing."""

    def __init__(
        self,
        processor: Optional[MedicalDocumentProcessor] = None,
        min_quality_threshold: int = 40,
    ):
        self.processor = processor or MedicalDocumentProcessor(use_ocr=True, mock_mode=True)
        self.min_quality_threshold = min_quality_threshold

    def process_and_validate(
        self, solicitud: RenewalSolicitud
    ) -> RenewalValidationResult:
        """Run classification on unprocessed documents and validate the request."""
        # Process any documents that have not been analysed yet.
        for doc in solicitud.documents:
            if doc.processing_result is not None:
                continue
            try:
                result = self.processor.process_document(Path(doc.stored_path))
                doc.processing_result = result
                detected_type = result.tipo_documento
                expected_type = self._expected_type_for(doc.requirement_id)
                if expected_type and detected_type != expected_type:
                    doc.classification_warning = (
                        f"El documento se clasificó como '{detected_type}' "
                        f"pero el requerimiento espera '{expected_type}'."
                    )
            except Exception as exc:
                logger.exception("Failed to process document %s", doc.document_id)
                doc.quality_warnings.append(f"No se pudo analizar el documento: {exc}")

        return self.validate(solicitud)

    def validate(self, solicitud: RenewalSolicitud) -> RenewalValidationResult:
        """Validate the renewal request against its document catalog."""
        catalog = get_catalog(solicitud.procedure_code)
        requirements_by_id = {req.requirement_id: req for req in catalog.requirements}

        missing: List[str] = []
        issues: List[ValidationIssue] = []
        duplicate_issues: List[Dict] = []
        conflicting_duplicates: List[Dict] = []
        quality_warnings: List[Dict] = []

        docs_by_requirement: Dict[str, List[UploadedDocument]] = defaultdict(list)
        for doc in solicitud.documents:
            docs_by_requirement[doc.requirement_id or "__unknown__"].append(doc)

        # Check each requirement: missing docs, duplicates, quality, classification.
        for req in catalog.requirements:
            req_docs = docs_by_requirement.get(req.requirement_id, [])

            if not req_docs and req.is_mandatory:
                missing.append(req.requirement_id)
                issues.append(
                    ValidationIssue(
                        issue_type="missing",
                        requirement_id=req.requirement_id,
                        message=f"Falta cargar el documento obligatorio: {req.name}.",
                        blocks_submission=True,
                    )
                )
                continue

            # Excess of identical/non-distinct documents.
            if len(req_docs) > req.max_documents:
                if req.allow_multiple_distinct and req.expected_document_type == "laboratorio":
                    distinct_types = self._distinct_study_types(req_docs)
                    if len(distinct_types) < len(req_docs):
                        duplicate_issues.extend(self._build_duplicate_entries(req_docs, req))
                        issues.extend(
                            self._duplicate_issues(req_docs, req, blocks_submission=True)
                        )
                else:
                    duplicate_issues.extend(self._build_duplicate_entries(req_docs, req))
                    issues.extend(
                        self._duplicate_issues(req_docs, req, blocks_submission=True)
                    )

            # Quality warnings per document.
            for doc in req_docs:
                quality_score = self._quality_score(doc)
                if quality_score < req.min_quality_score:
                    quality_warnings.append(
                        {
                            "document_id": doc.document_id,
                            "requirement_id": req.requirement_id,
                            "quality_score": quality_score,
                            "message": (
                                f"La calidad del documento '{req.name}' es baja "
                                f"(score {quality_score}/100). Podría afectar su legibilidad."
                            ),
                        }
                    )
                    issues.append(
                        ValidationIssue(
                            issue_type="quality",
                            requirement_id=req.requirement_id,
                            document_id=doc.document_id,
                            message=(
                                f"Advertencia de calidad en {req.name}: "
                                f"score {quality_score}/100."
                            ),
                            blocks_submission=False,
                        )
                    )

                # Classification confidence / mismatch.
                if doc.classification_warning:
                    quality_warnings.append(
                        {
                            "document_id": doc.document_id,
                            "requirement_id": req.requirement_id,
                            "message": doc.classification_warning,
                        }
                    )
                    issues.append(
                        ValidationIssue(
                            issue_type="classification",
                            requirement_id=req.requirement_id,
                            document_id=doc.document_id,
                            message=doc.classification_warning,
                            blocks_submission=False,
                        )
                    )

        # Conflicting duplicate detection:
        # When multiple documents of the same expected type exist and a different
        # mandatory requirement is still missing.
        conflicting_duplicates = self._detect_conflicting_duplicates(
            solicitud, catalog, requirements_by_id
        )
        for dup in conflicting_duplicates:
            issues.append(
                ValidationIssue(
                    issue_type="conflicting_duplicate",
                    requirement_id=dup.get("missing_requirement_id"),
                    document_id=dup.get("document_id"),
                    message=dup.get("message", ""),
                    blocks_submission=True,
                )
            )

        # Build messages list.
        messages = [issue.message for issue in issues]

        # Determine whether submission is allowed.
        has_blocking_issue = any(issue.blocks_submission for issue in issues)
        can_submit = not has_blocking_issue

        # Compute request status.
        if can_submit:
            status = SolicitudStatus.LISTA_PARA_ENVIO
        elif any(issue.issue_type == "quality" for issue in issues) and not any(
            issue.issue_type in {"missing", "conflicting_duplicate", "duplicate"}
            for issue in issues
        ):
            status = SolicitudStatus.DOCS_WARNING_CALIDAD
        elif missing or conflicting_duplicates:
            status = SolicitudStatus.DOCS_INCOMPLETAS
        else:
            status = SolicitudStatus.DOCS_INCOMPLETAS

        solicitud.status = status
        return RenewalValidationResult(
            solicitud_id=solicitud.solicitud_id,
            status=status,
            can_submit=can_submit,
            issues=issues,
            missing_requirements=missing,
            duplicate_issues=duplicate_issues,
            conflicting_duplicates=conflicting_duplicates,
            quality_warnings=quality_warnings,
            messages=messages,
            documents=solicitud.documents,
        )

    def _expected_type_for(self, requirement_id: Optional[str]) -> Optional[str]:
        try:
            catalog = get_catalog("RENOVACION_DIABETES")
            for req in catalog.requirements:
                if req.requirement_id == requirement_id:
                    return req.expected_document_type
        except Exception:
            pass
        return None

    @staticmethod
    def _distinct_study_types(docs: List[UploadedDocument]) -> set:
        """Return the set of distinct extracted study types in uploaded docs."""
        study_types = set()
        for doc in docs:
            study_type = doc.extracted_study_type
            if study_type:
                study_types.add(study_type.lower())
            elif doc.processing_result:
                study_types.add(doc.processing_result.tipo_documento.lower())
        return study_types

    @staticmethod
    def _build_duplicate_entries(
        docs: List[UploadedDocument], req: DocumentRequirement
    ) -> List[Dict]:
        entries: List[Dict] = []
        seen: set = set()
        for doc in docs:
            key = doc.extracted_study_type or doc.processing_result.tipo_documento if doc.processing_result else doc.document_id
            if key in seen:
                entries.append(
                    {
                        "document_id": doc.document_id,
                        "requirement_id": req.requirement_id,
                        "key": key,
                        "message": f"Documento duplicado detectado para {req.name}.",
                    }
                )
            else:
                seen.add(key)
        return entries

    @staticmethod
    def _duplicate_issues(
        docs: List[UploadedDocument], req: DocumentRequirement, blocks_submission: bool
    ) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        seen: set = set()
        for doc in docs:
            key = doc.extracted_study_type or doc.processing_result.tipo_documento if doc.processing_result else doc.document_id
            if key in seen:
                issues.append(
                    ValidationIssue(
                        issue_type="duplicate",
                        requirement_id=req.requirement_id,
                        document_id=doc.document_id,
                        message=f"Documento duplicado en {req.name}.",
                        blocks_submission=blocks_submission,
                    )
                )
            else:
                seen.add(key)
        return issues

    def _detect_conflicting_duplicates(
        self,
        solicitud: RenewalSolicitud,
        catalog,
        requirements_by_id: Dict[str, DocumentRequirement],
    ) -> List[Dict]:
        """
        Detect when non-distinct duplicates cover a requirement while another
        mandatory requirement remains empty.
        """
        missing_req_ids = {
            req.requirement_id
            for req in catalog.requirements
            if req.is_mandatory and not any(
                doc.requirement_id == req.requirement_id for doc in solicitud.documents
            )
        }

        conflicting: List[Dict] = []
        for doc in solicitud.documents:
            req = requirements_by_id.get(doc.requirement_id)
            if not req or not req.allow_multiple_distinct:
                continue
            if doc.processing_result is None:
                continue

            detected_type = doc.processing_result.tipo_documento
            for missing_id in missing_req_ids:
                missing_req = requirements_by_id.get(missing_id)
                if missing_req and missing_req.expected_document_type == detected_type:
                    # The uploaded doc matches the type of a missing requirement.
                    same_type_uploaded = [
                        d
                        for d in solicitud.documents
                        if d.processing_result
                        and d.processing_result.tipo_documento == detected_type
                    ]
                    if len(same_type_uploaded) >= 2:
                        conflicting.append(
                            {
                                "document_id": doc.document_id,
                                "requirement_id": req.requirement_id,
                                "missing_requirement_id": missing_id,
                                "message": (
                                    f"El documento cargado como '{req.name}' "
                                    f"corresponde a '{missing_req.name}', que aún no fue cargada. "
                                    f"Corregí la asignación o cargá el documento faltante."
                                ),
                            }
                        )
        return conflicting

    def _quality_score(self, doc: UploadedDocument) -> int:
        """
        Compute a simple legibility/quality score from the processing result
        or from a basic image dimension check.
        """
        if doc.processing_result is not None:
            return doc.processing_result.confianza_clasificacion

        try:
            image = Image.open(doc.stored_path)
            width, height = image.size
            if width < 300 or height < 300:
                return 20
            if width < 600 or height < 600:
                return 50
            return 80
        except Exception:
            return 0
