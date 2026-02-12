# GUIA PRÁTICO DE IMPLEMENTAÇÃO

Este guia fornece um roadmap step-by-step para aplicar as melhorias sugeridas no projeto AuditTax AP.

## FASE 1: FUNDAÇÕES (1-2 dias) ⚠️ PRIORIDADE ALTA

### 1.1 Setup de Logging

**Objetivo:** Substituir todos os `print()` por logging estruturado.

**Passos:**
```bash
# 1. Criar diretório de configuração
mkdir -p src/utils

# 2. Criar arquivo de logging
```

```python
# src/utils/logging_config.py
import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logging(log_level=logging.INFO):
    """Configura sistema de logging."""
    
    # Criar diretório de logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo com timestamp
    log_file = log_dir / f"audit_{datetime.now():%Y%m%d_%H%M%S}.log"
    
    # Formato
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    
    # Root logger
    logging.basicConfig(
        level=log_level,
        handlers=[console, file_handler]
    )
    
    # Silenciar logs de terceiros
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return log_file
```

**Aplicar em cada arquivo:**
```python
# No topo de cada arquivo
import logging
logger = logging.getLogger(__name__)

# Substituir
print("DEBUG: Processando...")
# Por:
logger.debug("Processando...")

# Substituir
print(f"ERRO: {e}")
# Por:
logger.error(f"Erro: {e}", exc_info=True)
```

**Testar:**
```bash
python main.py
# Deve criar arquivo em logs/audit_YYYYMMDD_HHMMSS.log
```

---

### 1.2 Exceções Customizadas

**Objetivo:** Criar hierarquia de exceções para melhor controle de erros.

```python
# src/domain/exceptions.py
class AuditTaxException(Exception):
    """Exceção base."""
    pass

class XMLParseException(AuditTaxException):
    """Erro ao parsear XML."""
    pass

class SefazScraperException(AuditTaxException):
    """Erro no scraping."""
    pass

class AuditException(AuditTaxException):
    """Erro na auditoria."""
    pass

class ReportGenerationException(AuditTaxException):
    """Erro no relatório."""
    pass
```

**Aplicar:**
```python
# src/infrastructure/xml_reader.py
from src.domain.exceptions import XMLParseException

def parse(self, xml_path):
    try:
        # ... código ...
    except ET.ParseError as e:
        raise XMLParseException(f"XML inválido: {e}")
    except Exception as e:
        raise XMLParseException(f"Erro ao ler XML: {e}")
```

---

### 1.3 Validação de DTOs

**Objetivo:** Validar dados na criação dos DTOs.

```python
# src/domain/dtos.py
@dataclass
class FiscalItemDTO:
    # ... campos ...
    
    def __post_init__(self):
        """Validações."""
        if self.origin not in ['XML', 'SEFAZ']:
            raise ValueError(f"Origin inválida: {self.origin}")
        
        if self.item_index <= 0:
            raise ValueError(f"item_index inválido: {self.item_index}")
        
        if self.ncm and len(self.ncm) != 8:
            raise ValueError(f"NCM deve ter 8 dígitos: {self.ncm}")
        
        if self.cfop and len(self.cfop) != 4:
            raise ValueError(f"CFOP deve ter 4 dígitos: {self.cfop}")
```

**Testar:**
```python
# Deve lançar exceção
item = FiscalItemDTO(origin="INVALID", ...)  # ValueError!
```

---

## FASE 2: REFATORAÇÃO DO SCRAPER (2-3 dias) ⚠️ PRIORIDADE ALTA

### 2.1 Separar em Classes

**Estrutura:**
```
src/infrastructure/sefaz/
├── __init__.py
├── scraper.py          # Fachada principal
├── driver_manager.py   # Gerencia Selenium
├── html_parser.py      # Orquestra parsing
├── cfop_extractor.py   # Extrai CFOP
└── item_extractor.py   # Extrai itens
```

**Passo 1:** Criar diretório
```bash
mkdir -p src/infrastructure/sefaz
touch src/infrastructure/sefaz/__init__.py
```

**Passo 2:** Copiar classes do exemplo `scraper_refatorado.py`

**Passo 3:** Atualizar imports
```python
# Antes
from src.infrastructure.sefaz_scraper import SefazScraper

# Depois
from src.infrastructure.sefaz.scraper import SefazScraper
```

**Passo 4:** Testar
```bash
python -c "from src.infrastructure.sefaz.scraper import SefazScraper; print('OK')"
```

---

### 2.2 Otimizações de Performance

