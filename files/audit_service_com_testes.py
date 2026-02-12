# src/services/audit_service.py
"""
Camada de serviço que orquestra o fluxo completo de auditoria.

Benefícios:
- Separação de responsabilidades
- Fácil de testar (mock de dependências)
- Reutilizável em diferentes contextos (CLI, API, GUI)
"""

import logging
from pathlib import Path
from typing import List, Optional
from decimal import Decimal

from src.domain.dtos import FiscalItemDTO, AuditResultDTO
from src.domain.exceptions import (
    XMLParseException,
    SefazScraperException,
    AuditException,
    ReportGenerationException
)
from src.infrastructure.xml_reader import XMLReader
from src.infrastructure.sefaz_scraper import SefazScraper
from src.core.auditor import AuditEngine
from src.presentation.report_generator import ReportGenerator


class AuditService:
    """
    Serviço de auditoria fiscal.
    
    Orquestra o fluxo completo:
    1. Leitura do XML
    2. Busca no memorial SEFAZ
    3. Auditoria item por item
    4. Geração de relatório
    """
    
    def __init__(
        self,
        xml_reader: Optional[XMLReader] = None,
        scraper: Optional[SefazScraper] = None,
        auditor: Optional[AuditEngine] = None,
        reporter: Optional[ReportGenerator] = None,
        tolerance: Decimal = Decimal("0.05")
    ):
        """
        Args:
            xml_reader: Leitor de XML (usa padrão se None)
            scraper: Scraper SEFAZ (usa padrão se None)
            auditor: Engine de auditoria (usa padrão se None)
            reporter: Gerador de relatórios (usa padrão se None)
            tolerance: Tolerância monetária
        """
        self.xml_reader = xml_reader or XMLReader()
        self.scraper = scraper or SefazScraper()
        self.auditor = auditor or AuditEngine(tolerance=tolerance)
        self.reporter = reporter or ReportGenerator()
        self.logger = logging.getLogger(__name__)
    
    def audit_nfe(
        self,
        xml_path: str,
        nfe_key: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> str:
        """
        Executa auditoria completa de uma NFe.
        
        Args:
            xml_path: Caminho do arquivo XML
            nfe_key: Chave de acesso (usa do XML se None)
            output_path: Caminho do relatório (auto se None)
            
        Returns:
            Path do relatório gerado
            
        Raises:
            XMLParseException: Erro ao ler XML
            SefazScraperException: Erro no scraping
            AuditException: Erro na auditoria
            ReportGenerationException: Erro ao gerar relatório
        """
        self.logger.info("="*60)
        self.logger.info("INICIANDO AUDITORIA FISCAL")
        self.logger.info("="*60)
        
        try:
            # Etapa 1: Ler XML
            key, xml_items = self._read_xml(xml_path)
            nfe_key = nfe_key or key
            
            if not nfe_key:
                raise AuditException("Chave NFe não encontrada no XML")
            
            # Etapa 2: Buscar SEFAZ
            sefaz_items = self._fetch_sefaz(nfe_key)
            
            # Etapa 3: Auditar
            results = self._audit_items(xml_items, sefaz_items)
            
            # Etapa 4: Gerar relatório
            report_path = self._generate_report(results, output_path)
            
            # Resumo
            self._log_summary(results)
            
            self.logger.info("="*60)
            self.logger.info("AUDITORIA CONCLUÍDA COM SUCESSO")
            self.logger.info(f"Relatório: {report_path}")
            self.logger.info("="*60)
            
            return report_path
            
        except (XMLParseException, SefazScraperException, AuditException, ReportGenerationException):
            # Re-raise exceções conhecidas
            raise
        except Exception as e:
            # Exceções inesperadas
            self.logger.error(f"Erro inesperado: {e}", exc_info=True)
            raise AuditException(f"Erro inesperado na auditoria: {e}")
    
    def _read_xml(self, xml_path: str) -> tuple[str, List[FiscalItemDTO]]:
        """Lê arquivo XML."""
        self.logger.info(f"[1/4] Lendo XML: {xml_path}")
        
        # Validar arquivo
        path = Path(xml_path)
        if not path.exists():
            raise XMLParseException(f"Arquivo não encontrado: {xml_path}")
        
        if not path.suffix.lower() == ".xml":
            raise XMLParseException(f"Arquivo não é XML: {xml_path}")
        
        # Parsear
        try:
            nfe_key, items = self.xml_reader.parse(xml_path)
            self.logger.info(f"  ✓ Chave: {nfe_key}")
            self.logger.info(f"  ✓ Itens: {len(items)}")
            return nfe_key, items
        except Exception as e:
            raise XMLParseException(f"Erro ao ler XML: {e}")
    
    def _fetch_sefaz(self, nfe_key: str) -> List[FiscalItemDTO]:
        """Busca memorial na SEFAZ."""
        self.logger.info(f"[2/4] Buscando memorial SEFAZ: {nfe_key}")
        
        try:
            items = self.scraper.fetch_memorial(nfe_key)
            
            if not items:
                raise SefazScraperException("Nenhum item retornado da SEFAZ")
            
            self.logger.info(f"  ✓ Itens SEFAZ: {len(items)}")
            return items
        except Exception as e:
            raise SefazScraperException(f"Erro ao buscar SEFAZ: {e}")
    
    def _audit_items(
        self,
        xml_items: List[FiscalItemDTO],
        sefaz_items: List[FiscalItemDTO]
    ) -> List[AuditResultDTO]:
        """Audita itens."""
        self.logger.info(f"[3/4] Auditando itens...")
        
        # Criar mapa SEFAZ
        sefaz_map = {item.item_index: item for item in sefaz_items}
        
        results = []
        missing_items = []
        
        for xml_item in xml_items:
            idx = xml_item.item_index
            sefaz_item = sefaz_map.get(idx)
            
            if not sefaz_item:
                self.logger.warning(f"  ⚠ Item {idx} não encontrado na SEFAZ")
                missing_items.append(idx)
                continue
            
            try:
                result = self.auditor.audit_item(xml_item, sefaz_item)
                results.append(result)
                
                status = "✓ OK" if result.is_compliant else "✗ DIVERGENTE"
                self.logger.info(f"  Item {idx}: {status}")
                
                if not result.is_compliant:
                    for diff in result.differences:
                        self.logger.debug(f"    - {diff.message}")
            
            except Exception as e:
                self.logger.error(f"  ✗ Erro no item {idx}: {e}")
                raise AuditException(f"Erro ao auditar item {idx}: {e}")
        
        if missing_items:
            self.logger.warning(f"Itens ausentes na SEFAZ: {missing_items}")
        
        return results
    
    def _generate_report(
        self,
        results: List[AuditResultDTO],
        output_path: Optional[str]
    ) -> str:
        """Gera relatório."""
        self.logger.info(f"[4/4] Gerando relatório...")
        
        try:
            report_path = self.reporter.generate_excel(results, output_path)
            self.logger.info(f"  ✓ Relatório: {report_path}")
            return report_path
        except Exception as e:
            raise ReportGenerationException(f"Erro ao gerar relatório: {e}")
    
    def _log_summary(self, results: List[AuditResultDTO]):
        """Log resumo da auditoria."""
        total = len(results)
        compliant = sum(1 for r in results if r.is_compliant)
        divergent = total - compliant
        
        self.logger.info("")
        self.logger.info("RESUMO DA AUDITORIA:")
        self.logger.info(f"  Total de itens: {total}")
        self.logger.info(f"  Conformes: {compliant} ({100*compliant/total:.1f}%)")
        self.logger.info(f"  Divergentes: {divergent} ({100*divergent/total:.1f}%)")
        
        if divergent > 0:
            self.logger.warning(f"⚠ Atenção: {divergent} itens com divergências!")


# =============================================================================
# TESTES UNITÁRIOS
# =============================================================================

# tests/services/test_audit_service.py
"""
Testes para AuditService.

Demonstra como testar usando mocks das dependências.
"""

import pytest
from decimal import Decimal
from unittest.mock import Mock, patch
from pathlib import Path

from src.services.audit_service import AuditService
from src.domain.dtos import FiscalItemDTO, AuditResultDTO, AuditDifference
from src.domain.exceptions import (
    XMLParseException,
    SefazScraperException,
    AuditException
)


@pytest.fixture
def mock_xml_reader():
    """Mock do XMLReader."""
    reader = Mock()
    reader.parse.return_value = (
        "13220107293118000188550010000001011000001014",  # NFe key
        [
            FiscalItemDTO(
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
        ]
    )
    return reader


@pytest.fixture
def mock_scraper():
    """Mock do SefazScraper."""
    scraper = Mock()
    scraper.fetch_memorial.return_value = [
        FiscalItemDTO(
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
            tax_value=Decimal("18.00"),
            mva_percent=Decimal("30.00"),
            is_suframa_benefit=False
        )
    ]
    return scraper


@pytest.fixture
def mock_auditor():
    """Mock do AuditEngine."""
    auditor = Mock()
    auditor.audit_item.return_value = AuditResultDTO(
        item_index=1,
        product_code="PROD-001",
        is_compliant=True,
        differences=[]
    )
    return auditor


@pytest.fixture
def mock_reporter():
    """Mock do ReportGenerator."""
    reporter = Mock()
    reporter.generate_excel.return_value = "relatorio_teste.csv"
    return reporter


@pytest.fixture
def audit_service(mock_xml_reader, mock_scraper, mock_auditor, mock_reporter):
    """Serviço com todas as dependências mockadas."""
    return AuditService(
        xml_reader=mock_xml_reader,
        scraper=mock_scraper,
        auditor=mock_auditor,
        reporter=mock_reporter
    )


# =============================================================================
# TESTES DE SUCESSO
# =============================================================================

def test_audit_nfe_success(audit_service, tmp_path):
    """Testa auditoria bem-sucedida."""
    # Preparar
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Executar
    report_path = audit_service.audit_nfe(str(xml_file))
    
    # Verificar
    assert report_path == "relatorio_teste.csv"
    
    # Verificar chamadas
    audit_service.xml_reader.parse.assert_called_once_with(str(xml_file))
    audit_service.scraper.fetch_memorial.assert_called_once()
    audit_service.auditor.audit_item.assert_called_once()
    audit_service.reporter.generate_excel.assert_called_once()


def test_audit_nfe_with_custom_key(audit_service, tmp_path):
    """Testa auditoria com chave customizada."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    custom_key = "99999999999999999999999999999999999999999999"
    
    audit_service.audit_nfe(str(xml_file), nfe_key=custom_key)
    
    # Verificar que usou a chave customizada
    audit_service.scraper.fetch_memorial.assert_called_with(custom_key)


# =============================================================================
# TESTES DE ERRO
# =============================================================================

def test_audit_nfe_xml_not_found(audit_service):
    """Testa erro quando XML não existe."""
    with pytest.raises(XMLParseException, match="Arquivo não encontrado"):
        audit_service.audit_nfe("arquivo_inexistente.xml")


def test_audit_nfe_invalid_extension(audit_service, tmp_path):
    """Testa erro quando arquivo não é XML."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("not xml")
    
    with pytest.raises(XMLParseException, match="Arquivo não é XML"):
        audit_service.audit_nfe(str(txt_file))


def test_audit_nfe_xml_parse_error(audit_service, tmp_path):
    """Testa erro ao parsear XML."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Simular erro no parser
    audit_service.xml_reader.parse.side_effect = Exception("Parse error")
    
    with pytest.raises(XMLParseException, match="Erro ao ler XML"):
        audit_service.audit_nfe(str(xml_file))


def test_audit_nfe_no_key(audit_service, mock_xml_reader, tmp_path):
    """Testa erro quando chave não é encontrada."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Simular XML sem chave
    mock_xml_reader.parse.return_value = ("", [])
    
    with pytest.raises(AuditException, match="Chave NFe não encontrada"):
        audit_service.audit_nfe(str(xml_file))


def test_audit_nfe_sefaz_error(audit_service, tmp_path):
    """Testa erro ao buscar SEFAZ."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Simular erro no scraper
    audit_service.scraper.fetch_memorial.side_effect = Exception("Scraper error")
    
    with pytest.raises(SefazScraperException, match="Erro ao buscar SEFAZ"):
        audit_service.audit_nfe(str(xml_file))


def test_audit_nfe_no_sefaz_items(audit_service, tmp_path):
    """Testa erro quando SEFAZ não retorna itens."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Simular SEFAZ vazio
    audit_service.scraper.fetch_memorial.return_value = []
    
    with pytest.raises(SefazScraperException, match="Nenhum item retornado"):
        audit_service.audit_nfe(str(xml_file))


# =============================================================================
# TESTES DE LÓGICA
# =============================================================================

def test_audit_handles_missing_items(audit_service, mock_scraper, tmp_path):
    """Testa quando item não existe na SEFAZ."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # XML tem item 2, mas SEFAZ não
    audit_service.xml_reader.parse.return_value = (
        "key",
        [
            # ... item 1 ...
            FiscalItemDTO(
                origin="XML",
                item_index=2,  # Este item não existe na SEFAZ
                product_code="PROD-002",
                ncm="12345678",
                cest="",
                cfop="5102",
                cst="00",
                amount_total=Decimal("50.00"),
                tax_base=Decimal("50.00"),
                tax_rate=Decimal("18.00"),
                tax_value=Decimal("9.00"),
                mva_percent=Decimal("0.00"),
                is_suframa_benefit=False
            )
        ]
    )
    
    # SEFAZ só tem item 1
    mock_scraper.fetch_memorial.return_value = [
        FiscalItemDTO(
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
            tax_value=Decimal("18.00"),
            mva_percent=Decimal("30.00"),
            is_suframa_benefit=False
        )
    ]
    
    # Deve executar sem erro (apenas log warning)
    report_path = audit_service.audit_nfe(str(xml_file))
    assert report_path


def test_audit_with_divergences(audit_service, mock_auditor, tmp_path):
    """Testa auditoria com divergências."""
    xml_file = tmp_path / "test.xml"
    xml_file.write_text("<xml>test</xml>")
    
    # Simular divergência
    mock_auditor.audit_item.return_value = AuditResultDTO(
        item_index=1,
        product_code="PROD-001",
        is_compliant=False,
        differences=[
            AuditDifference(
                field="NCM",
                xml_value="22021000",
                sefaz_value="22029900",
                message="Divergência de NCM"
            )
        ]
    )
    
    # Deve executar normalmente
    report_path = audit_service.audit_nfe(str(xml_file))
    assert report_path


# =============================================================================
# TESTE DE INTEGRAÇÃO (EXEMPLO)
# =============================================================================

@pytest.mark.integration
def test_full_audit_integration(tmp_path):
    """
    Teste de integração end-to-end.
    
    Usa componentes reais (exceto Selenium).
    """
    from src.infrastructure.xml_reader import XMLReader
    from src.core.auditor import AuditEngine
    from src.presentation.report_generator import ReportGenerator
    
    # Preparar XML de teste
    xml_content = '''<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
      <NFe>
        <infNFe Id="NFe13220107293118000188550010000001011000001014" versao="4.00">
          <det nItem="1">
            <prod>
              <cProd>PROD-001</cProd>
              <xProd>Produto Teste</xProd>
              <NCM>22021000</NCM>
              <CEST>0300700</CEST>
              <CFOP>6110</CFOP>
              <vProd>100.00</vProd>
            </prod>
            <imposto>
              <ICMS>
                <ICMS00>
                  <CST>00</CST>
                  <vBC>100.00</vBC>
                  <pICMS>18.00</pICMS>
                  <vICMS>18.00</vICMS>
                </ICMS00>
              </ICMS>
            </imposto>
          </det>
        </infNFe>
      </NFe>
    </nfeProc>'''
    
    xml_file = tmp_path / "test.xml"
    xml_file.write_text(xml_content)
    
    # Mock apenas do Scraper (Selenium)
    mock_scraper = Mock()
    mock_scraper.fetch_memorial.return_value = [
        FiscalItemDTO(
            origin="SEFAZ",
            item_index=1,
            product_code="PROD-001",
            ncm="22021000",
            cest="0300700",
            cfop="6110",
            cst="00",
            amount_total=Decimal("0.00"),
            tax_base=Decimal("100.00"),
            tax_rate=Decimal("18.00"),
            tax_value=Decimal("18.00"),
            mva_percent=Decimal("0.00"),
            is_suframa_benefit=False
        )
    ]
    
    # Criar serviço com componentes reais
    service = AuditService(
        xml_reader=XMLReader(),
        scraper=mock_scraper,
        auditor=AuditEngine(),
        reporter=ReportGenerator()
    )
    
    # Executar
    report_path = service.audit_nfe(str(xml_file))
    
    # Verificar
    assert Path(report_path).exists()
    assert Path(report_path).suffix == ".csv"
