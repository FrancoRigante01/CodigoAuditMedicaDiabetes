"""
Data structures and models for medical document processing.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """Represents an extracted field with its value and confidence score."""
    valor: str = Field(..., description="The extracted value")
    confianza: int = Field(..., ge=0, le=100, description="Confidence score 0-100")


class DocumentProcessingResult(BaseModel):
    """Main output structure for processed documents."""
    tipo_documento: str = Field(
        ..., 
        description="Classified document type: formulario_diabetes, laboratorio, estudio_diagnostico, prescripcion"
    )
    confianza_clasificacion: int = Field(
        ..., 
        ge=0, 
        le=100,
        description="Classification confidence score"
    )
    campos_extraidos: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Extracted fields with individual confidence scores"
    )
    faltantes_o_inconsistencias: List[str] = Field(
        default_factory=list,
        description="List of missing required fields or detected inconsistencies"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tipo_documento": "formulario_diabetes",
                "confianza_clasificacion": 85,
                "campos_extraidos": {
                    "diagnostico": {"valor": "Diabetes tipo 2", "confianza": 90},
                    "medicacion_solicitada": {"valor": "Metformina 500mg", "confianza": 85}
                },
                "faltantes_o_inconsistencias": ["Firma del médico ilegible"]
            }
        }


# Document type constants
DOCUMENT_TYPES = {
    "formulario_diabetes": {
        "name": "Formulario Diabetes",
        "required_fields": [
            "diagnostico",
            "tipo_diabetes",
            "medicacion_solicitada",
            "fecha_firma",
            "datos_medico_tratante"
        ],
        "optional_fields": [
            "insumo_solicitado",
            "notas_medico"
        ]
    },
    "laboratorio": {
        "name": "Estudio de Laboratorio",
        "required_fields": [
            "tipo_estudio",
            "fecha_estudio",
            "valores_relevantes"
        ],
        "optional_fields": [
            "laboratorio_nombre",
            "medico_solicitante"
        ]
    },
    "prescripcion": {
        "name": "Prescripción Médica",
        "required_fields": [
            "medicacion_insumo",
            "dosis",
            "vigencia_receta",
            "matricula_prescriptor"
        ],
        "optional_fields": [
            "nombre_prescriptor",
            "indicaciones"
        ]
    },
    "estudio_diagnostico": {
        "name": "Estudio Diagnóstico",
        "required_fields": [
            "tipo_informe",
            "fecha_informe",
            "conclusion_relevante"
        ],
        "optional_fields": [
            "medico_responsable",
            "modalidad_estudio"
        ]
    }
}


class ProcessingError(Exception):
    """Custom exception for document processing errors."""
    pass


class DocumentQualityWarning:
    """Represents quality issues detected in a document."""
    
    def __init__(self, field_name: str, issue: str, affects_confidence: bool = True):
        self.field_name = field_name
        self.issue = issue
        self.affects_confidence = affects_confidence
    
    def __str__(self):
        return f"[{self.field_name}] {self.issue}"
