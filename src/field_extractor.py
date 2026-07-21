"""
Field extraction module for medical documents.
Extracts document type-specific fields with individual confidence scores.
"""

import logging
import re
from typing import Dict, Tuple, List
import base64
import requests

from .models import DOCUMENT_TYPES, ExtractedField

logger = logging.getLogger(__name__)


class FieldExtractor:
    """Extracts fields from medical documents with per-field confidence scoring."""
    
    def __init__(self):
        """Initialize the field extractor."""
        import os
        self.api_url = "https://frida.azure-api.net/frida-app-service-llm-compatible-api/v1/chat/completions"
        self.api_key = os.environ.get("FRIDA_API_KEY", "")
        self.model_name = "SELENE-CIPHER"
        self.extraction_history = []
    
    def extract_fields(
        self,
        document_type: str,
        extracted_text: str,
        images_bytes: List[bytes] = None,
        classification_confidence: int = 80,
        quality_warnings: List = None
    ) -> Dict[str, ExtractedField]:
        """
        Extract fields specific to the document type.
        
        Args:
            document_type: One of: formulario_diabetes, laboratorio, estudio_diagnostico, prescripcion
            extracted_text: Text extracted from the document
            images_bytes: List of image bytes for multimodal analysis
            classification_confidence: Confidence of the document type classification
            quality_warnings: List of quality issues detected during document reading
        
        Returns:
            Dictionary mapping field names to ExtractedField objects with values and confidence scores
        """
        if document_type not in DOCUMENT_TYPES:
            logger.error(f"Unknown document type: {document_type}")
            return {}
        
        # Get field specifications for this document type
        doc_spec = DOCUMENT_TYPES[document_type]
        required_fields = doc_spec["required_fields"]
        optional_fields = doc_spec["optional_fields"]
        all_fields = required_fields + optional_fields
        
        # Assess overall text quality/legibility
        text_legibility_score = self._assess_text_legibility(extracted_text, quality_warnings)
        
        # Build extraction prompt with legibility context
        extraction_prompt = self._build_extraction_prompt(
            document_type, extracted_text, required_fields, optional_fields, text_legibility_score
        )
        
        # Prepare message for FRIDA
        message_content = [
            {
                "type": "text",
                "text": extraction_prompt
            }
        ]
        
        # Add images if available
        if images_bytes:
            for idx, img_bytes in enumerate(images_bytes[:3]):  # Limit to first 3 images
                try:
                    b64_image = base64.standard_b64encode(img_bytes).decode("utf-8")
                    message_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{b64_image}"
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to add image {idx} to extraction: {e}")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Ocp-Apim-Subscription-Key": self.api_key
        }

        payload = {
            "model": self.model_name,
            "user_id": "extractor_demo",
            "email": "demo@sancorsalud.com.ar",
            "messages": [
                {
                    "role": "user",
                    "content": message_content
                }
            ],
            "max_tokens": 2000,
            "temperature": 0.2
        }

        try:
            logger.info("Enviando solicitud a FRIDA API para extracción...")
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            if not response.ok:
                logger.error(f"FRIDA API Error {response.status_code}: {response.text}")
            response.raise_for_status()
            
            response_json = response.json()
            if "choices" in response_json and len(response_json["choices"]) > 0:
                result_text = response_json["choices"][0]["message"]["content"]
                logger.error(f"====== FRIDA EXTRACTION RESPONSE ======\n{result_text}\n=======================================")
            else:
                logger.error(f"Respuesta inesperada de FRIDA API: {response_json}")
                return self._create_empty_extraction(all_fields)
            
            extracted_fields = self._parse_extraction_response(
                result_text, required_fields, optional_fields, 
                classification_confidence, text_legibility_score
            )
            
            self.extraction_history.append({
                "document_type": document_type,
                "extracted_fields": extracted_fields,
                "raw_response": result_text
            })
            
            return extracted_fields
            
        except Exception as e:
            logger.error(f"Field extraction error: {e}")
            return self._create_empty_extraction(all_fields)
    
    def _build_extraction_prompt(
        self,
        document_type: str,
        text: str,
        required_fields: List[str],
        optional_fields: List[str],
        text_legibility_score: int = 80
    ) -> str:
        """Build the prompt for field extraction with legibility context."""
        
        field_descriptions = self._get_field_descriptions(document_type)
        
        # Build required fields section
        required_fields_spec = "\\n".join([
            f"- {field} (REQUIRED): {field_descriptions.get(field, 'Extract this field')}"
            for field in required_fields
        ])
        
        # Build optional fields section
        optional_fields_spec = "\\n".join([
            f"- {field} (OPTIONAL): {field_descriptions.get(field, 'Extract this field')}"
            for field in optional_fields
        ])
        
        # Build legibility assessment
        legibility_guidance = self._get_legibility_guidance(text_legibility_score)
        
        prompt = f"""You are a medical document field extractor for diabetes medication auditing.
Extract specific fields from a {document_type} document.

DOCUMENT QUALITY ASSESSMENT:
- Text legibility score: {text_legibility_score}/100
- Guidance: {legibility_guidance}

REQUIRED FIELDS (critical - must extract or mark NOT_FOUND):
{required_fields_spec}

OPTIONAL FIELDS (nice-to-have - extract if visible):
{optional_fields_spec}

Document content:
{text[:3000]}

EXTRACTION INSTRUCTIONS:
1. For REQUIRED fields: Always attempt extraction. If illegible/missing, set VALUE to NOT_FOUND with low confidence (20-40).
2. For OPTIONAL fields: Only extract if clearly visible. Set to NOT_FOUND if not present.
3. For EACH field, assign a confidence score (0-100) based on:
   - Text clarity and legibility (adjust based on document quality)
   - Field completeness (lower if partial information)
   - Data validity (lower if unusual or suspicious values)
   - DO NOT guess or invent values - if unsure, lower confidence
4. Account for handwritten text (typically lower confidence than printed)
5. Flag illegible sections with low confidence rather than making up values

RESPONSE FORMAT (for each field):
FIELD: <field_name>
VALUE: <extracted_value or NOT_FOUND>
CONFIDENCE: <0-100>
REASONING: <one sentence explaining confidence>

CRITICAL: Be conservative with confidence scores. If document quality is poor,
confidence scores across all fields should reflect this uncertainty."""
        
        return prompt
    
    def _get_field_descriptions(self, document_type: str) -> Dict[str, str]:
        """Get human-readable descriptions of fields for each document type."""
        
        descriptions = {
            "formulario_diabetes": {
                "diagnostico": "Primary diagnosis mentioned in the form",
                "tipo_diabetes": "Type of diabetes (tipo 1, tipo 2, gestacional, etc.)",
                "medicacion_solicitada": "Medications being requested/prescribed",
                "insumo_solicitado": "Medical supplies (test strips, glucometer, etc.)",
                "fecha_firma": "Date when the form was signed",
                "datos_medico_tratante": "Treating physician name, license number, signature",
                "notas_medico": "Any additional notes or observations from the physician"
            },
            "laboratorio": {
                "tipo_estudio": "Type of laboratory test (glucose, A1c, etc.)",
                "fecha_estudio": "Date when the test was performed",
                "valores_relevantes": "Numerical results (glucose value, A1c percentage, etc.)",
                "laboratorio_nombre": "Name of the laboratory that performed the test",
                "medico_solicitante": "Physician who requested the test"
            },
            "prescripcion": {
                "medicacion_insumo": "Medication or medical supply being prescribed",
                "dosis": "Dosage and administration instructions",
                "vigencia_receta": "Prescription validity period or expiration date",
                "matricula_prescriptor": "Prescriber's professional license/registration number",
                "nombre_prescriptor": "Name of the prescribing physician",
                "indicaciones": "Clinical indications or reasons for prescription"
            },
            "estudio_diagnostico": {
                "tipo_informe": "Type of diagnostic study (ultrasound, CT, X-ray, etc.)",
                "fecha_informe": "Date when the study was performed or reported",
                "conclusion_relevante": "Key clinical findings or conclusions",
                "medico_responsable": "Physician responsible for the study",
                "modalidad_estudio": "Imaging or diagnostic modality used"
            }
        }
        
        return descriptions.get(document_type, {})
    
    def _parse_extraction_response(
        self,
        response_text: str,
        required_fields: List[str],
        optional_fields: List[str],
        classification_confidence: int,
        text_legibility_score: int = 80
    ) -> Dict[str, ExtractedField]:
        """Parse Claude's response to extract field values and confidences."""
        
        extracted = {}
        all_fields = required_fields + optional_fields
        
        # Split response into field blocks
        field_blocks = re.split(r'(?:^|\n)FIELD:\s+', response_text, flags=re.MULTILINE)
        
        for block in field_blocks[1:]:  # Skip first empty split
            try:
                lines = block.strip().split('\n')
                field_name = lines[0].strip()
                
                # Extract value
                value = "NOT_FOUND"
                value_match = re.search(r'VALUE:\s*(.+?)(?=\nCONFIDENCE:|$)', block, re.DOTALL)
                if value_match:
                    value = value_match.group(1).strip()
                
                # Extract confidence
                confidence = 20  # Default low confidence if not found
                conf_match = re.search(r'CONFIDENCE:\s*(\d+)', block)
                if conf_match:
                    confidence = int(conf_match.group(1))
                    confidence = max(0, min(100, confidence))  # Clamp to 0-100
                
                # Adjust confidence based on classification confidence AND text legibility
                if value != "NOT_FOUND":
                    # Apply both document classification and text quality factors
                    confidence = int(confidence * (classification_confidence / 100))
                    confidence = int(confidence * (text_legibility_score / 100))
                else:
                    # If field not found, confidence is always low regardless of legibility
                    confidence = 0
                
                # Only include fields from expected field list
                if field_name in all_fields or field_name.replace('_', ' ').title() in all_fields:
                    extracted[field_name] = ExtractedField(
                        valor=value,
                        confianza=confidence
                    )
            
            except Exception as e:
                logger.warning(f"Error parsing field block: {e}")
                continue
        
        # Add any missing required fields with NOT_FOUND and zero confidence
        for field in required_fields:
            if field not in extracted:
                extracted[field] = ExtractedField(
                    valor="NOT_FOUND",
                    confianza=0
                )
        
        # Add any missing optional fields with NOT_FOUND and zero confidence
        for field in optional_fields:
            if field not in extracted:
                extracted[field] = ExtractedField(
                    valor="NOT_FOUND",
                    confianza=0
                )
        
        return extracted
    
    def _create_empty_extraction(self, fields: List[str]) -> Dict[str, ExtractedField]:
        """Create an empty extraction result for all fields."""
        return {
            field: ExtractedField(valor="NOT_FOUND", confianza=0)
            for field in fields
        }
    
    def _assess_text_legibility(self, text: str, quality_warnings: List = None) -> int:
        """
        Assess overall legibility of extracted text.
        
        Returns a score from 0-100 based on text quality indicators.
        """
        if not text or len(text.strip()) == 0:
            return 10  # Very poor - essentially no text
        
        legibility_score = 100  # Start with perfect score
        
        # Check text length (more text = better quality)
        if len(text.strip()) < 100:
            legibility_score -= 20
        elif len(text.strip()) < 500:
            legibility_score -= 10
        
        # Count suspicious patterns (very common OCR errors or illegible markers)
        text_lower = text.lower()
        suspicious_count = 0
        
        # Look for common OCR artifacts or illegible patterns
        suspicious_patterns = [
            r'[^\w\s\d.,;:\-ñáéíóúü]',  # Non-standard characters
            r'\?{2,}',  # Multiple question marks (OCR uncertainty)
            r'xxx',  # Common illegibility marker
            r'---',  # Lines indicating missing content
        ]
        
        for pattern in suspicious_patterns:
            matches = len(re.findall(pattern, text_lower))
            suspicious_count += matches
        
        if suspicious_count > 10:
            legibility_score -= 30
        elif suspicious_count > 5:
            legibility_score -= 15
        
        # Check for quality warnings
        if quality_warnings:
            for warning in quality_warnings:
                if "resolution" in str(warning).lower() or "low" in str(warning).lower():
                    legibility_score -= 20
                elif "blank" in str(warning).lower() or "content" in str(warning).lower():
                    legibility_score -= 25
        
        # Check handwriting indicators (common in Spanish documents)
        handwriting_words = ["manuscrito", "handwritten", "firma", "firmado", "holográfico"]
        if any(word in text_lower for word in handwriting_words):
            legibility_score -= 10  # Handwriting typically has lower confidence
        
        # Ensure score stays within bounds
        return max(10, min(100, legibility_score))
    
    def _get_legibility_guidance(self, legibility_score: int) -> str:
        """Get guidance text based on legibility score."""
        if legibility_score >= 85:
            return "Document is clear and legible. Extract with normal confidence levels."
        elif legibility_score >= 70:
            return "Document has minor quality issues. Reduce confidence for borderline extractions."
        elif legibility_score >= 50:
            return "Document quality is moderate. Significantly reduce confidence for uncertain fields."
        elif legibility_score >= 30:
            return "Document quality is poor. Only extract fields that are clearly visible, otherwise mark NOT_FOUND."
        else:
            return "Document is very poor quality/mostly illegible. Mark uncertain fields as NOT_FOUND with low confidence."
    
    def get_extraction_history(self):
        """Return the history of extractions made."""
        return self.extraction_history
