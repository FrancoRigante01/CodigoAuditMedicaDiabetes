"""Main document processing orchestrator.

Combines document reading, classification, field extraction, validation, and
output formatting into a single, reusable pipeline.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from .document_reader import DocumentReader
from .classifier import DocumentClassifier
from .field_extractor import FieldExtractor
from .validator import DocumentValidator
from .output_formatter import OutputFormatter
from .error_handler import ErrorHandler
from .models import DocumentProcessingResult, ProcessingError

logger = logging.getLogger(__name__)


class MedicalDocumentProcessor:
    """End-to-end processor for medical documents in the diabetes audit demo."""

    def __init__(
        self,
        use_ocr: bool = True,
        api_key: Optional[str] = None,
        mock_mode: bool = False,
    ):
        """
        Initialize the medical document processor.

        Args:
            use_ocr: Whether to use OCR for scanned documents.
            api_key: Optional Anthropic API key for classification/extraction.
            mock_mode: If True, use deterministic mock logic instead of API calls.
                       Useful for demos without an API key.
        """
        self.use_ocr = use_ocr
        self.mock_mode = mock_mode
        self.reader = DocumentReader(use_ocr=use_ocr)
        self.validator = DocumentValidator()
        self.formatter = OutputFormatter()
        self.error_handler = ErrorHandler(logger=logger)

        if not mock_mode:
            # These require a valid Anthropic API key.
            self.classifier = DocumentClassifier(api_key=api_key)
            self.extractor = FieldExtractor()
        else:
            self.classifier = None
            self.extractor = None

    def process_document(
        self,
        file_path: Union[str, Path]
    ) -> DocumentProcessingResult:
        """
        Process a document through the full pipeline.

        Args:
            file_path: Path to the PDF or image file.

        Returns:
            DocumentProcessingResult with classification, fields, and issues.
        """
        file_path = Path(file_path)

        try:
            # Step 1: Read document (PDF / image -> text + images + metadata)
            logger.info(f"Reading document: {file_path}")
            text, images, metadata = self.reader.read_document(file_path)
            quality_warnings = self.reader.get_quality_warnings()

            # Step 2: Classify document
            if self.mock_mode:
                doc_type, classification_confidence = self._mock_classify(file_path, text)
            else:
                doc_type, classification_confidence = self.classifier.classify_document(
                    text,
                    images,
                    metadata
                )

            # Step 3: Extract fields
            if self.mock_mode:
                extracted_fields = self._mock_extract_fields(doc_type)
            else:
                extracted_fields = self.extractor.extract_fields(
                    document_type=doc_type,
                    extracted_text=text,
                    images_bytes=images,
                    classification_confidence=classification_confidence,
                    quality_warnings=quality_warnings
                )

            # Step 4: Validate (missing fields, inconsistencies, quality)
            issues = self.validator.validate_document(
                document_type=doc_type,
                extracted_fields=extracted_fields,
                extracted_text=text,
                quality_warnings=quality_warnings
            )

            # Step 5: Format output
            result = self.formatter.format_result(
                document_type=doc_type,
                classification_confidence=classification_confidence,
                extracted_fields=extracted_fields,
                inconsistencies_and_missing=issues
            )

            logger.info(
                f"Document processed: type={doc_type}, "
                f"classification_confidence={classification_confidence}"
            )
            return result

        except Exception as e:
            error_message = self.error_handler.handle_error(
                error_type="extraction_failed",
                error_details={"reason": str(e)},
                raise_exception=False
            )
            logger.exception("Document processing failed")
            raise ProcessingError(error_message) from e

    def process_documents(
        self,
        file_paths: List[Union[str, Path]]
    ) -> List[DocumentProcessingResult]:
        """Process multiple documents and return a list of results."""
        results = []
        for path in file_paths:
            try:
                result = self.process_document(path)
                results.append(result)
            except ProcessingError as e:
                logger.error(f"Failed to process {path}: {e}")
                raise
        return results

    def _mock_classify(self, file_path: Path, extracted_text: str = "") -> tuple[str, int]:
        """Deterministic classification for mock/demonstration mode."""
        lower_name = file_path.stem.lower()
        text_lower = (extracted_text or "").lower()

        mapping = {
            "formulario_diabetes": "formulario_diabetes",
            "laboratorio": "laboratorio",
            "prescripcion": "prescripcion",
            "estudio_diagnostico": "estudio_diagnostico",
        }

        # First, try to classify by filename hints
        for key, doc_type in mapping.items():
            if key in lower_name:
                return doc_type, 92

        # Fallback: classify by keyword presence in extracted text
        keyword_rules = [
            ("laboratorio", ["glucosa", "glucemia", "hbac", "hemoglobina glicosilada",
                             "colesterol", "trigliceridos", "orina", "sangre",
                             "laboratorio", "resultados", "mg/dl", "u/l"]),
            ("prescripcion", ["receta", "prescripcion", "indicaciones", "dosis",
                              "tomar", "comp", "comprimidos", "mg", "farmacia"]),
            ("estudio_diagnostico", ["ecografia", "ecocardiografia", "radiografia",
                                     "tomografia", "resonancia", "informe", "conclusion",
                                     "estudio", "imagenes", "hallazgos"]),
            ("formulario_diabetes", ["diabetes", "medicacion", "solicitud",
                                     "autorizacion", "medico tratante", "firma"]),
        ]

        scores = {doc_type: 0 for doc_type in mapping.values()}
        for doc_type, keywords in keyword_rules:
            for keyword in keywords:
                if keyword in text_lower:
                    scores[doc_type] += 1

        if scores and max(scores.values()) > 0:
            best_type = max(scores, key=scores.get)
            return best_type, 85

        return "estudio_diagnostico", 75

    def _mock_extract_fields(self, doc_type: str) -> Dict[str, dict]:
        """Deterministic field templates for mock/demonstration mode."""
        from .models import DOCUMENT_TYPES, ExtractedField

        templates = {
            "formulario_diabetes": {
                "diagnostico": ("Diabetes Mellitus tipo 2", 95),
                "tipo_diabetes": ("tipo 2", 90),
                "medicacion_solicitada": ("Metformina 500mg, Enalapril 10mg", 88),
                "insumo_solicitado": ("Tiras reactivas, lancetas", 85),
                "fecha_firma": ("12/07/2024", 98),
                "datos_medico_tratante": ("Dr. Roberto Martínez López, MP-2024-001567", 92),
            },
            "laboratorio": {
                "tipo_estudio": ("Glucemia en Ayunas, HbA1c", 92),
                "fecha_estudio": ("08/07/2024", 96),
                "valores_relevantes": ("Glucemia: 145 mg/dL, HbA1c: 7.8%", 90),
            },
            "prescripcion": {
                "medicacion_insumo": ("Metformina 850mg, Bromocriptina 2.5mg", 94),
                "dosis": ("1 comprimido c/12hs, 1/2 comprimido en la mañana", 89),
                "vigencia_receta": ("30 días, válida hasta 13/08/2024", 97),
                "matricula_prescriptor": ("MP-1985-002456", 93),
            },
            "estudio_diagnostico": {
                "tipo_informe": ("Ecocardiografía", 91),
                "fecha_informe": ("11/07/2024", 99),
                "conclusion_relevante": ("Función sistólica y diastólica conservadas. Sin hallazgos patológicos", 87),
            },
        }

        template = templates.get(doc_type, {})
        fields = {}
        for name, (value, confidence) in template.items():
            fields[name] = ExtractedField(valor=value, confianza=confidence)

        # Fill in any expected but missing fields with NOT_FOUND and confidence 0
        spec = DOCUMENT_TYPES.get(doc_type, {})
        for name in spec.get("required_fields", []) + spec.get("optional_fields", []):
            if name not in fields:
                fields[name] = ExtractedField(valor="NOT_FOUND", confianza=0)

        return fields