**Compilar Regex uma vez:**
```python
class ItemExtractor:
    # Regex compilados (fora do método)
    CST_PATTERN = re.compile(r'(\d+)')
    MVA_PATTERN = re.compile(r'MVA ORIGINAL\s*([\d,]+)%')
    
    def _extract_cst(self, data_map):
        # Usar regex pré-compilado
        match = self.CST_PATTERN.match(data_map.get("CST", ""))
        return match.group(1) if match else ""
```

**Usar lxml ao invés de html.parser:**
```python
# Antes
soup = BeautifulSoup(html, "html.parser")

# Depois (2-3x mais rápido!)
soup = BeautifulSoup(html, "lxml")
```

**Instalar:**
```bash
pip install lxml
```

---

## FASE 3: REFATORAÇÃO DO AUDITOR (1-2 dias) 🔵 PRIORIDADE MÉDIA

### 3.1 Implementar Strategy Pattern

**Passo 1:** Copiar `audit_rules_refatorado.py` para `src/core/audit_rules.py`

**Passo 2:** Atualizar `src/core/auditor.py`
```python
from src.core.audit_rules import AuditRuleChainBuilder

class AuditEngine:
    def __init__(self, tolerance: Decimal = Decimal("0.05")):
        self.tolerance = tolerance
        self.calculator = TaxCalculator()
        
        # Construir cadeia de regras
        builder = AuditRuleChainBuilder(tolerance)
        self.rule_chain = (builder
                          .with_cadastral_rules()
                          .with_monetary_rules()
                          .with_special_rules()
                          .build())
    
    def audit_item(self, xml_item, sefaz_item):
        """Usa cadeia de regras."""
        differences = self.rule_chain.check(xml_item, sefaz_item)
        
        return AuditResultDTO(
            item_index=xml_item.item_index,
            product_code=xml_item.product_code,
            is_compliant=(len(differences) == 0),
            differences=differences
        )
```

**Passo 3:** Testar
```bash
python -m pytest tests/test_audit.py -v
```

---

## FASE 4: CAMADA DE SERVIÇOS (1 dia) 🔵 PRIORIDADE MÉDIA

### 4.1 Criar Serviço

**Passo 1:** Criar `src/services/audit_service.py` (copiar do exemplo)

**Passo 2:** Atualizar `main.py`
```python
from src.services.audit_service import AuditService
from src.utils.logging_config import setup_logging

def main():
    # Setup logging
    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=== AuditTax AP - Início ===")
    
    # Input
    xml_path = input("Caminho do XML: ").strip()
    
    # Criar serviço
    service = AuditService()
    
    try:
        # Executar auditoria
        report_path = service.audit_nfe(xml_path)
        
        print(f"\n✓ Sucesso! Relatório: {report_path}")
        
    except Exception as e:
        logger.error(f"Erro na auditoria: {e}", exc_info=True)
        print(f"\n✗ Erro: {e}")

if __name__ == "__main__":
    main()
```

---

## FASE 5: TESTES (2-3 dias) 🔵 PRIORIDADE MÉDIA

### 5.1 Configurar Fixtures

```python
# tests/conftest.py
import pytest
from decimal import Decimal
from src.domain.dtos import FiscalItemDTO

@pytest.fixture
def xml_item():
    return FiscalItemDTO(
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

@pytest.fixture
def sefaz_item():
    return FiscalItemDTO(
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
```

### 5.2 Adicionar Testes Parametrizados

```python
@pytest.mark.parametrize("field,xml_val,sefaz_val,should_fail", [
    ("ncm", "12345678", "87654321", True),
    ("ncm", "12345678", "12345678", False),
    ("cfop", "6110", "5102", True),
])
def test_field_validation(xml_item, sefaz_item, field, xml_val, sefaz_val, should_fail):
    engine = AuditEngine()
    
    setattr(xml_item, field, xml_val)
    setattr(sefaz_item, field, sefaz_val)
    
    result = engine.audit_item(xml_item, sefaz_item)
    
    assert result.is_compliant == (not should_fail)
```

### 5.3 Rodar Testes
```bash
# Todos os testes
pytest tests/ -v

# Com cobertura
pip install pytest-cov
pytest tests/ --cov=src --cov-report=html

# Ver relatório
open htmlcov/index.html
```

---

## FASE 6: CONFIGURAÇÃO EXTERNA (1 dia) 🟢 PRIORIDADE BAIXA

### 6.1 Usar Pydantic Settings

```bash
pip install pydantic python-dotenv
```

