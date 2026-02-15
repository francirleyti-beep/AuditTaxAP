# Plano de Implementação - Evolução DTOs e Validações

## Objetivo

# Plano de Implementação: Integração Frontend & Evolução do Backend

Este plano detalha as alterações necessárias para refletir a nova lógica de extração e validação (backend) na interface do usuário (frontend).

## 1. Backend (API & Banco de Dados)

### A. Atualização de Modelos (`backend/core/models.py`)

Precisamos armazenar os novos dados extraídos (Cabeçalho da Nota) e os erros de validação interna.

- **Tabela `audits`**:
  - Adicionar coluna `invoice_header` (JSON): Para armazenar Emitente, Destinatário, Totais, etc.
  - Adicionar coluna `consistency_errors` (JSON): Para armazenar lista de erros de validação interna.
- **Tabela `audit_items`**:
  - Adicionar coluna `details` (JSON): Para armazenar `qtd`, `valor_unitario`, `descricao_completa`, `ncm`, `cest`, `cfop`, etc.

### B. Atualização do Worker (`backend/api/celery_worker.py`)

O retorno do `AuditService.process_audit` mudou de 2 para 3 valores.

- **Correção Crítica**: Atualizar desempacotamento: `report, results, errors = service.process_audit(...)`.
- **Persistência**:
  - Salvar `invoice_header` extraído do `XMLReader` (precisaremos expor isso no Service ou ler novamente). *Melhoria: O Service deve retornar o DTO completo ou o Worker deve extrair antes.*
  - Salvar `consistency_errors` na coluna correspondente.
  - Salvar detalhes do item (`FiscalItemDTO`) na coluna `details` dos itens.

### C. Atualização da API (`backend/api/routes.py`)

- **Endpoint `GET /audit/{id}/results`**:
  - Incluir `invoice_header` e `consistency_errors` na resposta JSON.
  - Incluir os campos detalhados (`details`) dentro da lista de itens.

## 2. Frontend (React/TypeScript)

### A. Tipagem (`src/types/audit.ts`)

Atualizar interfaces para refletir a nova resposta da API.

- `Audit`: Adicionar `invoice_header` e `consistency_errors`.
- `AuditItem`: Adicionar campos de detalhe (qty, unit_price, description).
- `ConsistencyError`: Nova interface.

### B. Componentes

1. **`InvoiceHeader.tsx`** (Novo): Card no topo do dashboard exibindo:
    - Número/Série, Data Emissão.
    - Emitente e Destinatário (CNPJ/Nome).
    - Totais (Valor Nota, Valor Produtos, ICMS).
2. **`ConsistencyAlert.tsx`** (Novo):
    - Exibir alerta vermelho se `consistency_errors` > 0.
    - Lista expansível com os erros encontrados no XML.
3. **`AuditResultsTable.tsx`** (Atualização):
    - Adicionar colunas: Descrição, Qtd, Valor Unit.
    - Melhorar formatação de moeda.

## 3. Plano de Execução

### Fase 1: Backend (Prioridade Alta - Fix Broker)

1. [ ] Alterar `AuditService` para retornar `InvoiceDTO` completo junto com resultados (ou extrair no Worker).
2. [ ] Atualizar `models.py` (Adicionar colunas JSON).
3. [ ] Atualizar `celery_worker.py` para lidar com a nova tupla de retorno e salvar dados extras.
4. [ ] Atualizar `routes.py` para expor novos dados.

### Fase 2: Frontend

5. [ ] Atualizar Interfaces TypeScript.
2. [ ] Criar componente `InvoiceHeader`.
3. [ ] Criar componente `ConsistencyAlert`.
4. [ ] Atualizar tabela de resultados.

### Fase 3: Validação

9. [ ] Rodar Auditoria Completa via Interface.
2. [ ] Verificar se dados do cabeçalho aparecem.
3. [ ] Verificar se erros de consistência aparecem.
