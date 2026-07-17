"""
Error handling and logging module for document processing.
Provides comprehensive error management and optional debug logging.
"""

import logging
import logging.handlers
import sys
import traceback
from typing import Optional, Callable
from datetime import datetime
from pathlib import Path

from .models import ProcessingError


class ProcessingLogger:
    """Manages logging configuration for document processing."""
    
    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[str] = None,
        enable_debug: bool = False
    ):
        """
        Initialize logging configuration.
        
        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Optional file path for log output
            enable_debug: Enable debug logging (verbose output)
        """
        self.log_level = log_level
        self.log_file = log_file
        self.enable_debug = enable_debug
        self._configure_logging()
    
    def _configure_logging(self):
        """Configure root logger with appropriate handlers."""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG if self.enable_debug else logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler (always enabled)
        console_handler = logging.StreamHandler(sys.stdout)
        console_level = logging.DEBUG if self.enable_debug else self._parse_level(self.log_level)
        console_handler.setLevel(console_level)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler (if log_file specified)
        if self.log_file:
            try:
                log_path = Path(self.log_file)
                log_path.parent.mkdir(parents=True, exist_ok=True)
                
                file_handler = logging.handlers.RotatingFileHandler(
                    self.log_file,
                    maxBytes=10*1024*1024,
                    backupCount=5
                )
                file_handler.setLevel(logging.DEBUG)
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                )
                file_handler.setFormatter(file_formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                console_handler.emit(
                    logging.LogRecord(
                        "root", logging.WARNING, "",
                        0, f"Failed to setup file logging: {e}", (), None
                    )
                )
    
    @staticmethod
    def _parse_level(level_str: str) -> int:
        """Parse log level string to logging constant."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return levels.get(level_str.upper(), logging.INFO)
    
    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance for a module."""
        return logging.getLogger(name)


class ErrorHandler:
    """Handles errors and provides meaningful error messages."""
    
    # Error message templates
    ERROR_MESSAGES = {
        "file_not_found": "File not found: {path}. Please check the file path.",
        "unsupported_format": "Unsupported file format: {format}. Supported: PDF, JPG, PNG.",
        "file_too_large": "File too large: {size}MB. Maximum allowed: {max_size}MB.",
        "invalid_document_type": "Invalid document type: {type}. Must be one of: {valid_types}.",
        "extraction_failed": "Failed to extract fields from document: {reason}",
        "classification_failed": "Failed to classify document: {reason}",
        "validation_failed": "Document validation failed: {reason}",
        "api_error": "API error: {message}. Please check your API key and try again.",
        "invalid_json": "Failed to parse JSON response: {reason}",
        "quality_warning": "Document quality issue detected: {issue}",
        "missing_field": "Required field missing: {field}",
        "low_confidence": "Low confidence extraction for field '{field}': {confidence}%",
    }
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize error handler."""
        self.logger = logger or logging.getLogger(__name__)
        self.errors = []
        self.warnings = []
    
    def handle_error(
        self,
        error_type: str,
        error_details: dict,
        log_traceback: bool = True,
        raise_exception: bool = True
    ) -> Optional[str]:
        """Handle an error with message formatting and logging."""
        message_template = self.ERROR_MESSAGES.get(
            error_type,
            f"Unknown error type: {error_type}"
        )
        
        try:
            error_message = message_template.format(**error_details)
        except KeyError as e:
            error_message = f"Error formatting message: {message_template} - {str(e)}"
        
        # Log the error
        self.logger.error(error_message)
        
        # Log traceback if requested
        if log_traceback:
            self.logger.debug(traceback.format_exc())
        
        # Store error for audit trail
        self.errors.append({
            "type": error_type,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "details": error_details
        })
        
        # Raise exception if requested
        if raise_exception:
            raise ProcessingError(error_message)
        
        return error_message
    
    def handle_warning(
        self,
        warning_type: str,
        warning_details: dict,
        log_level: str = "WARNING"
    ) -> str:
        """Handle a warning with message formatting and logging."""
        message_template = self.ERROR_MESSAGES.get(
            warning_type,
            f"Unknown warning type: {warning_type}"
        )
        
        try:
            warning_message = message_template.format(**warning_details)
        except KeyError as e:
            warning_message = f"Error formatting message: {message_template} - {str(e)}"
        
        # Log the warning
        log_func = getattr(self.logger, log_level.lower(), self.logger.warning)
        log_func(warning_message)
        
        # Store warning for audit trail
        self.warnings.append({
            "type": warning_type,
            "message": warning_message,
            "timestamp": datetime.now().isoformat(),
            "details": warning_details
        })
        
        return warning_message
    
    def get_error_summary(self) -> dict:
        """Get summary of all errors and warnings encountered."""
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings
        }
    
    def clear_history(self):
        """Clear error and warning history."""
        self.errors.clear()
        self.warnings.clear()


class SafeExecutor:
    """Wraps functions with error handling and retry logic."""
    
    def __init__(
        self,
        error_handler: ErrorHandler,
        max_retries: int = 1,
        retry_delay: float = 1.0
    ):
        """Initialize safe executor."""
        self.error_handler = error_handler
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.logger = logging.getLogger(__name__)
    
    def execute(
        self,
        func: Callable,
        *args,
        error_type: str = "extraction_failed",
        return_default: Optional[object] = None,
        **kwargs
    ):
        """Execute a function with error handling and optional retries."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.debug(
                    f"Executing {func.__name__} "
                    f"(attempt {attempt + 1}/{self.max_retries + 1})"
                )
                return func(*args, **kwargs)
            
            except ProcessingError as e:
                last_exception = e
                self.logger.error(f"Processing error in {func.__name__}: {str(e)}")
                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
                    continue
            
            except Exception as e:
                last_exception = e
                self.logger.error(
                    f"Unexpected error in {func.__name__}: {str(e)}"
                )
                self.logger.debug(traceback.format_exc())
                if attempt < self.max_retries:
                    import time
                    time.sleep(self.retry_delay)
                    continue
        
        # All retries exhausted
        self.logger.error(
            f"Failed to execute {func.__name__} after {self.max_retries + 1} attempts"
        )
        
        if return_default is not None:
            return return_default
        
        # Raise the last exception
        raise last_exception
