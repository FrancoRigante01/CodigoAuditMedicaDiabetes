"""
Medical Document Ingestion and Classification Module (DEMO)

This module processes medical documents (PDF, images) and extracts/classifies
information for a diabetes medical audit use case.

WARNING: This is a DEMO with FICTIONAL DATA ONLY.
Do NOT use with real patient data without proper security and compliance review.
"""

from .processor import MedicalDocumentProcessor

__version__ = "0.1.0"

__all__ = ["MedicalDocumentProcessor"]
