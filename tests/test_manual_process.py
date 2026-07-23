import os
from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

from src.processor import MedicalDocumentProcessor

processor = MedicalDocumentProcessor(use_ocr=True, mock_mode=False)
result = processor.process_document("tests/1_aprobacion_completa.png")

print("Result:")
print(result.model_dump())
