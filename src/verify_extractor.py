"""
Script de verificação: testa o ItemExtractor refatorado contra o HTML real SEFAZ-AP.
Valida extração dos 6 itens com MVA Ajustada, Benefício SUFRAMA e Valor Cobrado.
"""
import sys
import os
# Adicionar raiz do projeto ao path (pai de src/)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from decimal import Decimal
from bs4 import BeautifulSoup
from src.infrastructure.sefaz.item_extractor import ItemExtractor

# Dados esperados (verificados manualmente no HTML)
EXPECTED = {
    1: {"mva": "39.51", "suframa": "540.98", "valor": "455.25", "ncm": "04069020", "cest": "1702400", "cst": "040"},
    2: {"mva": "39.51", "suframa": "347.69", "valor": "292.59", "ncm": "04061010", "cest": "1702401", "cst": "040"},
    3: {"mva": "39.51", "suframa": "43.92",  "valor": "36.96",  "ncm": "04061010", "cest": "1702401", "cst": "040"},
    4: {"mva": "47.02", "suframa": "38.58",  "valor": "36.29",  "ncm": "04061090", "cest": "1702300", "cst": "040"},
    5: {"mva": "47.02", "suframa": "24.05",  "valor": "22.62",  "ncm": "04061090", "cest": "1702300", "cst": "040"},
    6: {"mva": "40.59", "suframa": "13.34",  "valor": "11.41",  "ncm": "04015029", "cest": "1701902", "cst": "040"},
}

def main():
    html_path = os.path.join(
        "tests", "samples", 
        "SEFAZ-AP_MATHEUS.html"
    )
    
    if not os.path.exists(html_path):
        print(f"ERRO: HTML não encontrado em {html_path}")
        return False
    
    with open(html_path, "r", encoding="windows-1252") as f:
        html = f.read()
    
    soup = BeautifulSoup(html, "html.parser")
    extractor = ItemExtractor()
    items = extractor.extract(soup, cfop_map={}, default_cfop="6110")
    
    print(f"Total de itens extraídos: {len(items)}")
    print("=" * 90)
    
    all_ok = True
    
    for item in items:
        idx = item.item_index
        expected = EXPECTED.get(idx)
        if not expected:
            print(f"  ITEM:{idx} - NÃO ESPERADO (extra)")
            continue
        
        errors = []
        
        # Verificar MVA Ajustada
        if str(item.sefaz_mva_percent) != expected["mva"]:
            errors.append(f"MVA: esperado={expected['mva']}, extraído={item.sefaz_mva_percent}")
        
        # Verificar Benefício SUFRAMA
        if str(item.sefaz_benefit_value) != expected["suframa"]:
            errors.append(f"SUFRAMA: esperado={expected['suframa']}, extraído={item.sefaz_benefit_value}")
        
        # Verificar Valor Cobrado
        if str(item.sefaz_tax_value) != expected["valor"]:
            errors.append(f"VALOR: esperado={expected['valor']}, extraído={item.sefaz_tax_value}")
        
        # Verificar NCM
        if item.ncm != expected["ncm"]:
            errors.append(f"NCM: esperado={expected['ncm']}, extraído={item.ncm}")
        
        # Verificar CEST
        if item.cest != expected["cest"]:
            errors.append(f"CEST: esperado={expected['cest']}, extraído={item.cest}")
        
        # Verificar CST
        if item.cst != expected["cst"]:
            errors.append(f"CST: esperado={expected['cst']}, extraído={item.cst}")
        
        status = "✅" if not errors else "❌"
        print(f"  ITEM:{idx} {status}")
        print(f"    NCM={item.ncm} | CEST={item.cest} | CST={item.cst}")
        print(f"    MVA Ajustada={item.sefaz_mva_percent}% | SUFRAMA=R${item.sefaz_benefit_value} | VALOR=R${item.sefaz_tax_value}")
        
        if errors:
            all_ok = False
            for err in errors:
                print(f"    ⚠️  {err}")
        print()
    
    # Verificar que extraiu todos os 6 itens
    if len(items) != 6:
        all_ok = False
        print(f"❌ Esperados 6 itens, extraídos {len(items)}")
    
    print("=" * 90)
    if all_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
