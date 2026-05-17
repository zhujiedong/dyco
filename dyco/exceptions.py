class DycoError(Exception):
    """Base exception for DYCO."""
    pass

class NoFilesFoundError(DycoError):
    """Raised when no files match the discovery pattern."""
    pass
