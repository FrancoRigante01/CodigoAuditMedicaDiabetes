"""
Output formatting module for document processing results.
Generates JSON responses in the specified format.
"""

import json
import logging
from typing import Dict, List, Optional

from .models import DocumentProcessingResult, ExtractedField

logger = logging.getLogger(__name__)


class OutputFormatter:
    """Formats document processing results into JSON output."""
    
    def __init__(self):
        """Initialize the output formatter."""
        pass
    
    def format_result(
        self,
        document_type: str,
        classification_confidence: int,
        extracted_fields: Dict[str, ExtractedField],
        inconsistencies_and_missing: List[str]
    ) -> DocumentProcessingResult:
        """
        Format processing result into the required structure.
        
        Args:
            document_type: Classified document type
            classification_confidence: Confidence of the classification (0-100)
            extracted_fields: Dictionary mapping field names to ExtractedField objects
            inconsistencies_and_missing: List of detected issues
        
        Returns:
            DocumentProcessingResult ready for JSON serialization
        """
        # Clamp confidence to valid range
        classification_confidence = max(0, min(100, classification_confidence))
        
        # Create the result object
        result = DocumentProcessingResult(
            tipo_documento=document_type,
            confianza_clasificacion=classification_confidence,
            campos_extraidos=extracted_fields,
            faltantes_o_inconsistencias=inconsistencies_and_missing
        )
        
        logger.info(
            f"Formatted result for document type: {document_type} "
            f"with {len(extracted_fields)} fields and "
            f"{len(inconsistencies_and_missing)} issues"
        )
        
        return result
    
    def to_json_string(
        self,
        result: DocumentProcessingResult,
        pretty_print: bool = True,
        indent: int = 2
    ) -> str:
        """
        Convert result to JSON string.
        
        Args:
            result: DocumentProcessingResult object
            pretty_print: Whether to format with indentation
            indent: Number of spaces for indentation
        
        Returns:
            JSON string representation
        """
        # Convert Pydantic model to dictionary
        result_dict = self._convert_to_serializable(result)
        
        if pretty_print:
            return json.dumps(result_dict, indent=indent, ensure_ascii=False)
        else:
            return json.dumps(result_dict, ensure_ascii=False)
    
    def to_json_dict(
        self,
        result: DocumentProcessingResult
    ) -> Dict:
        """
        Convert result to dictionary format suitable for JSON.
        
        Args:
            result: DocumentProcessingResult object
        
        Returns:
            Dictionary representation
        """
        return self._convert_to_serializable(result)
    
    def _convert_to_serializable(self, result: DocumentProcessingResult) -> Dict:
        """
        Convert DocumentProcessingResult to a JSON-serializable dictionary.
        
        Handles Pydantic model serialization.
        """
        return {
            "tipo_documento": result.tipo_documento,
            "confianza_clasificacion": result.confianza_clasificacion,
            "campos_extraidos": {
                field_name: {
                    "valor": field_data.valor,
                    "confianza": field_data.confianza
                }
                for field_name, field_data in result.campos_extraidos.items()
            },
            "faltantes_o_inconsistencias": result.faltantes_o_inconsistencias
        }
    
    def validate_result(self, result: DocumentProcessingResult) -> bool:
        """
        Validate that a result meets all requirements.
        
        Returns:
            True if valid, False otherwise
        """
        # Check document type is valid
        valid_types = [
            "formulario_diabetes",
            "laboratorio",
            "estudio_diagnostico",
            "prescripcion"
        ]
        if result.tipo_documento not in valid_types:
            logger.error(f"Invalid document type: {result.tipo_documento}")
            return False
        
        # Check classification confidence range
        if not (0 <= result.confianza_clasificacion <= 100):
            logger.error(
                f"Classification confidence out of range: "
                f"{result.confianza_clasificacion}"
            )
            return False
        
        # Check all field confidences are in valid range
        for field_name, field_data in result.campos_extraidos.items():
            if not (0 <= field_data.confianza <= 100):
                logger.error(
                    f"Field {field_name} confidence out of range: "
                    f"{field_data.confianza}"
                )
                return False
        
        logger.info("Result validation passed")
        return True
