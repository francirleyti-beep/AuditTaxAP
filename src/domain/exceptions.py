class AuditTaxException(Exception):
    """Exceção base do sistema."""
    pass

class XMLParseException(AuditTaxException):
    """Erro ao parsear XML."""
    pass

class SefazScraperException(AuditTaxException):
    """Erro no scraping da SEFAZ."""
    pass

class AuditException(AuditTaxException):
    """Erro na auditoria."""
    pass

class ReportGenerationException(AuditTaxException):
    """Erro na geração de relatório."""
    pass
