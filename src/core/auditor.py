import logging
from typing import List, Optional
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO, AuditResultDTO
from src.core.audit_rules import AuditRuleChainBuilder

class AuditEngine:
    """
    Motor de auditoria que executa uma cadeia de regras.
    Refatorado para usar Strategy Pattern v3.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Carrega regras padrão via Builder
        builder = AuditRuleChainBuilder()
        self.rules = builder.build_standard_chain()
        self.logger.info(f"AuditEngine inicializado com {len(self.rules)} regras.")

    def audit_item(self, xml_item: FiscalItemDTO, sefaz_item: FiscalItemDTO) -> AuditResultDTO:
        """
        Audita um par de itens (XML vs SEFAZ) executando todas as regras.
        """
        differences = []
        
        # Executa cadeia de regras
        for rule in self.rules:
            try:
                diff = rule.validate(xml_item, sefaz_item)
                if diff:
                    differences.append(diff)
            except Exception as e:
                self.logger.error(f"Erro ao executar regra {type(rule).__name__}: {e}", exc_info=True)
                # Opcional: Adicionar erro sistêmico na lista de diferenças?
                
        is_compliant = (len(differences) == 0)
        
        return AuditResultDTO(
            item_index=xml_item.item_index,
            product_code=xml_item.product_code,
            is_compliant=is_compliant,
            differences=differences
        )
