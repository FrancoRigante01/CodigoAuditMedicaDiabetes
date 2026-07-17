"""
Document type classifier for medical documents.
Classifies documents into: formulario_diabetes, laboratorio, estudio_diagnostico, prescripcion.
"""

import logging
import re
from typing import Tuple
from anthropic import Anthropic

from .models import DOCUMENT_TYPES

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Classifies medical documents using Claude's vision capabilities."""
    
    DOCUMENT_TYPES_ENUM = list(DOCUMENT_TYPES.keys())
    
    def __init__(self, api_key: str = None):
        """
        Initialize the classifier with Claude API.
        
        Args:
            api_key: Anthropic API key (uses ANTHROPIC_API_KEY env var if not provided)
        """
        self.client = Anthropic()
        self.classification_history = []
    
    def classify_document(
        self,
        extracted_text: str,
        images_bytes: list = None,
        metadata: dict = None
    ) -> Tuple[str, int]:
        """
        Classify a document and return type and confidence score.
        
        Args:
            extracted_text: Text extracted from the document
            images_bytes: List of image bytes for multimodal analysis
            metadata: Document metadata (format, page_count, etc.)
        
        Returns:
            Tuple of (document_type, confidence_score)
        """
        if not extracted_text and not images_bytes:
            logger.warning("No text or images provided for classification")
            return "estudio_diagnostico", 10  # Default low-confidence classification
        
        # Build classification prompt
        classification_prompt = self._build_classification_prompt(
            extracted_text, metadata
        )
        
        # Prepare message for Claude
        message_content = [
            {
                "type": "text",
                "text": classification_prompt
            }
        ]
        
        # Add images if available
        if images_bytes:
            for idx, img_bytes in enumerate(images_bytes[:3]):  # Limit to first 3 images
                try:
                    import base64
                    b64_image = base64.standard_b64encode(img_bytes).decode("utf-8")
                    message_content.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": b64_image
                        }
                    })
                except Exception as e:
                    logger.warning(f"Failed to add image {idx} to classification: {e}")
        
        try:
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": message_content
                    }
                ]
            )
            
            result_text = response.content[0].text
            doc_type, confidence = self._parse_classification_response(result_text)
            
            self.classification_history.append({
                "type": doc_type,
                "confidence": confidence,
                "raw_response": result_text
            })
            
            return doc_type, confidence
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return "estudio_diagnostico", 20
    
    def _build_classification_prompt(self, text: str, metadata: dict = None) -> str:
        """Build the prompt for document classification."""
        
        metadata_str = ""
        if metadata:
            metadata_str = f"""
Document Metadata:
- Format: {metadata.get('format', 'unknown')}
- Page count: {metadata.get('page_count', 1)}
- Has structured text: {metadata.get('has_text', False)}
"""
        
        prompt = f"""You are a medical document classifier for diabetes medication auditing. 
Classify the following medical document into ONE of these categories:
1. formulario_diabetes - A structured form signed by a treating physician with diagnosis and medication requests
2. laboratorio - Laboratory test results with values like glucose, hemoglobin A1c, etc.
3. estudio_diagnostico - Medical diagnostic reports and complementary studies
4. prescripcion - Medical prescriptions for medications or supplies (test strips, glucometers)

{metadata_str}

Document content:
{text[:2000]}

Respond ONLY in this exact format:
DOCUMENT_TYPE: [one of: formulario_diabetes, laboratorio, estudio_diagnostico, prescripcion]
CONFIDENCE: [number 0-100]
REASONING: [one sentence explaining why]

Be conservative with confidence - lower it if:
- Text is unclear or illegible
- Document type indicators are ambiguous
- Multiple possible classifications apply
- Image quality is poor"""
        
        return prompt
    
    def _parse_classification_response(self, response_text: str) -> Tuple[str, int]:
        """Parse Claude's response to extract document type and confidence."""
        
        doc_type = None
        confidence = 50
        
        # Extract document type
        type_match = re.search(
            r'DOCUMENT_TYPE:\s*([a-z_]+)',
            response_text,
            re.IGNORECASE
        )
        if type_match:
            found_type = type_match.group(1).strip()
            if found_type in self.DOCUMENT_TYPES_ENUM:
                doc_type = found_type
        
        # Extract confidence
        conf_match = re.search(
            r'CONFIDENCE:\s*(\d+)',
            response_text,
            re.IGNORECASE
        )
        if conf_match:
            confidence = int(conf_match.group(1))
            confidence = max(0, min(100, confidence))  # Clamp to 0-100
        
        # Default if parsing failed
        if not doc_type:
            doc_type = "estudio_diagnostico"
            confidence = 30
            logger.warning("Failed to parse classification response, using default")
        
        return doc_type, confidence
    
    def get_classification_history(self):
        """Return the history of classifications made."""
        return self.classification_history