```python
# config.py
from pydantic import BaseSettings
from decimal import Decimal

class Settings(BaseSettings):
    # SEFAZ
    sefaz_url: str = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
    selenium_headless: bool = False
    
    # Auditoria
    audit_tolerance: Decimal = Decimal("0.05")
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

```bash
# .env (não commitar!)
SEFAZ_URL=http://www.sefaz.ap.gov.br/EMISSAO/memorial.php
AUDIT_TOLERANCE=0.05
LOG_LEVEL=DEBUG
SELENIUM_HEADLESS=true
```

### 6.2 Usar Configuração

```python
from config import settings

scraper = SefazScraper(headless=settings.selenium_headless)
auditor = AuditEngine(tolerance=settings.audit_tolerance)
```

---

## CHECKLIST DE IMPLEMENTAÇÃO

### Fase 1: Fundações ⚠️
- [ ] Implementar logging estruturado
- [ ] Criar exceções customizadas
- [ ] Adicionar validação nos DTOs
- [ ] Testar cada componente

### Fase 2: Scraper ⚠️
- [ ] Separar em classes menores
- [ ] Compilar regex
- [ ] Usar lxml
- [ ] Testar extração

### Fase 3: Auditor 🔵
- [ ] Implementar Strategy Pattern
- [ ] Criar regras individuais
- [ ] Usar RuleChainBuilder
- [ ] Testar cada regra

### Fase 4: Serviços 🔵
- [ ] Criar AuditService
- [ ] Atualizar main.py
- [ ] Testar fluxo completo

### Fase 5: Testes 🔵
- [ ] Criar fixtures
- [ ] Testes parametrizados
- [ ] Cobertura > 80%
- [ ] Testes de integração

### Fase 6: Configuração 🟢
- [ ] Setup Pydantic
- [ ] Criar .env
- [ ] Atualizar código
- [ ] Documentar

---

## ESTIMATIVA DE TEMPO

| Fase | Tempo Estimado | Prioridade |
|------|---------------|------------|
| 1. Fundações | 1-2 dias | ⚠️ Alta |
| 2. Scraper | 2-3 dias | ⚠️ Alta |
| 3. Auditor | 1-2 dias | 🔵 Média |
| 4. Serviços | 1 dia | 🔵 Média |
| 5. Testes | 2-3 dias | 🔵 Média |
| 6. Configuração | 1 dia | 🟢 Baixa |
| **TOTAL** | **8-12 dias** | |

---

## MÉTRICAS DE SUCESSO

Antes das melhorias:
```
├── Complexidade: Alta (15-20 por função)
├── Cobertura: ~30%
├── Manutenibilidade: Baixa
└── Performance: ~10s por NFe
```

Depois das melhorias:
```
├── Complexidade: Baixa (3-5 por função) ✓
├── Cobertura: ~80% ✓
├── Manutenibilidade: Alta ✓
└── Performance: ~6s por NFe (-40%) ✓
```

---

## PRÓXIMOS PASSOS (FUTURO)

### Melhorias Avançadas
1. API REST com FastAPI
2. Interface web com Streamlit
3. Processamento paralelo (multiprocessing)
4. Cache de resultados SEFAZ
5. Geração de relatórios PDF
6. Dashboard de métricas
7. Notificações por email
8. Integração CI/CD

### Documentação
1. README completo
2. Docstrings em todas as funções
3. Guia de contribuição
4. Diagramas de arquitetura
5. Exemplos de uso
6. FAQ

---

## COMANDOS ÚTEIS

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar testes
pytest tests/ -v

# Cobertura
pytest tests/ --cov=src

# Lint
pip install flake8 black
flake8 src/
black src/

# Type checking
pip install mypy
mypy src/

# Executar aplicação
python main.py
```

---

## RECURSOS

- **Código de Exemplo:** Consulte os arquivos gerados:
  - `audit_rules_refatorado.py` - Strategy Pattern
  - `scraper_refatorado.py` - Scraper modularizado
  - `audit_service_com_testes.py` - Serviços e testes
  
- **Documentação:**
  - `ANALISE_COMPLETA.md` - Análise detalhada
  - `CORRECOES_CFOP_CST.md` - Correções específicas

- **Testes:**
  - Execute `test_scraper_v4.py` para validar scraper
  - Execute `diagnose_structure.py` para debug

---

## CONTATO E SUPORTE

Em caso de dúvidas durante a implementação:
1. Consulte a documentação gerada
2. Execute os scripts de diagnóstico
3. Revise os exemplos de código
4. Verifique os logs em `logs/`

Boa implementação! 🚀
