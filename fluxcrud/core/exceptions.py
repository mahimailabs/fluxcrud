class FluxCRUDError(Exception):
    """Base exception for FluxCRUD."""

    pass


class ConfigurationError(FluxCRUDError):
    """Raised when there is a configuration error."""

    pass


class DatabaseError(FluxCRUDError):
    """Raised when a database error occurs."""

    pass


class NotFoundError(FluxCRUDError):
    """Raised when a record is not found."""

    pass


class ValidationError(FluxCRUDError):
    """Raised when data validation fails."""

    pass
