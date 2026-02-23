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
        # Ambos já devem estar normalizados para 3 dígitos (ABB)
        xml_cst = xml_item.cst
        sefaz_cst = sefaz_item.cst
        
        if xml_cst != sefaz_cst:
            return AuditDifference(
                field="CST",
                xml_value=xml_cst,
                sefaz_value=sefaz_cst,
                message=f"Situação Tributária divergente (XML: {xml_cst} vs SEFAZ: {sefaz_cst})"
            )
        return None

class ICMSOriginRule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Validação simples de preenchimento por enquanto
        if not xml_item.icms_orig and xml_item.origin == "XML":
             return AuditDifference(
                field="ICMS_ORIG",
                xml_value="Vazio",
                sefaz_value="-",
                message="Origem da Mercadoria não preenchida no XML"
            )
        return None

class MonetaryRule(AuditRule):
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Lógica ST vs Próprio
        # Se houver destaque de ST no XML, comparamos o ST do XML com o Valor Calculado da SEFAZ
        # Caso contrário, comparamos o ICMS Próprio com o Valor Calculado da SEFAZ (Antecipação)
        
        if xml_item.icms_st_value > Decimal("0.00"):
            xml_val = xml_item.icms_st_value
            label = "ICMS ST"
        else:
            xml_val = xml_item.tax_value
            label = "ICMS Próprio"

        sefaz_val = sefaz_item.sefaz_tax_value
        
        diff = abs(xml_val - sefaz_val)
        if diff > self.tolerance:
             # Mensagem personalizada para falta de destaque de ST
             if xml_val == 0 and sefaz_val > 0:
                 msg = f"Item sem destaque de {label} no XML, mas com cobrança identificada pela SEFAZ (R$ {sefaz_val:.2f})"
             else:
                 msg = f"Diferença de valor ({label}) > {self.tolerance} (XML: {xml_val:.2f} vs SEFAZ: {sefaz_val:.2f})"

             return AuditDifference(
                field="TAX_VALUE",
                xml_value=f"{label}: {xml_val:.2f}",
                sefaz_value=f"SEFAZ: {sefaz_val:.2f}",
                message=msg
            )
        return None

class SuframaBenefitRule(AuditRule):
    """Compara o valor monetário do benefício SUFRAMA (vICMSDeson vs SEFAZ)."""
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        xml_val = xml_item.sefaz_benefit_value   # vICMSDeson do XML
        sefaz_val = sefaz_item.sefaz_benefit_value  # R$ extraído da SEFAZ
        
        # Se ambos são zero, não há benefício — compatível
        if xml_val == Decimal("0.00") and sefaz_val == Decimal("0.00"):
            return None
        
        diff = abs(xml_val - sefaz_val)
        if diff > self.tolerance:
            return AuditDifference(
                field="SUFRAMA_VALOR",
                xml_value=f"R$ {xml_val:.2f}",
                sefaz_value=f"R$ {sefaz_val:.2f}",
                message=f"Benefício SUFRAMA divergente (diff R$ {diff:.2f})"
            )
        return None

class MVARule(AuditRule):
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # XML pMVAST vs SEFAZ MVA Ajustada
        # Nota: Se o XML for CST 40, pMVAST costuma ser 0, mas a SEFAZ aplica MVA.
        # Nesses casos, a regra pode disparar, o que é CORRETO para indicar que a SEFAZ está tributando
        # algo que o contribuinte achou que era isento/desonerado sem ST.
        diff = abs(xml_item.mva_percent - sefaz_item.mva_percent)
        if diff > Decimal("0.01"):
            return AuditDifference(
                field="MVA %",
                xml_value=f"{xml_item.mva_percent:.2f}%",
                sefaz_value=f"{sefaz_item.mva_percent:.2f}%",
                message="Alíquota MVA divergente (ou aplicada pela SEFAZ)"
            )
        return None

class OriginRule(AuditRule):
    """Valida UF de Origem vs XML."""
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        if xml_item.origin_uf and sefaz_item.origin_uf:
            if xml_item.origin_uf.upper() != sefaz_item.origin_uf.upper():
                return AuditDifference(
                    field="UF_ORIGEM",
                    xml_value=xml_item.origin_uf,
                    sefaz_value=sefaz_item.origin_uf,
                    message="UF de Origem divergente"
                )
        return None

class AliquotRule(AuditRule):
    """Valida Alíquotas Interestadual e Interna."""
    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # 1. Interestadual
        if xml_item.icms_interestadual_rate > 0 and sefaz_item.icms_interestadual_rate > 0:
            if abs(xml_item.icms_interestadual_rate - sefaz_item.icms_interestadual_rate) > Decimal("0.01"):
                return AuditDifference(
                    field="ALIQ_INTERESTADUAL",
                    xml_value=f"{xml_item.icms_interestadual_rate:.2f}%",
                    sefaz_value=f"{sefaz_item.icms_interestadual_rate:.2f}%",
                    message="Alíquota Interestadual divergente"
                )
        
        # 2. Interna (AP)
        # No XML, a interna de destino pode vir em pICMSST ou pICMS (se for operação interna)
        xml_internal = xml_item.icms_st_rate if xml_item.icms_st_rate > 0 else xml_item.tax_rate
        if xml_internal > 0 and sefaz_item.tax_rate > 0:
            if abs(xml_internal - sefaz_item.tax_rate) > Decimal("0.01"):
                 return AuditDifference(
                    field="ALIQ_INTERNA",
                    xml_value=f"{xml_internal:.2f}%",
                    sefaz_value=f"{sefaz_item.tax_rate:.2f}%",
                    message="Alíquota Interna divergente"
                )
        return None

class ProductValueRule(AuditRule):
    """(RF05) Valida Valor do Produto (vProd vs A) VALOR PRODUTO)."""
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # XML vProd vs SEFAZ Amount Total (que agora é extraído do A) VALOR PRODUTO)
        diff = abs(xml_item.amount_total - sefaz_item.amount_total)
        if diff > self.tolerance:
            return AuditDifference(
                field="VALOR_PRODUTO",
                xml_value=f"R$ {xml_item.amount_total:.2f}",
                sefaz_value=f"R$ {sefaz_item.amount_total:.2f}",
                message=f"Valor do Produto divergente (> {self.tolerance})"
            )
        return None

class TaxBaseRule(AuditRule):
    """(RF05 Intermediária) Valida Base de Cálculo."""
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # Se tem ST, compara Base ST (vBCST)
        if xml_item.icms_st_value > Decimal("0.00"):
            xml_base = xml_item.icms_st_base
            label = "Base ST"
        else:
            # Se não, compara Base Normal (vBC) - Regra de Antecipação
            xml_base = xml_item.tax_base
            label = "Base ICMS"

        sefaz_base = sefaz_item.tax_base
        
        diff = abs(xml_base - sefaz_base)
        if diff > self.tolerance:
             return AuditDifference(
                field="BASE_CALCULO",
                xml_value=f"{label}: {xml_base:.2f}",
                sefaz_value=f"SEFAZ: {sefaz_base:.2f}",
                message=f"Diferença de Base de Cálculo > {self.tolerance}"
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
            OriginRule(), # Nova regra
            ICMSOriginRule(),
            ProductValueRule(),
            TaxBaseRule(),
            SuframaBenefitRule(),
            AliquotRule(),
            MonetaryRule(tolerance=Config.AUDIT_TOLERANCE),
            MVARule()
        ]
