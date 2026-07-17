"""
Catalog of required documents for the renewal procedure.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

from .renewal_models import DocumentRequirement, RenewalCatalog


def build_renovacion_diabetes_catalog() -> RenewalCatalog:
    """Build the catalog of required documents for RENOVACION_DIABETES."""
    requirements = [
        DocumentRequirement(
            requirement_id="FORMULARIO_RENOVACION",
            expected_document_type="formulario_diabetes",
            name="Formulario de Renovación",
            description="Formulario específico para la solicitud de renovación del tratamiento de diabetes.",
            is_mandatory=True,
            max_documents=1,
            allow_multiple_distinct=False,
            min_quality_score=40,
            min_classification_confidence=50,
        ),
        DocumentRequirement(
            requirement_id="ESTUDIOS_LABORATORIO",
            expected_document_type="laboratorio",
            name="Estudios de Laboratorio",
            description="Estudios de laboratorio vigentes requeridos para la renovación (ej.: hemoglobina glicosilada, glucemia).",
            is_mandatory=True,
            max_documents=5,
            allow_multiple_distinct=True,
            min_quality_score=40,
            min_classification_confidence=50,
        ),
        DocumentRequirement(
            requirement_id="PRESCRIPCION_MEDICA",
            expected_document_type="prescripcion",
            name="Prescripción Médica",
            description="Prescripción médica vigente que respalde la solicitud de renovación.",
            is_mandatory=True,
            max_documents=1,
            allow_multiple_distinct=False,
            min_quality_score=40,
            min_classification_confidence=50,
        ),
        DocumentRequirement(
            requirement_id="ESTUDIO_DIAGNOSTICO",
            expected_document_type="estudio_diagnostico",
            name="Estudio Diagnóstico",
            description="Estudio diagnóstico que acredite la indicación del tratamiento (puede ser ecografía, tomografía, etc.).",
            is_mandatory=True,
            max_documents=2,
            allow_multiple_distinct=True,
            min_quality_score=40,
            min_classification_confidence=50,
        ),
    ]

    return RenewalCatalog(
        procedure_code="RENOVACION_DIABETES",
        name="Renovación de tratamiento de Diabetes",
        requirements=requirements,
    )


RENOVACION_CATALOGS = {
    "RENOVACION_DIABETES": build_renovacion_diabetes_catalog(),
}


def get_catalog(procedure_code: str) -> RenewalCatalog:
    """Return the catalog for the given procedure code."""
    if procedure_code not in RENOVACION_CATALOGS:
        raise ValueError(f"No catalog configured for procedure code: {procedure_code}")
    return RENOVACION_CATALOGS[procedure_code]
