import logging
import os
from typing import List
from src.domain.dtos import AuditResultDTO, FiscalItemDTO
from src.domain.exceptions import AuditException
from src.infrastructure.xml_reader import XMLReader
from src.infrastructure.sefaz.scraper import SefazScraper
from src.core.auditor import AuditEngine
from src.presentation.report_generator import ReportGenerator

class AuditService:
    """
    Serviço principal de auditoria.
    Orquestra: XML -> Scraper -> Auditoria -> Relatório.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.xml_reader = XMLReader()
        self.scraper = SefazScraper()
        self.auditor = AuditEngine()
        self.reporter = ReportGenerator()

    def process_audit(self, xml_path: str, nfe_key: str = "") -> tuple[str, List[AuditResultDTO]]:
        """
        Executa fluxo completo de auditoria.
        Retorna (caminho_relatorio, lista_resultados).
        """
        self.logger.info(f"Iniciando auditoria para arquivo: {xml_path}")
        
        # 1. Ler XML
        try:
            detected_key, xml_items = self.xml_reader.parse(xml_path)
            if not nfe_key:
                nfe_key = detected_key
            
            if not nfe_key:
                raise AuditException("Chave NFe não encontrada no XML e não fornecida.")
                
            self.logger.info(f"XML processado. Itens: {len(xml_items)}. Chave: {nfe_key}")
            
        except Exception as e:
            self.logger.error(f"Erro na leitura do XML: {e}")
            raise

        # 2. Buscar SEFAZ
        try:
            sefaz_items = self.scraper.fetch_memorial(nfe_key)
            if not sefaz_items:
                raise AuditException("Nenhum item retornado da SEFAZ.")
                
            self.logger.info(f"Dados SEFAZ obtidos. Itens: {len(sefaz_items)}")
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar na SEFAZ: {e}")
            raise

        # 3. Auditar
        audit_results = self._perform_audit(xml_items, sefaz_items)
        
        # 4. Gerar Relatório
        try:
            report_path = self.reporter.generate_csv(audit_results)
            self.logger.info(f"Relatório gerado em: {report_path}")
            return report_path, audit_results
        except Exception as e:
            self.logger.error(f"Erro ao gerar relatório: {e}")
            raise

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
