from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, List
from src.domain.dtos import FiscalItemDTO, AuditDifference, AuditResultDTO

class AuditRule(ABC):
    """Interface para regras de auditoria."""
    
    @abstractmethod
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        """
        Retorna uma AuditDifference se houver violação, ou None.
        """
        pass

class NCMRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        if xml_item.ncm != sefaz_item.ncm:
            return AuditDifference(
                field="NCM",
                xml_value=xml_item.ncm,
                sefaz_value=sefaz_item.ncm,
                message="NCM divergente"
            )
        return None

class CESTRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Normalização básica: remover pontos
        xml_cest = xml_item.cest.replace(".", "")
        sefaz_cest = sefaz_item.cest.replace(".", "")
        if xml_cest != sefaz_cest:
            return AuditDifference(
                field="CEST",
                xml_value=xml_item.cest,
                sefaz_value=sefaz_item.cest,
                message="CEST divergente"
            )
        return None

class CFOPRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        if xml_item.cfop != sefaz_item.cfop:
             return AuditDifference(
                field="CFOP",
                xml_value=xml_item.cfop,
                sefaz_value=sefaz_item.cfop,
                message="CFOP divergente"
            )
        return None

class CSTRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Normalização para 3 dígitos
        xml_cst = xml_item.cst.zfill(3)
        sefaz_cst = sefaz_item.cst.zfill(3)
        
        if xml_cst != sefaz_cst:
            return AuditDifference(
                field="CST",
                xml_value=xml_cst,
                sefaz_value=sefaz_cst,
                message="CST divergente"
            )
        return None

class MonetaryRule(AuditRule):
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Comparar Base de Cálculo ou Valor Imposto?
        # A regra geral é comparar o Valor a Recolher (Tax Value)
        # Mas podemos validar Base e Alíquota também se desejado.
        # Focaremos no Tax Value (ICMS ST ou Antecipado)
        
        diff = abs(xml_item.tax_value - sefaz_item.tax_value)
        if diff > self.tolerance:
             return AuditDifference(
                field="TAX_VALUE",
                xml_value=f"{xml_item.tax_value:.2f}",
                sefaz_value=f"{sefaz_item.tax_value:.2f}",
                message=f"Diferença de valor > {self.tolerance}"
            )
        return None

class SuframaBenefitRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        if xml_item.is_suframa_benefit != sefaz_item.is_suframa_benefit:
            return AuditDifference(
                field="SUFRAMA",
                xml_value=str(xml_item.is_suframa_benefit),
                sefaz_value=str(sefaz_item.is_suframa_benefit),
                message="Benefício SUFRAMA inconsistente"
            )
        return None

class MVARule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        diff = abs(xml_item.mva_percent - sefaz_item.mva_percent)
        if diff > Decimal("0.01"): # Tolerância pequena para percentual
            return AuditDifference(
                field="MVA %",
                xml_value=f"{xml_item.mva_percent:.2f}",
                sefaz_value=f"{sefaz_item.mva_percent:.2f}",
                message="MVA divergente"
            )
        return None

from src.utils.config import Config

class AuditRuleChainBuilder:
    """Constrói a cadeia de regras de auditoria."""
    
    def build_standard_chain(self) -> List[AuditRule]:
        return [
            NCMRule(),
            CESTRule(),
            CFOPRule(),
            CSTRule(),
            SuframaBenefitRule(),
            MonetaryRule(tolerance=Config.AUDIT_TOLERANCE),
            MVARule()
        ]
