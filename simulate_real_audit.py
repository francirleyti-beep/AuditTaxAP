"""
Script de simulação de Auditoria Completa.
Usa Components REAIS, exceto o download (Scraper) que é mockado para usar o HTML local.
Isso valida o fluxo XML -> Validação -> Auditoria -> Relatório.
"""
import sys
import os
import logging
from unittest.mock import MagicMock

# Ajusta path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.services.audit_service import AuditService
from src.infrastructure.sefaz.item_extractor import ItemExtractor
from bs4 import BeautifulSoup

def main():
    # Configuração
    xml_path = "tests/samples/52260277595395006269550050000238801206971225.xml"
    html_path = "tests/samples/SEFAZ-AP_MATHEUS.html"
    
    print(f"=== SIMULAÇÃO DE AUDITORIA COMPLETA ===")
    print(f"XML: {xml_path}")
    print(f"HTML (Simulando SEFAZ): {html_path}")
    
    # Validar arquivos
    if not os.path.exists(xml_path):
        print(f"❌ XML não encontrado: {xml_path}")
        return
    if not os.path.exists(html_path):
        print(f"❌ HTML não encontrado: {html_path}")
        return

    # Instanciar Serviço
    service = AuditService()
    
    # --- MOCK do Scraper (Bypass Rede/Captcha) ---
    # Em vez de ir na web, lê o arquivo local e usa o Extractor real
    print("\n[Scraper] Simulando acesso à SEFAZ via arquivo local...")
    with open(html_path, "r", encoding="windows-1252") as f:
        html_content = f.read()
        
    soup = BeautifulSoup(html_content, "html.parser")
    extractor = ItemExtractor()
    # Extração real dos dados do HTML
    sefaz_items = extractor.extract(soup, cfop_map={}, default_cfop="0000")
    
    # Injeta o mock no serviço
    service.scraper.fetch_memorial = MagicMock(return_value=sefaz_items)
    print(f"[Scraper] {len(sefaz_items)} itens extraídos do HTML local.")
    
    # --- Executar Fluxo Principal ---
    print("\n[AuditService] Iniciando processamento...")
    try:
        report_path, results = service.process_audit(xml_path)
        print(f"\n✅ SUCESSO! Relatório gerado em: {report_path}")
        
        # Exibir conteúdo curto do relatório
        print("\n--- Conteúdo do Relatório (Primeiras linhas) ---")
        with open(report_path, "r", encoding="utf-8-sig") as f:
            for _ in range(10):
                line = f.readline()
                if not line: break
                print(line.strip())
                
    except Exception as e:
        print(f"❌ ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
