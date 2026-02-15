import logging
import os
from typing import List, Tuple
from src.domain.dtos import AuditResultDTO, FiscalItemDTO, AuditDifference, InvoiceDTO
from src.domain.exceptions import AuditException
from src.infrastructure.xml_reader import XMLReader
from src.infrastructure.sefaz.scraper import SefazScraper
from src.core.auditor import AuditEngine
from src.core.invoice_validator import InvoiceValidator
from src.presentation.report_generator import ReportGenerator

class AuditService:
    """
    Serviço principal de auditoria.
    Orquestra: XML -> Scraper -> Auditoria -> Validação -> Relatório.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.xml_reader = XMLReader()
        self.scraper = SefazScraper()
        self.invoice_validator = InvoiceValidator()
        self.auditor = AuditEngine()
        self.reporter = ReportGenerator()

    def process_audit(self, xml_path: str, nfe_key: str = "") -> Tuple[str, List[AuditResultDTO], List[AuditDifference], InvoiceDTO]:
        """
        Executa fluxo completo de auditoria.
        Retorna (caminho_relatorio, lista_resultados_itens, lista_erros_consistencia).
        """
        self.logger.info(f"Iniciando auditoria para arquivo: {xml_path}")
        
        # 1. Ler XML (Agora retorna InvoiceDTO)
        try:
            invoice_dto = self.xml_reader.parse(xml_path)
            
            if not nfe_key:
                nfe_key = invoice_dto.access_key
            
            if not nfe_key:
                raise AuditException("Chave NFe não encontrada no XML e não fornecida.")
                
            self.logger.info(f"XML processado. Invoice Key: {nfe_key}. Itens: {len(invoice_dto.items)}")
            self.logger.info(f"XML processado. Invoice Key: {invoice_dto.access_key}. Itens: {len(invoice_dto.items)}")
            
        except Exception as e:
            self.logger.error(f"Erro na leitura do XML: {e}")
            raise

        # 2. Validar Consistência Interna
        consistency_errors = self.invoice_validator.validate(invoice_dto)
        if consistency_errors:
            self.logger.warning(f"Encontrados {len(consistency_errors)} erros de consistência interna no XML.")

        # 3. Buscar SEFAZ
        try:
            sefaz_items = self.scraper.fetch_memorial(invoice_dto.access_key, xml_path) # Passando xml_path como fallback/contexto se necessário
            if not sefaz_items:
                raise AuditException("Nenhum item retornado da SEFAZ.")
                
            self.logger.info(f"Dados SEFAZ obtidos. Itens: {len(sefaz_items)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar na SEFAZ: {e}")
            raise AuditException(f"Falha na comunicação com SEFAZ: {str(e)}")

        # 4. Auditar (Cruzamento XML x SEFAZ)
        try:
            audit_results = self._perform_audit(invoice_dto.items, sefaz_items)
        except Exception as e:
             self.logger.error(f"Erro na auditoria interna: {e}")
             raise AuditException(f"Falha no processamento da auditoria: {str(e)}")
        
        # 5. Gerar Relatório
        try:
            report_path = self.reporter.generate_csv(audit_results, consistency_errors)
            self.logger.info(f"Relatório gerado em: {report_path}")
            return report_path, audit_results, consistency_errors, invoice_dto
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            # Em caso de erro no relatório, retorna vazio mas com os dados processados importando para a API
            return "", audit_results, consistency_errors, invoice_dto

    def _perform_audit(self, xml_items: List[FiscalItemDTO], sefaz_items: List[FiscalItemDTO]) -> List[AuditResultDTO]:
        """Executa auditoria item a item."""
        sefaz_map = {item.item_index: item for item in sefaz_items}
        results = []
        
        for xml_item in xml_items:
            sefaz_item = sefaz_map.get(xml_item.item_index)
            
            if sefaz_item:
                result = self.auditor.audit_item(xml_item, sefaz_item)
                results.append(result)
            else:
                self.logger.warning(f"Item {xml_item.item_index} não encontrado na SEFAZ.")
                # Opcional: Adicionar resultado de erro
                
        return results
