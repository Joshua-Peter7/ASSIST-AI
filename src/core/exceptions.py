"""Application-level exceptions."""


class AppError(Exception):
    """Base exception for predictable application failures."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppError):
    """Raised when a requested resource does not exist."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class ValidationError(AppError):
    """Raised when input validation fails outside FastAPI schema validation."""

    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(message=message, status_code=422)
