"""Domain-level exceptions that are framework-agnostic.

The API layer is responsible for translating these into HTTP responses.
"""


class DomainError(Exception):
    """Base class for all domain exceptions."""


class NotFoundError(DomainError):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, identifier: object) -> None:
        """
        Arg: resource - name of the resource type; identifier - lookup value.
        Operation: builds a human-readable message from resource and identifier.
        Return: NotFoundError instance.
        """
        super().__init__(f"{resource} '{identifier}' not found.")
        self.resource = resource
        self.identifier = identifier


class ForbiddenError(DomainError):
    """Raised when the requesting user lacks permission for the action."""

    def __init__(self, reason: str = "Access denied.") -> None:
        """
        Arg: reason - optional human-readable explanation.
        Operation: stores the reason as the exception message.
        Return: ForbiddenError instance.
        """
        super().__init__(reason)


class ConflictError(DomainError):
    """Raised when an operation conflicts with current resource state."""

    def __init__(self, detail: str) -> None:
        """
        Arg: detail - description of the conflict.
        Operation: stores detail as the exception message.
        Return: ConflictError instance.
        """
        super().__init__(detail)


class ValidationError(DomainError):
    """Raised when a request is well-formed but asks for something inconsistent.

    Falls through to the generic DomainError handler, which answers 422.
    """

    def __init__(self, detail: str) -> None:
        """
        Arg: detail - description of what does not add up.
        Operation: stores detail as the exception message.
        Return: ValidationError instance.
        """
        super().__init__(detail)
