"""
Script de simulação de Auditoria Completa.
Usa Components REAIS, exceto o download (Scraper) que é mockado para usar o HTML local.
Isso valida o fluxo XML -> Validação -> Auditoria -> Relatório.
"""
import sys
import os
import logging
from unittest.mock import MagicMock

# Ajusta path para incluir a raiz do projeto (pai de tests/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.audit_service import AuditService
from src.infrastructure.sefaz.item_extractor import ItemExtractor
from bs4 import BeautifulSoup

def main():
    # Configuração (caminhos relativos à raiz do projeto, pois o script roda de lá via sys.path hack ou working dir)
    # Mas wait, se rodarmos de tests/, o CWD pode ser tests/ ou root.
    # O Docker WORKDIR é /app.
    # Se rodarmos `python tests/simulate_real_audit.py`, o CWD é /app.
    # Então paths relativos devem ser a partir de /app.
    
    xml_path = "tests/samples/52260277595395006269550050000238801206971225.xml"
    html_path = "tests/samples/SEFAZ-AP_MATHEUS.html"
    
    print(f"=== SIMULAÇÃO DE AUDITORIA COMPLETA ===")
    print(f"XML: {xml_path}")
    print(f"HTML (Simulando SEFAZ): {html_path}")
    
    # Validar arquivos
    if not os.path.exists(xml_path):
        print(f"❌ XML não encontrado: {xml_path}")
        # Tentar caminho absoluto baseado em __file__
        xml_path = os.path.join(os.path.dirname(__file__), "samples", "52260277595395006269550050000238801206971225.xml")
        if not os.path.exists(xml_path):
             print(f"❌ XML realmente não encontrado em {xml_path}")
             return
        print(f"✅ XML encontrado via caminho relativo ao script: {xml_path}")

    if not os.path.exists(html_path):
        # Tentar caminho absoluto
        html_path = os.path.join(os.path.dirname(__file__), "samples", "SEFAZ-AP_MATHEUS.html")
        if not os.path.exists(html_path):
            print(f"❌ HTML não encontrado: {html_path}")
            return
        print(f"✅ HTML encontrado via caminho relativo ao script: {html_path}")

    # Instanciar Serviço
    try:
        service = AuditService()
    except Exception as e:
        print(f"❌ Erro ao instanciar AuditService: {e}")
        return
    
    # --- MOCK do Scraper (Bypass Rede/Captcha) ---
    print("\n[Scraper] Simulando acesso à SEFAZ via arquivo local...")
    try:
        with open(html_path, "r", encoding="windows-1252") as f:
            html_content = f.read()
    except Exception as e:
        print(f"❌ Erro ao ler HTML: {e}")
        return
        
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
        # Nota: process_audit retorna 4 valores agora
        ret = service.process_audit(xml_path)
        
        report_path = ret[0]
        results = ret[1]
        consistency_errors = ret[2]
        invoice_dto = ret[3]
        
        print(f"\n✅ SUCESSO! Relatório gerado em: {report_path}")
        print(f"📊 Detalhes do Retorno:")
        print(f"   - Resultados de Auditoria: {len(results)} itens")
        print(f"   - Erros de Consistência: {len(consistency_errors)}")
        print(f"   - InvoiceDTO Header: {invoice_dto.emitter_name} -> {invoice_dto.recipient_name} (Total: {invoice_dto.total_invoice})")
        
        # Exibir conteúdo curto do relatório
        print("\n--- Conteúdo do Relatório (Primeiras linhas) ---")
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8-sig") as f:
                for _ in range(15):
                    line = f.readline()
                    if not line: break
                    print(line.strip())
        else:
             print(f"⚠️ Arquivo de relatório não encontrado em {report_path}")
                
    except Exception as e:
        print(f"❌ ERRO CRÍTICO NA AUDITORIA: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
