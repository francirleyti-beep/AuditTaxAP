# AuditTaxAP 📊

Sistema profissional de auditoria fiscal automatizada para o estado do Amapá. O sistema realiza o cruzamento de dados entre o XML da NF-e e o Memorial de Cálculo da SEFAZ-AP, identificando divergências em ICMS Normal, ICMS ST, Antecipação e Benefícios SUFRAMA.

## 🚀 Arquitetura do Sistema

O projeto segue os princípios da **Clean Architecture**, dividido em:

- **Frontend:** React (TypeScript, TailwindCSS, Lucide Icons).
- **Backend API:** FastAPI (Python 3.9).
- **Worker:** Celery + Redis para processamento assíncrono de scraping e auditoria.
- **Infrastructure:** Selenium (Chrome Standalone) para extração de dados da SEFAZ.
- **Database:** SQLite (via SQLAlchemy) para histórico e auditorias.

## 🛠️ Tecnologias Utilizadas

- **Core:** Python 3.9, FastAPI, Celery, SQLAlchemy.
- **Auditoria:** Regras de negócio desacopladas, Recálculo Matemático Independente.
- **Scraping:** Selenium, BeautifulSoup4.
- **DevOps:** Docker, Docker Compose.

## 📋 Funcionalidades Principais

- [x] **Diferenciação Fiscal:** Distingue entre ICMS Normal (Operação Própria) e ICMS ST.
- [x] **Lógica SUFRAMA:** Cálculo preciso de desoneração e crédito teórico.
- [x] **Recálculo Independente:** Valida se a SEFAZ cobrou o valor matematicamente esperado.
- [x] **Dashboard:** Visualização clara de divergências com filtros e gráficos.
- [x] **Histórico:** Registro permanente de todas as auditorias realizadas.
- [x] **Modo Escuro:** Interface otimizada para alta produtividade em qualquer ambiente.

## ⚙️ Como Rodar

### Requisitos
- Docker e Docker Compose instalados.

### Passo a Passo
1. Clone o repositório.
2. Certifique-se de que o arquivo `.env` existe (use o `.env.example` como base).
3. Execute o comando:
   ```bash
   docker compose up -d --build
   ```
4. Acesse o sistema em: `http://localhost:3000`

## 📂 Estrutura de Pastas

- `src/core/`: Regras de auditoria e lógica tributária (Domain Logic).
- `src/infrastructure/`: Scrapers e leitores de XML.
- `src/domain/`: DTOs e modelos de dados universais.
- `backend/api/`: Endpoints e rotas da API.
- `frontend/`: Aplicação React.
- `tools/`: Scripts de diagnóstico e utilitários de desenvolvimento.

---
© 2026 AuditTax AP - Todos os direitos reservados.
