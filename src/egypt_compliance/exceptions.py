class ETAError(Exception):
    """Base error for the Egypt Compliance SDK."""


class ETAAuthenticationError(ETAError):
    """Raised when ETA identity login fails or an API call is unauthorized."""

    def __init__(
        self,
        message: str,
        *,
        error: str | None = None,
        error_description: str | None = None,
        status_code: int | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.error_description = error_description
        self.status_code = status_code


class ETAAPIError(ETAError):
    """Raised when an authenticated ETA API call returns a standard error."""

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        target: str | None = None,
        status_code: int | None = None,
        details: list | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.target = target
        self.status_code = status_code
        self.details = details or []
