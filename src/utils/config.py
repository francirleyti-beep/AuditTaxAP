import os
from decimal import Decimal
from typing import Optional
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env se existir
load_dotenv()

class Config:
    """
    Centraliza as configurações da aplicação.
    Carrega valores de variáveis de ambiente ou utiliza defaults.
    """
    
    # SEFAZ
    SEFAZ_URL: str = os.getenv("SEFAZ_URL", "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php")
    SEFAZ_TIMEOUT: int = int(os.getenv("SEFAZ_TIMEOUT", "30"))
    HEADLESS_MODE: bool = os.getenv("HEADLESS_MODE", "False").lower() == "true"
    
    # Auditoria
    AUDIT_TOLERANCE: Decimal = Decimal(os.getenv("AUDIT_TOLERANCE", "0.05"))
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()

    @classmethod
    def get_audit_tolerance(cls) -> Decimal:
        return cls.AUDIT_TOLERANCE

    @classmethod
    def is_headless(cls) -> bool:
        return cls.HEADLESS_MODE
