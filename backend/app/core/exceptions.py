"""Custom exception hierarchy for MonitorMBG."""

from fastapi import HTTPException, status


class MonitorMBGException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(MonitorMBGException):
    """Raised when a requested entity is not found."""

    def __init__(self, entity: str, entity_id: str | int):
        super().__init__(f"{entity} with id '{entity_id}' not found")
        self.entity = entity
        self.entity_id = entity_id


class DuplicateEntityException(MonitorMBGException):
    """Raised when attempting to create a duplicate entity."""

    def __init__(self, entity: str, field: str, value: str):
        super().__init__(f"{entity} with {field}='{value}' already exists")


class CVProcessingException(MonitorMBGException):
    """Raised when computer vision processing fails."""
    pass


class NLPProcessingException(MonitorMBGException):
    """Raised when NLP processing fails."""
    pass


class ScoringException(MonitorMBGException):
    """Raised when scoring computation fails."""
    pass


# ── HTTP Exception Shortcuts ──

def not_found(detail: str = "Resource not found") -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def bad_request(detail: str = "Bad request") -> HTTPException:
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def unauthorized(detail: str = "Not authenticated") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
