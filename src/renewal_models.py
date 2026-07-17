"""
Data models for the renewal documents upload and validation flow.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .models import DocumentProcessingResult


class SolicitudStatus(str, Enum):
    BORRADOR = "BORRADOR"
    DOCS_EN_CARGA = "DOCS_EN_CARGA"
    DOCS_INCOMPLETAS = "DOCS_INCOMPLETAS"
    DOCS_WARNING_CALIDAD = "DOCS_WARNING_CALIDAD"
    LISTA_PARA_ENVIO = "LISTA_PARA_ENVIO"
    EN_AUDITORIA = "EN_AUDITORIA"


class DocumentRequirement(BaseModel):
    """Configuration for a document requirement within a renewal procedure."""

    requirement_id: str = Field(..., description="Unique identifier for the requirement")
    expected_document_type: str = Field(..., description="Expected document type")
    name: str = Field(..., description="Human readable name")
    description: str = Field(default="", description="Description shown to the affiliate")
    is_mandatory: bool = Field(default=True, description="Whether the requirement is mandatory")
    max_documents: int = Field(default=1, ge=1, description="Maximum documents allowed for this requirement")
    allow_multiple_distinct: bool = Field(
        default=False,
        description="Whether multiple documents are allowed when they represent distinct studies"
    )
    min_quality_score: int = Field(default=40, ge=0, le=100, description="Minimum acceptable legibility/clarity score")
    min_classification_confidence: int = Field(default=50, ge=0, le=100, description="Minimum classification confidence")


class UploadedDocument(BaseModel):
    """Represents a document uploaded by the affiliate."""

    document_id: str = Field(..., description="Unique identifier for the uploaded document")
    requirement_id: Optional[str] = Field(default=None, description="Requirement this document was uploaded for")
    filename: str = Field(..., description="Original filename")
    stored_path: str = Field(..., description="Path where the file is stored")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    processing_result: Optional[DocumentProcessingResult] = Field(
        default=None,
        description="Result from the existing document processing pipeline"
    )
    quality_warnings: List[str] = Field(default_factory=list)
    classification_warning: Optional[str] = Field(default=None, description="Warning if detected type differs from expected")
    extracted_study_type: Optional[str] = Field(default=None, description="Specific study type, used for distinct labs")


class RenewalSolicitud(BaseModel):
    """Represents a renewal request with its uploaded documents."""

    solicitud_id: str = Field(..., description="Unique identifier for the renewal request")
    affiliate_id: Optional[str] = Field(default=None, description="Identifier of the affiliate")
    procedure_code: str = Field(default="RENOVACION_DIABETES")
    status: SolicitudStatus = Field(default=SolicitudStatus.BORRADOR)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default=None)
    submitted_at: Optional[datetime] = Field(default=None)
    documents: List[UploadedDocument] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """A single validation issue detected for a renewal request."""

    issue_type: str = Field(..., description="missing, duplicate, conflicting_duplicate, quality, classification")
    requirement_id: Optional[str] = Field(default=None)
    document_id: Optional[str] = Field(default=None)
    message: str = Field(..., description="Human readable message")
    blocks_submission: bool = Field(default=False)


class RenewalValidationResult(BaseModel):
    """Result of validating a renewal request."""

    solicitud_id: str
    status: SolicitudStatus
    can_submit: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    missing_requirements: List[str] = Field(default_factory=list)
    duplicate_issues: List[Dict] = Field(default_factory=list)
    conflicting_duplicates: List[Dict] = Field(default_factory=list)
    quality_warnings: List[Dict] = Field(default_factory=list)
    messages: List[str] = Field(default_factory=list)
    documents: List[UploadedDocument] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "solicitud_id": "sol-123",
                "status": "DOCS_INCOMPLETAS",
                "can_submit": False,
                "issues": [
                    {
                        "issue_type": "missing",
                        "requirement_id": "PRESCRIPCION_MEDICA",
                        "message": "Falta cargar la prescripción médica."
                    }
                ],
                "messages": ["Falta cargar la prescripción médica."]
            }
        }


class RenewalCatalog(BaseModel):
    """Catalog of required documents for a renewal procedure."""

    procedure_code: str
    name: str
    requirements: List[DocumentRequirement]
