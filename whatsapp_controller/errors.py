class WhatsAppError(Exception):
    """Base exception for WhatsApp Controller"""
    pass

class WhatsAppPermissionError(WhatsAppError):
    """Raised when macOS Accessibility permissions are missing."""
    pass

class WhatsAppNotRunningError(WhatsAppError):
    """Raised when WhatsApp cannot be launched."""
    pass

class ContactAmbiguousError(WhatsAppError):
    """Raised when a contact name maps to multiple ambiguous entities."""
    pass

class ContactNotFoundError(WhatsAppError):
    """Raised when the contact cannot be found in the UI."""
    pass

class ActionTimeoutError(WhatsAppError):
    """Raised when a UI automation action times out."""
    pass
