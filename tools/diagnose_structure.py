from bs4 import BeautifulSoup
import re

# Caminho do HTML real
path = r"c:\Projetos\AuditTaxAP\tests\samples\52260277595395006269550050000238801206971225\SEFAZ-AP_MATHEUS.html"

with open(path, "r", encoding="windows-1252") as f:
    html = f.read()

soup = BeautifulSoup(html, "html.parser")

print("=" * 80)
print("ANÁLISE DA TABELA DE CFOP (INFORMACOES DETALHADAS DA COBRANCA)")
print("=" * 80)

# Encontrar a tabela com CFOP
tables = soup.find_all("table")
for i, table in enumerate(tables):
    text = table.get_text(" ", strip=True).upper()
    if "OPERACAO" in text and "CFOP" in text and "INFORMACOES DETALHADAS" in text:
        print(f"\nTabela {i} encontrada!")
        print(f"Headers encontrados:")
        
        thead = table.find("thead")
        if thead:
            header_rows = thead.find_all("tr")
            for hr in header_rows:
                cells = hr.find_all(["th", "td"])
                headers = [c.get_text(strip=True) for c in cells]
                print(f"  {headers}")
        
        tbody = table.find("tbody")
        if tbody:
            rows = tbody.find_all("tr")
            print(f"\nLinhas do corpo ({len(rows)} linhas):")
            for j, row in enumerate(rows):
                cells = row.find_all("td")
                values = [c.get_text(strip=True) for c in cells]
                print(f"  Linha {j}: {values}")

print("\n" + "=" * 80)
print("ANÁLISE DOS BLOCOS DE ITENS (H2)")
print("=" * 80)

h2_headers = soup.find_all("h2", string=lambda t: t and t.strip().startswith("ITEM:"))
print(f"\nEncontrados {len(h2_headers)} blocos H2 de itens\n")

for idx, h2 in enumerate(h2_headers[:3]):  # Primeiros 3 itens apenas
    print(f"\n{'='*60}")
    print(f"ITEM {idx + 1}")
    print(f"{'='*60}")
    
    # Texto do H2
    h2_text = h2.get_text(strip=True)
    print(f"H2 Text: {h2_text}")
    
    # Encontrar a TD pai
    td_item = h2.find_parent("td")
    if not td_item:
        print("  ERRO: Não encontrou TD pai do H2")
        continue
    
    # Encontrar a TR (linha 1)
    row1 = td_item.find_parent("tr")
    if not row1:
        print("  ERRO: Não encontrou TR pai")
        continue
    
    # Extrair todas as células da linha 1
    cells = row1.find_all("td")
    print(f"\nLinha 1 tem {len(cells)} células:")
    
    for i, cell in enumerate(cells):
        # Procurar H5 labels
        h5_labels = cell.find_all("h5")
        cell_text = cell.get_text(" ", strip=True)
        
        if h5_labels:
            print(f"\n  Célula {i}:")
            for h5 in h5_labels:
                label = h5.get_text(strip=True).upper()
                # Valor é o texto da célula sem o label
                value = cell_text.replace(h5.get_text(strip=True), "").strip()
                print(f"    {label}: '{value}'")
        elif i == 0 and h2 in cell.descendants:
            print(f"\n  Célula {i}: [Contém H2 - Item Box]")
            print(f"    Texto completo: {cell_text[:100]}")
    
    # Verificar linha 2 (descrição)
    row2 = row1.find_next_sibling("tr")
    if row2:
        desc_text = row2.get_text(" ", strip=True)
        print(f"\nLinha 2 (Descrição): {desc_text[:100]}...")
    
    # Verificar linha 3 (classificação/MVA)
    row3 = row2.find_next_sibling("tr") if row2 else None
    if row3:
        class_text = row3.get_text(" ", strip=True)
        print(f"\nLinha 3 (Classificação): {class_text[:100]}...")
        
        # Procurar MVA
        match_mva = re.search(r'MVA ORIGINAL\s*([\d,]+)%', class_text)
        if match_mva:
            print(f"  MVA encontrado: {match_mva.group(1)}%")
    
    # Verificar linha 4 (cálculo detalhado)
    row4 = row3.find_next_sibling("tr") if row3 else None
    if row4:
        calc_text = row4.get_text(" ", strip=True)
        print(f"\nLinha 4 (Cálculo): {calc_text[:150]}...")
        
        # Procurar indicadores
        if "DESONERACAO DA SUFRAMA" in calc_text.upper():
            print("  SUFRAMA: SIM")
        
        # Procurar base de cálculo
        match_bc = re.search(r'F\)\s*BASE.*?=\s*([\d\.,]+)', calc_text)
        if match_bc:
            print(f"  Base de Cálculo: {match_bc.group(1)}")

print("\n" + "=" * 80)
print("FIM DO DIAGNÓSTICO")
print("=" * 80)
