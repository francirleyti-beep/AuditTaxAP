class AuditException(Exception):
    """Base exception for audit related errors."""
    pass

class SefazScraperException(AuditException):
    """Raised when there is an error scraping data from SEFAZ."""
    pass

class XMLReaderException(AuditException):
    """Raised when there is an error parsing the XML file."""
    pass

class RuleViolationException(AuditException):
    """Raised when a specific audit rule is violated."""
    pass
