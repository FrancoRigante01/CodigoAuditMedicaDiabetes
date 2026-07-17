"""
Document validation module for completeness checking and inconsistency detection.
Detects missing required fields, quality issues, and logical inconsistencies.
"""

import logging
import re
from typing import List, Dict, Tuple
from datetime import datetime, timedelta

from .models import DOCUMENT_TYPES, ExtractedField

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validates documents for completeness and consistency."""
    
    def __init__(self):
        """Initialize the validator."""
        self.validation_rules = self._initialize_validation_rules()
    
    def validate_document(
        self,
        document_type: str,
        extracted_fields: Dict[str, ExtractedField],
        extracted_text: str,
        quality_warnings: List = None
    ) -> List[str]:
        """
        Validate document completeness and consistency.
        
        Args:
            document_type: Type of document
            extracted_fields: Dictionary of extracted fields with confidence scores
            extracted_text: Full extracted text from document
            quality_warnings: List of quality issues detected during reading
        
        Returns:
            List of inconsistencies, missing fields, and quality issues
        """
        issues = []
        
        # Add quality warnings
        if quality_warnings:
            for warning in quality_warnings:
                issues.append(f"Calidad: {warning.issue}")
        
        # Check required fields
        required_fields = DOCUMENT_TYPES.get(document_type, {}).get("required_fields", [])
        missing_fields = self._check_missing_fields(extracted_fields, required_fields)
        issues.extend(missing_fields)
        
        # Check low confidence fields
        low_confidence_issues = self._check_low_confidence_fields(extracted_fields)
        issues.extend(low_confidence_issues)
        
        # Document-type specific validation
        type_specific_issues = self._validate_document_type_specific(
            document_type, extracted_fields, extracted_text
        )
        issues.extend(type_specific_issues)
        
        # Check for logical inconsistencies
        consistency_issues = self._check_logical_consistency(
            document_type, extracted_fields
        )
        issues.extend(consistency_issues)
        
        return issues
    
    def _check_missing_fields(
        self,
        extracted_fields: Dict[str, ExtractedField],
        required_fields: List[str]
    ) -> List[str]:
        """Check for missing required fields."""
        issues = []
        
        for field in required_fields:
            if field not in extracted_fields:
                issues.append(f"Campo requerido faltante: {field}")
            else:
                field_value = extracted_fields[field].valor
                if field_value == "NOT_FOUND" or not field_value.strip():
                    issues.append(f"Campo requerido vacío o ilegible: {field}")
        
        return issues
    
    def _check_low_confidence_fields(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Check for fields with very low confidence scores."""
        issues = []
        
        # If confidence is below 30 and field is NOT_FOUND, flag it
        for field_name, field_data in extracted_fields.items():
            if field_data.confianza < 30 and field_data.valor != "NOT_FOUND":
                issues.append(
                    f"Campo con confianza muy baja ({field_data.confianza}%): "
                    f"{field_name}. Verificar manualmente."
                )
            elif field_data.confianza < 50 and field_data.valor != "NOT_FOUND":
                issues.append(
                    f"Campo con confianza moderadamente baja ({field_data.confianza}%): "
                    f"{field_name}. Revisar por posibles errores."
                )
        
        return issues
    
    def _validate_document_type_specific(
        self,
        document_type: str,
        extracted_fields: Dict[str, ExtractedField],
        extracted_text: str
    ) -> List[str]:
        """Apply document-type specific validation rules."""
        
        issues = []
        
        if document_type == "formulario_diabetes":
            issues.extend(self._validate_formulario_diabetes(extracted_fields))
        elif document_type == "laboratorio":
            issues.extend(self._validate_laboratorio(extracted_fields))
        elif document_type == "prescripcion":
            issues.extend(self._validate_prescripcion(extracted_fields))
        elif document_type == "estudio_diagnostico":
            issues.extend(self._validate_estudio_diagnostico(extracted_fields))
        
        return issues
    
    def _validate_formulario_diabetes(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Validation specific to diabetes forms."""
        issues = []
        
        # Check for signature
        if "datos_medico_tratante" in extracted_fields:
            value = extracted_fields["datos_medico_tratante"].valor
            confidence = extracted_fields["datos_medico_tratante"].confianza
            if value == "NOT_FOUND" or confidence < 40:
                issues.append("Firma o datos del médico tratante ilegibles o ausentes")
        
        # Check type of diabetes is specified
        if "tipo_diabetes" in extracted_fields:
            value = extracted_fields["tipo_diabetes"].valor
            if value == "NOT_FOUND":
                issues.append("Tipo de diabetes no especificado")
        
        # Check for at least one medication or supply
        med_found = (
            extracted_fields.get("medicacion_solicitada", ExtractedField(valor="NOT_FOUND", confianza=0)).valor != "NOT_FOUND"
        )
        insumo_found = (
            extracted_fields.get("insumo_solicitado", ExtractedField(valor="NOT_FOUND", confianza=0)).valor != "NOT_FOUND"
        )
        if not (med_found or insumo_found):
            issues.append("Ni medicación ni insumos solicitados encontrados")
        
        return issues
    
    def _validate_laboratorio(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Validation specific to laboratory reports."""
        issues = []
        
        # Check study date
        if "fecha_estudio" in extracted_fields:
            date_val = extracted_fields["fecha_estudio"].valor
            if date_val != "NOT_FOUND":
                try:
                    # Try to parse common date formats
                    date_obj = self._parse_date(date_val)
                    if date_obj:
                        # Check if date is not in the future
                        if date_obj > datetime.now():
                            issues.append(f"Fecha de estudio en el futuro: {date_val}")
                        # Check if date is not too old (> 1 year for demo purposes)
                        if (datetime.now() - date_obj).days > 365:
                            issues.append(f"Estudio muy antiguo (> 1 año): {date_val}")
                except:
                    pass
        
        # Check for numerical values
        if "valores_relevantes" in extracted_fields:
            value = extracted_fields["valores_relevantes"].valor
            if value == "NOT_FOUND":
                issues.append("Valores de laboratorio no encontrados")
        
        return issues
    
    def _validate_prescripcion(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Validation specific to prescriptions."""
        issues = []
        
        # Check prescription validity
        if "vigencia_receta" in extracted_fields:
            validity_val = extracted_fields["vigencia_receta"].valor
            if validity_val != "NOT_FOUND":
                try:
                    expiry_date = self._parse_date(validity_val)
                    if expiry_date:
                        if expiry_date < datetime.now():
                            issues.append(f"Receta vencida: {validity_val}")
                        # Check if expiry is too far in future (> 2 years)
                        if (expiry_date - datetime.now()).days > 730:
                            issues.append(f"Vigencia de receta inusualmente larga: {validity_val}")
                except:
                    pass
        
        # Check for dosage information
        if "dosis" in extracted_fields:
            value = extracted_fields["dosis"].valor
            if value == "NOT_FOUND":
                issues.append("Dosis no especificada")
            else:
                # Check for unusual values (very high/low doses)
                dosage_issues = self._validate_dosage(value)
                issues.extend(dosage_issues)
        
        # Check prescriber credentials
        if "matricula_prescriptor" in extracted_fields:
            mat_val = extracted_fields["matricula_prescriptor"].valor
            confidence = extracted_fields["matricula_prescriptor"].confianza
            if mat_val == "NOT_FOUND" or confidence < 40:
                issues.append("Matrícula del prescriptor ilegible o ausente")
        
        return issues
    
    def _validate_estudio_diagnostico(
        self,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Validation specific to diagnostic studies."""
        issues = []
        
        # Check study date
        if "fecha_informe" in extracted_fields:
            date_val = extracted_fields["fecha_informe"].valor
            if date_val != "NOT_FOUND":
                try:
                    date_obj = self._parse_date(date_val)
                    if date_obj and date_obj > datetime.now():
                        issues.append(f"Fecha de informe en el futuro: {date_val}")
                except:
                    pass
        
        # Check for conclusion
        if "conclusion_relevante" in extracted_fields:
            value = extracted_fields["conclusion_relevante"].valor
            if value == "NOT_FOUND":
                issues.append("Conclusión del estudio no encontrada")
        
        return issues
    
    def _check_logical_consistency(
        self,
        document_type: str,
        extracted_fields: Dict[str, ExtractedField]
    ) -> List[str]:
        """Check for logical inconsistencies between fields."""
        issues = []
        
        # Example: Check if diabetes type is consistent with medication type
        if document_type == "formulario_diabetes":
            diabetes_type = extracted_fields.get("tipo_diabetes", ExtractedField(valor="NOT_FOUND", confianza=0)).valor
            medication = extracted_fields.get("medicacion_solicitada", ExtractedField(valor="NOT_FOUND", confianza=0)).valor
            
            if diabetes_type != "NOT_FOUND" and medication != "NOT_FOUND":
                # Simple heuristic: some medications are primarily for type 2
                type2_medications = ["metformina", "glipizida", "gliburide", "acarbosa"]
                type1_medications = ["insulina"]
                
                med_lower = medication.lower()
                type_lower = diabetes_type.lower()
                
                # Check for obvious mismatch
                if any(t1_med in med_lower for t1_med in type1_medications) and "tipo 2" in type_lower:
                    issues.append(
                        "Posible inconsistencia: Insulina solicitada pero se reporta tipo 2 (revisar)"
                    )
        
        return issues
    
    def _parse_date(self, date_str: str):
        """Try to parse a date string in various formats."""
        formats = [
            "%d/%m/%Y",
            "%Y-%m-%d",
            "%d-%m-%Y",
            "%Y/%m/%d",
            "%d de %B de %Y",
            "%d de %b de %Y",
        ]
        
        # Clean the string
        date_str = date_str.strip()
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _validate_dosage(self, dosage_str: str) -> List[str]:
        """Validate dosage information."""
        issues = []
        
        # Extract numbers from dosage string
        numbers = re.findall(r'\d+(?:\.\d+)?', dosage_str)
        
        if numbers:
            for num_str in numbers:
                try:
                    num = float(num_str)
                    # Check for extremely high values (potential errors)
                    if num > 10000:
                        issues.append(f"Dosis potencialmente muy alta: {dosage_str} (revisar)")
                except ValueError:
                    pass
        
        return issues
    
    def _initialize_validation_rules(self) -> Dict:
        """Initialize document-specific validation rules."""
        return {
            "formulario_diabetes": {
                "required_signature": True,
                "check_dates": True,
                "min_fields": 3
            },
            "laboratorio": {
                "check_dates": True,
                "check_values": True,
                "min_fields": 2
            },
            "prescripcion": {
                "check_expiry": True,
                "check_dosage": True,
                "min_fields": 2
            },
            "estudio_diagnostico": {
                "check_dates": True,
                "min_fields": 2
            }
        }
