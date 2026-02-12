# Technical Specification (SPEC) - AuditTax AP

## 1. Arquitetura do Sistema
A solução seguirá o padrão **ETL (Extract, Transform, Load)** adaptado para auditoria.

### Diagrama de Camadas
1. **Input Layer:** `XMLReader` (lxml) & `SefazScraper` (Selenium).
2. **Normalization Layer:** Converte ambos os inputs para `FiscalItemDTO` (Data Transfer Object) padronizado.
3. **Core Logic Layer:** `AuditEngine`. Compara dois DTOs e aplica regras de negócio.
4. **Presentation Layer:** `ReportGenerator` (Pandas/Excel).

## 2. Stack Tecnológica
- **Linguagem:** Python 3.10+ (Tipagem forte obrigatória).
- **Web Driver:** Selenium WebDriver (Chrome/Edge).
- **Parsing:** `BeautifulSoup4` (HTML Sefaz), `lxml` (XML NFe).
- **Dados:** `Pandas` (Manipulação tabular), `openpyxl` (Excel).
- **Matemática:** Biblioteca padrão `decimal` com Contexto de Precisão 2 casas (ROUND_HALF_UP).

## 3. Modelo de Dados (Schema Lógico)

Não haverá banco de dados relacional complexo na V1, mas os objetos em memória seguirão esta estrutura:

```python
@dataclass
class FiscalItemDTO:
    origin: str # 'XML' ou 'SEFAZ'
    item_index: int
    product_code: str
    ncm: str
    cest: str
    cfop: str
    cst: str
    amount_total: Decimal
    tax_base: Decimal
    tax_rate: Decimal
    tax_value: Decimal
    mva_percent: Decimal
    is_suframa_benefit: bool