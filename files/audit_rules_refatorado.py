# src/core/audit_rules.py
"""
Regras de auditoria usando Strategy Pattern e Chain of Responsibility.
Cada regra é independente e testável.
"""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import List, Optional
from src.domain.dtos import FiscalItemDTO, AuditDifference


class AuditRule(ABC):
    """
    Classe base para regras de auditoria.
    
    Implementa Chain of Responsibility: cada regra pode encadear a próxima.
    """
    
    def __init__(self, tolerance: Decimal = Decimal("0.00")):
        self.tolerance = tolerance
        self.next_rule: Optional['AuditRule'] = None
    
    def set_next(self, rule: 'AuditRule') -> 'AuditRule':
        """
        Encadeia a próxima regra.
        
        Returns:
            A próxima regra (para permitir chaining fluente)
        """
        self.next_rule = rule
        return rule
    
    def check(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        """
        Executa a verificação e propaga para próxima regra se houver.
        
        Args:
            xml_item: Item extraído do XML
            sefaz_item: Item extraído da SEFAZ
            
        Returns:
            Lista de divergências encontradas
        """
        differences = self._execute(xml_item, sefaz_item)
        
        if self.next_rule:
            differences.extend(self.next_rule.check(xml_item, sefaz_item))
        
        return differences
    
    @abstractmethod
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        """
        Implementa a lógica específica da regra.
        
        Este método deve ser sobrescrito pelas subclasses.
        """
        pass


# =============================================================================
# REGRAS CADASTRAIS
# =============================================================================

class NCMRule(AuditRule):
    """Verifica concordância do código NCM."""
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        if xml_item.ncm != sefaz_item.ncm:
            return [AuditDifference(
                field="NCM",
                xml_value=xml_item.ncm,
                sefaz_value=sefaz_item.ncm,
                message="Divergência de NCM"
            )]
        return []


class CESTRule(AuditRule):
    """Verifica concordância do código CEST."""
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        # CEST pode ser vazio em alguns casos
        if xml_item.cest and sefaz_item.cest and xml_item.cest != sefaz_item.cest:
            return [AuditDifference(
                field="CEST",
                xml_value=xml_item.cest,
                sefaz_value=sefaz_item.cest,
                message="Divergência de CEST"
            )]
        return []


class CFOPRule(AuditRule):
    """Verifica concordância do CFOP."""
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        if xml_item.cfop != sefaz_item.cfop:
            return [AuditDifference(
                field="CFOP",
                xml_value=xml_item.cfop,
                sefaz_value=sefaz_item.cfop,
                message="Divergência de CFOP"
            )]
        return []


class CSTRule(AuditRule):
    """
    Verifica concordância do CST.
    
    Normaliza CST removendo zeros à esquerda antes da comparação.
    Ex: "00" e "0" são considerados iguais.
    """
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        # Normalizar: remover zeros à esquerda
        cst_xml = xml_item.cst.lstrip("0") if xml_item.cst else ""
        cst_sefaz = sefaz_item.cst.lstrip("0") if sefaz_item.cst else ""
        
        if cst_xml != cst_sefaz:
            return [AuditDifference(
                field="CST",
                xml_value=cst_xml,
                sefaz_value=cst_sefaz,
                message="Divergência de CST"
            )]
        return []


# =============================================================================
# REGRAS MONETÁRIAS
# =============================================================================

class MonetaryRule(AuditRule):
    """
    Regra genérica para verificação de valores monetários.
    
    Permite tolerância configurável para pequenas diferenças de arredondamento.
    """
    
    def __init__(self, field_name: str, field_attr: str, tolerance: Decimal = Decimal("0.05")):
        """
        Args:
            field_name: Nome amigável do campo (para mensagem)
            field_attr: Nome do atributo no DTO
            tolerance: Tolerância máxima aceitável
        """
        super().__init__(tolerance)
        self.field_name = field_name
        self.field_attr = field_attr
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        val_xml = getattr(xml_item, self.field_attr)
        val_sefaz = getattr(sefaz_item, self.field_attr)
        
        delta = abs(val_xml - val_sefaz)
        
        if delta > self.tolerance:
            return [AuditDifference(
                field=self.field_name,
                xml_value=str(val_xml),
                sefaz_value=str(val_sefaz),
                message=f"Divergência de {self.field_name} (Diferença: R$ {delta:.2f})"
            )]
        return []


class TaxBaseRule(MonetaryRule):
    """Verifica concordância da Base de Cálculo."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        super().__init__("Base de Cálculo", "tax_base", tolerance)


class TaxValueRule(MonetaryRule):
    """Verifica concordância do Valor do ICMS."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        super().__init__("Valor ICMS", "tax_value", tolerance)


class MVARule(MonetaryRule):
    """Verifica concordância do MVA %."""
    
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        super().__init__("MVA %", "mva_percent", tolerance)


# =============================================================================
# REGRAS ESPECIAIS
# =============================================================================

class SuframaBenefitRule(AuditRule):
    """
    Verifica consistência do benefício SUFRAMA.
    
    Se ambos indicam SUFRAMA, devem ter valores zerados.
    """
    
    def _execute(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> List[AuditDifference]:
        differences = []
        
        # Se ambos indicam SUFRAMA
        if xml_item.is_suframa_benefit and sefaz_item.is_suframa_benefit:
            # Valor do ICMS deve ser zero ou próximo de zero
            if xml_item.tax_value > Decimal("0.10") or sefaz_item.tax_value > Decimal("0.10"):
                differences.append(AuditDifference(
                    field="Benefício SUFRAMA",
                    xml_value=f"SUFRAMA (ICMS: {xml_item.tax_value})",
                    sefaz_value=f"SUFRAMA (ICMS: {sefaz_item.tax_value})",
                    message="Item com SUFRAMA deveria ter ICMS zerado"
                ))
        
        # Se apenas um indica SUFRAMA
        elif xml_item.is_suframa_benefit != sefaz_item.is_suframa_benefit:
            differences.append(AuditDifference(
                field="Benefício SUFRAMA",
                xml_value="Sim" if xml_item.is_suframa_benefit else "Não",
                sefaz_value="Sim" if sefaz_item.is_suframa_benefit else "Não",
                message="Divergência na aplicação do benefício SUFRAMA"
            ))
        
        return differences


# =============================================================================
# BUILDER PARA CONSTRUIR CADEIA DE REGRAS
# =============================================================================

class AuditRuleChainBuilder:
    """
    Builder para construir cadeias de regras de auditoria.
    
    Uso:
        builder = AuditRuleChainBuilder(tolerance=Decimal("0.05"))
        chain = builder.with_cadastral_rules().with_monetary_rules().build()
        differences = chain.check(xml_item, sefaz_item)
    """
    
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance
        self.rules: List[AuditRule] = []
    
    def with_cadastral_rules(self) -> 'AuditRuleChainBuilder':
        """Adiciona regras cadastrais (NCM, CEST, CFOP, CST)."""
        self.rules.extend([
            NCMRule(),
            CESTRule(),
            CFOPRule(),
            CSTRule(),
        ])
        return self
    
    def with_monetary_rules(self) -> 'AuditRuleChainBuilder':
        """Adiciona regras monetárias (Base, Valor, MVA)."""
        self.rules.extend([
            TaxBaseRule(self.tolerance),
            TaxValueRule(self.tolerance),
            MVARule(self.tolerance),
        ])
        return self
    
    def with_special_rules(self) -> 'AuditRuleChainBuilder':
        """Adiciona regras especiais (SUFRAMA, etc)."""
        self.rules.append(SuframaBenefitRule())
        return self
    
    def with_custom_rule(self, rule: AuditRule) -> 'AuditRuleChainBuilder':
        """Adiciona uma regra customizada."""
        self.rules.append(rule)
        return self
    
    def build(self) -> AuditRule:
        """
        Constrói a cadeia de regras.
        
        Returns:
            Primeira regra da cadeia (que encadeia todas as outras)
        
        Raises:
            ValueError: Se nenhuma regra foi adicionada
        """
        if not self.rules:
            raise ValueError("Nenhuma regra foi adicionada à cadeia")
        
        # Encadear regras
        for i in range(len(self.rules) - 1):
            self.rules[i].set_next(self.rules[i + 1])
        
        # Retornar primeira regra
        return self.rules[0]


# =============================================================================
# EXEMPLO DE USO
# =============================================================================

if __name__ == "__main__":
    # Construir cadeia completa
    builder = AuditRuleChainBuilder(tolerance=Decimal("0.05"))
    rule_chain = (builder
                  .with_cadastral_rules()
                  .with_monetary_rules()
                  .with_special_rules()
                  .build())
    
    # Criar itens de teste
    xml_item = FiscalItemDTO(
        origin="XML",
        item_index=1,
        product_code="PROD-001",
        ncm="22021000",
        cest="0300700",
        cfop="6110",
        cst="040",
        amount_total=Decimal("100.00"),
        tax_base=Decimal("100.00"),
        tax_rate=Decimal("18.00"),
        tax_value=Decimal("18.00"),
        mva_percent=Decimal("30.00"),
        is_suframa_benefit=False
    )
    
    sefaz_item = FiscalItemDTO(
        origin="SEFAZ",
        item_index=1,
        product_code="PROD-001",
        ncm="22021000",
        cest="0300700",
        cfop="6110",
        cst="040",
        amount_total=Decimal("0.00"),
        tax_base=Decimal("100.00"),
        tax_rate=Decimal("18.00"),
        tax_value=Decimal("18.03"),  # Pequena diferença
        mva_percent=Decimal("30.00"),
        is_suframa_benefit=False
    )
    
    # Executar verificação
    differences = rule_chain.check(xml_item, sefaz_item)
    
    # Resultado
    if differences:
        print(f"Encontradas {len(differences)} divergências:")
        for diff in differences:
            print(f"  - {diff.message}")
    else:
        print("✓ Nenhuma divergência encontrada (item conforme)")
