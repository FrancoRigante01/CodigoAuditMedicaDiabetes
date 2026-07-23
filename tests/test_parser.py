from src.field_extractor import FieldExtractor
from src.models import DOCUMENT_TYPES

response = """
FIELD: diagnostico
VALUE: Diabetes Tipo 2
CONFIDENCE: 95
REASONING: Diagnostico claramente impreso.

FIELD: tipo_diabetes
VALUE: Tipo 2
CONFIDENCE: 95
REASONING: Extraido directamente.
"""

fe = FieldExtractor()
doc_spec = DOCUMENT_TYPES["formulario_diabetes"]
all_req = doc_spec["required_fields"]
all_opt = doc_spec["optional_fields"]

res = fe._parse_extraction_response(response, all_req, all_opt, classification_confidence=98, text_legibility_score=80)
print(res)
