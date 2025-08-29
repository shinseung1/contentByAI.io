"""Custom exceptions and error handling."""

from typing import Any, Dict, Optional
from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for different types of errors."""
    
    # Configuration errors
    CONFIG_INVALID = "CONFIG_INVALID"
    CONFIG_MISSING = "CONFIG_MISSING"
    
    # Authentication errors
    AUTH_FAILED = "AUTH_FAILED"
    AUTH_EXPIRED = "AUTH_EXPIRED"
    AUTH_INVALID = "AUTH_INVALID"
    
    # API errors
    API_CONNECTION_FAILED = "API_CONNECTION_FAILED"
    API_RATE_LIMITED = "API_RATE_LIMITED"
    API_QUOTA_EXCEEDED = "API_QUOTA_EXCEEDED"
    API_INVALID_REQUEST = "API_INVALID_REQUEST"
    API_SERVER_ERROR = "API_SERVER_ERROR"
    
    # Content errors
    CONTENT_GENERATION_FAILED = "CONTENT_GENERATION_FAILED"
    CONTENT_VALIDATION_FAILED = "CONTENT_VALIDATION_FAILED"
    CONTENT_NOT_FOUND = "CONTENT_NOT_FOUND"
    
    # Bundle errors
    BUNDLE_CREATION_FAILED = "BUNDLE_CREATION_FAILED"
    BUNDLE_NOT_FOUND = "BUNDLE_NOT_FOUND"
    BUNDLE_INVALID = "BUNDLE_INVALID"
    
    # Publishing errors
    PUBLISH_FAILED = "PUBLISH_FAILED"
    PUBLISH_UNAUTHORIZED = "PUBLISH_UNAUTHORIZED"
    PUBLISH_QUOTA_EXCEEDED = "PUBLISH_QUOTA_EXCEEDED"
    
    # Media errors
    MEDIA_UPLOAD_FAILED = "MEDIA_UPLOAD_FAILED"
    MEDIA_NOT_FOUND = "MEDIA_NOT_FOUND"
    MEDIA_INVALID_FORMAT = "MEDIA_INVALID_FORMAT"
    
    # Quality errors
    QUALITY_CHECK_FAILED = "QUALITY_CHECK_FAILED"
    QUALITY_THRESHOLD_NOT_MET = "QUALITY_THRESHOLD_NOT_MET"
    
    # Database errors
    DB_CONNECTION_FAILED = "DB_CONNECTION_FAILED"
    DB_OPERATION_FAILED = "DB_OPERATION_FAILED"


class AIWriterError(Exception):
    """Base exception for AIWriter application."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.cause = cause

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "cause": str(self.cause) if self.cause else None
        }


class RetryableError(AIWriterError):
    """Error that can be retried."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode,
        retry_after: Optional[int] = None,
        max_retries: int = 5,
        **kwargs
    ):
        super().__init__(message, error_code, **kwargs)
        self.retry_after = retry_after
        self.max_retries = max_retries


class FatalError(AIWriterError):
    """Fatal error that should not be retried."""
    pass


class ConfigurationError(FatalError):
    """Configuration related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.CONFIG_INVALID, **kwargs)


class AuthenticationError(FatalError):
    """Authentication related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.AUTH_FAILED, **kwargs)


class APIError(RetryableError):
    """API related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, **kwargs):
        error_code = self._get_error_code_from_status(status_code)
        super().__init__(message, error_code, **kwargs)
        self.status_code = status_code

    @staticmethod
    def _get_error_code_from_status(status_code: Optional[int]) -> ErrorCode:
        """Get error code from HTTP status code."""
        if status_code is None:
            return ErrorCode.API_CONNECTION_FAILED
        elif status_code == 401:
            return ErrorCode.AUTH_FAILED
        elif status_code == 403:
            return ErrorCode.AUTH_INVALID
        elif status_code == 429:
            return ErrorCode.API_RATE_LIMITED
        elif 400 <= status_code < 500:
            return ErrorCode.API_INVALID_REQUEST
        elif status_code >= 500:
            return ErrorCode.API_SERVER_ERROR
        else:
            return ErrorCode.API_CONNECTION_FAILED


class ContentGenerationError(RetryableError):
    """Content generation related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.CONTENT_GENERATION_FAILED, **kwargs)


class BundleError(AIWriterError):
    """Bundle related errors."""
    
    def __init__(self, message: str, bundle_id: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCode.BUNDLE_CREATION_FAILED, **kwargs)
        self.bundle_id = bundle_id


class PublishingError(RetryableError):
    """Publishing related errors."""
    
    def __init__(self, message: str, platform: Optional[str] = None, **kwargs):
        super().__init__(message, ErrorCode.PUBLISH_FAILED, **kwargs)
        self.platform = platform


class QualityCheckError(AIWriterError):
    """Quality check related errors."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(message, ErrorCode.QUALITY_CHECK_FAILED, **kwargs)