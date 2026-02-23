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

from src.core.calculator import TaxCalculator

class MonetaryRule(AuditRule):
    def __init__(self, calculator: TaxCalculator, tolerance: Decimal = Decimal("0.05")):
        self.calculator = calculator
        self.tolerance = tolerance

    def validate(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> Optional[AuditDifference]:
        # 1. Identificar o cenário de tributação do XML para comparação direta
        has_st_xml = xml_item.icms_st_value > Decimal("0.00")
        
        if has_st_xml:
            xml_val = xml_item.icms_st_value
            label = "ICMS ST (Substituição Tributária)"
        else:
            xml_val = xml_item.tax_value
            label = "ICMS Normal (Operação Própria)"

        sefaz_val = sefaz_item.sefaz_tax_value
        
        # 2. Auditoria: XML vs SEFAZ (Validação de Conformidade)
        diff_xml_sefaz = abs(xml_val - sefaz_val)
        
        if diff_xml_sefaz > self.tolerance:
             if not has_st_xml and sefaz_val > 0:
                 msg = f"Divergência de Regime: XML indica apenas {label}, mas SEFAZ exige Antecipação/ST (R$ {sefaz_val:.2f})"
             else:
                 msg = f"Diferença de Valor: XML ({label}) R$ {xml_val:.2f} vs SEFAZ R$ {sefaz_val:.2f}"

             return AuditDifference(
                field="VALOR_IMPOSTO",
                xml_value=f"{label}: {xml_val:.2f}",
                sefaz_value=f"SEFAZ: {sefaz_val:.2f}",
                message=msg
            )

        # 3. Validação do Cálculo da SEFAZ (Recálculo Independente)
        # Determinar alíquota interna efetiva (Fallback para pICMSST se ALIQ INTERNA falhou no scraping)
        alq_intra = sefaz_item.tax_rate
        if alq_intra == Decimal("0.00") and sefaz_item.icms_st_rate > Decimal("0.00"):
            alq_intra = sefaz_item.icms_st_rate
        
        # Se não temos alíquota interna mínima razoável, não podemos validar o cálculo
        if alq_intra < Decimal("4.00"):
            return None

        # Determinar a base e o crédito conforme cenário fiscal (Plano A-I)
        base_produto = sefaz_item.amount_total
        benefit = sefaz_item.sefaz_benefit_value
        # pICMS interestadual
        alq_inter = sefaz_item.icms_interestadual_rate or xml_item.icms_interestadual_rate
        
        if xml_item.is_suframa_benefit and benefit > Decimal("0.00"):
            # Operação SUFRAMA: base líquida = produto - benefício (Passo D)
            base_liquida = base_produto - benefit
            # O CRÉDITO (Passo H) para abater do débito de ST é o próprio valor do benefício desonerado
            credito = benefit
        else:
            # Operação normal: base = produto, crédito = ICMS próprio
            base_liquida = base_produto
            credito = xml_item.tax_value
        
        # Recálculo matemático presumido
        calculated_val = self.calculator.calculate_icms_st(
            base_calc=base_liquida,
            mva=sefaz_item.mva_percent,
            alq_intra=alq_intra,
            valor_icms_proprio=credito
        )

        # Se o que a SEFAZ cobrou foge do cálculo matemático dela própria
        diff_calc_sefaz = abs(calculated_val - sefaz_val)
        if diff_calc_sefaz > self.tolerance:
             return AuditDifference(
                field="CALCULO_SEFAZ",
                xml_value=f"Esperado: {calculated_val:.2f}",
                sefaz_value=f"Cobrado: {sefaz_val:.2f}",
                message=f"O valor cobrado pela SEFAZ diverge do cálculo matemático presumido (MVA {sefaz_item.mva_percent}% | Alq {alq_intra}%)"
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
        # Se não há cobrança de imposto em nenhum dos lados, o produto é tratado como isento
        # e a conferência do valor do produto é desnecessária para a auditoria de ST/Antecipação.
        if xml_item.icms_st_value == Decimal("0.00") and sefaz_item.sefaz_tax_value == Decimal("0.00"):
            return None

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
        # Se tem ST, compara Base ST (vBCST) - Base Presumida
        if xml_item.icms_st_value > Decimal("0.00"):
            xml_base = xml_item.icms_st_base
            label = "Base ICMS ST (Presumida)"
        else:
            # Se não, compara Base Normal (vBC) - Operação Própria
            xml_base = xml_item.tax_base
            label = "Base ICMS Normal (Operação Própria)"

        sefaz_base = sefaz_item.tax_base
        
        diff = abs(xml_base - sefaz_base)
        if diff > self.tolerance:
             return AuditDifference(
                field="BASE_CALCULO",
                xml_value=f"{label}: {xml_base:.2f}",
                sefaz_value=f"SEFAZ: {sefaz_base:.2f}",
                message=f"Diferença de Base de Cálculo ({label}) > {self.tolerance}"
            )
        return None

from src.utils.config import Config

class AuditRuleChainBuilder:
    """Constrói a cadeia de regras de auditoria."""
    
    def build_standard_chain(self) -> List[AuditRule]:
        calculator = TaxCalculator()
        return [
            NCMRule(),
            CESTRule(),
            CFOPRule(),
            CSTRule(),
            OriginRule(), 
            ICMSOriginRule(),
            ProductValueRule(),
            TaxBaseRule(),
            SuframaBenefitRule(),
            AliquotRule(),
            MonetaryRule(calculator=calculator, tolerance=Config.AUDIT_TOLERANCE),
            MVARule()
        ]
