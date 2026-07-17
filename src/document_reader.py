"""
Document reading and content extraction from PDFs and images.
Handles multimodal input (scanned documents, handwritten text, printed text).
"""

import base64
import io
import logging
from pathlib import Path
from typing import Union, List, Optional
import json

import cv2
from PIL import Image
import pdfplumber
import easyocr

from .models import ProcessingError, DocumentQualityWarning

logger = logging.getLogger(__name__)


class DocumentReader:
    """Reads and extracts content from PDF and image documents."""
    
    SUPPORTED_FORMATS = {".pdf", ".png", ".jpg", ".jpeg"}
    MAX_FILE_SIZE_MB = 50
    
    def __init__(self, use_ocr: bool = True, use_vision_api: bool = True):
        """
        Initialize document reader.
        
        Args:
            use_ocr: Whether to use EasyOCR for scanned documents
            use_vision_api: Whether to use vision API for document understanding
        """
        self.use_ocr = use_ocr
        self.use_vision_api = use_vision_api
        self.quality_warnings: List[DocumentQualityWarning] = []
        
        # Initialize OCR reader for Spanish language
        if self.use_ocr:
            try:
                self.ocr_reader = easyocr.Reader(['es', 'en'])
                logger.info("OCR reader initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OCR reader: {e}")
                self.ocr_reader = None
    
    def read_document(self, file_path: Union[str, Path]) -> tuple[str, List[bytes], dict]:
        """
        Read document and extract text and images.
        
        Args:
            file_path: Path to PDF or image file
            
        Returns:
            Tuple of (extracted_text, images_bytes_list, metadata)
            
        Raises:
            ProcessingError: If file cannot be read or processed
        """
        file_path = Path(file_path)
        
        # Validate file
        self._validate_file(file_path)
        
        # Reset quality warnings
        self.quality_warnings = []
        
        # Route to appropriate reader
        if file_path.suffix.lower() == ".pdf":
            return self._read_pdf(file_path)
        else:
            return self._read_image(file_path)
    
    def _validate_file(self, file_path: Path) -> None:
        """Validate file exists and has acceptable format/size."""
        if not file_path.exists():
            raise ProcessingError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() not in self.SUPPORTED_FORMATS:
            raise ProcessingError(
                f"Unsupported file format: {file_path.suffix}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.MAX_FILE_SIZE_MB:
            raise ProcessingError(
                f"File too large: {file_size_mb:.1f}MB. "
                f"Maximum: {self.MAX_FILE_SIZE_MB}MB"
            )
    
    def _read_pdf(self, file_path: Path) -> tuple[str, List[bytes], dict]:
        """Extract text and images from PDF."""
        all_text = []
        images_bytes = []
        metadata = {
            "format": "pdf",
            "page_count": 0,
            "has_text": False,
            "has_scanned_images": False
        }
        
        try:
            with pdfplumber.open(file_path) as pdf:
                metadata["page_count"] = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    # Extract text from PDF
                    text = page.extract_text()
                    if text and text.strip():
                        all_text.append(f"--- Página {page_num + 1} ---\n{text}")
                        metadata["has_text"] = True
                    
                    # Extract images from PDF for vision analysis
                    try:
                        for img_index, img_dict in enumerate(page.images):
                            try:
                                img_bytes = img_dict['stream'].get_rawdata()
                                images_bytes.append(img_bytes)
                                metadata["has_scanned_images"] = True
                            except Exception as e:
                                logger.warning(f"Could not extract image {img_index} from page {page_num}: {e}")
                    except Exception as e:
                        logger.debug(f"Could not extract images from page {page_num}: {e}")
                    
                    # If page has no extracted text, treat as scanned image
                    if not text or len(text.strip()) < 20:
                        try:
                            # Render page as image for OCR
                            pil_image = page.to_image().original
                            img_byte_arr = io.BytesIO()
                            pil_image.save(img_byte_arr, format='PNG')
                            images_bytes.append(img_byte_arr.getvalue())
                            metadata["has_scanned_images"] = True
                        except Exception as e:
                            logger.warning(f"Could not convert page {page_num} to image: {e}")
        
        except Exception as e:
            raise ProcessingError(f"Failed to read PDF {file_path}: {e}")
        
        # Perform OCR on extracted images if needed
        ocr_text = self._perform_ocr_on_images(images_bytes)
        if ocr_text:
            all_text.append(f"\n--- Contenido de escaneo/OCR ---\n{ocr_text}")
        
        full_text = "\n".join(all_text) if all_text else ""
        return full_text, images_bytes, metadata
    
    def _read_image(self, file_path: Path) -> tuple[str, List[bytes], dict]:
        """Extract text and metadata from image."""
        try:
            # Read image
            image = Image.open(file_path)
            
            # Get basic metadata
            metadata = {
                "format": file_path.suffix.lower()[1:],  # Remove leading dot
                "size": image.size,
                "mode": image.mode
            }
            
            # Check image quality
            self._assess_image_quality(image)
            
            # Convert to bytes for vision API
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format=image.format or 'PNG')
            images_bytes = [img_byte_arr.getvalue()]
            
            # Perform OCR
            extracted_text = self._perform_ocr_on_image(file_path)
            
            metadata["has_text"] = bool(extracted_text and extracted_text.strip())
            metadata["has_scanned_images"] = True
            
            return extracted_text, images_bytes, metadata
        
        except Exception as e:
            raise ProcessingError(f"Failed to read image {file_path}: {e}")
    
    def _perform_ocr_on_image(self, file_path: Path) -> str:
        """Perform OCR on single image."""
        if not self.use_ocr or not self.ocr_reader:
            return ""
        
        try:
            result = self.ocr_reader.readtext(str(file_path))
            text = "\n".join([text for (_, text, conf) in result])
            return text
        except Exception as e:
            logger.warning(f"OCR failed on {file_path}: {e}")
            return ""
    
    def _perform_ocr_on_images(self, images_bytes: List[bytes]) -> str:
        """Perform OCR on list of image bytes."""
        if not self.use_ocr or not self.ocr_reader or not images_bytes:
            return ""
        
        all_text = []
        
        for idx, img_bytes in enumerate(images_bytes):
            try:
                # Convert bytes to numpy array for OCR
                nparr = cv2.imdecode(
                    __import__('numpy').frombuffer(img_bytes, __import__('numpy').uint8),
                    cv2.IMREAD_COLOR
                )
                
                if nparr is None:
                    # Try PIL for other formats
                    img = Image.open(io.BytesIO(img_bytes))
                    nparr = __import__('numpy').array(img)
                
                result = self.ocr_reader.readtext(nparr)
                text = "\n".join([text for (_, text, conf) in result])
                if text.strip():
                    all_text.append(text)
            
            except Exception as e:
                logger.warning(f"OCR failed on image {idx}: {e}")
                continue
        
        return "\n".join(all_text)
    
    def _assess_image_quality(self, image: Image.Image) -> None:
        """Assess image quality and log warnings."""
        width, height = image.size
        
        # Check resolution
        if width < 200 or height < 200:
            warning = DocumentQualityWarning(
                "image_quality",
                "Very low resolution image detected - may affect OCR accuracy"
            )
            self.quality_warnings.append(warning)
            logger.warning(warning)
        
        # Check if image appears to be mostly blank
        img_array = __import__('numpy').array(image.convert('L'))
        pixel_variance = img_array.var()
        
        if pixel_variance < 50:
            warning = DocumentQualityWarning(
                "image_content",
                "Image appears mostly blank or uniform - may not contain document content"
            )
            self.quality_warnings.append(warning)
            logger.warning(warning)
    
    def encode_image_to_base64(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 for API transmission."""
        return base64.standard_b64encode(image_bytes).decode('utf-8')
    
    def get_quality_warnings(self) -> List[DocumentQualityWarning]:
        """Get list of quality warnings from last read operation."""
        return self.quality_warnings
