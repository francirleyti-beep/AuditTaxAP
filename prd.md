# Product Requirements Document (PRD) - AuditTax AP

## 1. Visão Geral do Produto
O **AuditTax AP** é uma aplicação web de conformidade fiscal projetada para varejistas e contadores que operam no estado do Amapá. O software automatiza a comparação entre os impostos destacados na Nota Fiscal Eletrônica (XML de Entrada) e o cálculo de cobrança exigido pela SEFAZ AP (Memorial de Cálculo), identificando pagamentos indevidos ou riscos de autuação fiscal.

## 2. O Problema
- O cálculo do ICMS-ST no Amapá envolve variáveis complexas: Desoneração da SUFRAMA, MVA Ajustada e Crédito Presumido.
- A SEFAZ AP disponibiliza o "Memorial de Cálculo" via web, protegido por Captcha visual.
- A conferência manual item a item é inviável para alto volume de notas.
- Divergências de centavos ou erros de cadastro (NCM/CEST) geram multas pesadas.

## 3. Público Alvo
- Analistas Fiscais e Contadores.
- Supermercados e Varejistas do Regime Normal e Simples Nacional no AP.

## 4. Fluxos do Usuário (User Journey)

### Fluxo Principal: Auditoria de Nota Fiscal
1. **Upload:** Usuário acessa a interface web (`localhost:3000`) e arrasta ou seleciona um arquivo XML de NFe.
2. **Iniciar Auditoria:** Usuário clica em "Iniciar Auditoria". O sistema exibe progresso em tempo real via WebSocket.
3. **Processamento Automático (Backend):**
   - O worker Celery recebe a tarefa.
   - `XMLReader` extrai os itens e a Chave da NFe do XML.
   - `SeleniumDriverManager` abre um navegador remoto (Selenium Grid), navega até a página da SEFAZ AP.
   - O sistema preenche automaticamente a Chave da NFe.
   - O sistema **resolve automaticamente o Captcha** via OCR (Tesseract) com pré-processamento de imagem (escala, binarização, inversão, dilatação e sharpening). Em caso de falha, tenta até 10 vezes com novo captcha.
   - `SefazScraper` extrai o HTML da tabela de resultados do Memorial de Cálculo.
4. **Auditoria:** O `AuditEngine` cruza os dados do XML com os dados extraídos da SEFAZ, aplicando 7 regras de validação.
5. **Resultado:**
   - O sistema gera um relatório CSV destacando divergências.
   - A interface exibe os resultados com tabela detalhada, gráficos (dashboard) e botão de download.
   - Os resultados ficam salvos no histórico para consulta posterior.

### Fluxo Secundário: Histórico de Auditorias
1. Usuário clica em "Histórico" na interface.
2. O sistema exibe lista de auditorias anteriores com status, data e resumo.
3. Usuário pode clicar em uma auditoria para ver os resultados completos e baixar o relatório.

## 5. Requisitos Funcionais (RF)

| ID   | Requisito              | Descrição | Status |
|------|------------------------|-----------|--------|
| RF01 | Parsing XML            | Ler tags complexas de NFe 4.0 (incluindo `vICMSDeson`, `CEST`, `motDesICMS`). Extrai automaticamente a Chave de Acesso. | ✅ Implementado |
| RF02 | Scraping Automatizado  | Navegar na SEFAZ AP, preencher chave NFe, resolver captcha **automaticamente via OCR** e extrair tabela HTML. | ✅ Implementado |
| RF03 | Match de Itens         | Vincular itens do XML com itens da SEFAZ usando índice de item. | ✅ Implementado |
| RF04 | Auditoria Cadastral    | Validar igualdade de NCM, CEST, CFOP e CST (com normalização). | ✅ Implementado |
| RF05 | Auditoria de Valores   | Comparar valores monetários (Tax Value) com tolerância configurável (padrão: R$ 0,05). | ✅ Implementado |
| RF06 | Validação MVA          | Comparar percentual de MVA entre XML e SEFAZ (tolerância de 0,01%). | ✅ Implementado |
| RF07 | Validação SUFRAMA      | Verificar consistência do benefício SUFRAMA entre XML e SEFAZ. | ✅ Implementado |
| RF08 | Interface Web          | Frontend React com dark mode, drag-and-drop para upload, progresso em tempo real via WebSocket. | ✅ Implementado |
| RF09 | Histórico de Auditorias| Persistência de auditorias em banco de dados com consulta via interface. | ✅ Implementado |
| RF10 | Download de Relatórios | Download do relatório CSV diretamente pela interface web. | ✅ Implementado |

## 6. Requisitos Não Funcionais (RNF)

| ID    | Requisito          | Descrição |
|-------|--------------------|-----------|
| RNF01 | Deploy via Docker  | Toda a stack executa via `docker-compose up` com 5 serviços. |
| RNF02 | Rate Limiting      | API protegida com `fastapi-limiter` via Redis. |
| RNF03 | Processamento Async| Auditorias são processadas assincronamente via Celery workers. |
| RNF04 | Progresso Real-Time| WebSocket (Redis Pub/Sub) para atualizações de progresso em tempo real. |
| RNF05 | Tolerância a Falhas| Retry automático de captcha (até 10 tentativas) com recuperação de estado. |

## 7. Alterações em Relação à V1 (Escopo Original)
- ~~Quebra automática de Captcha~~ → **Implementado** via Tesseract OCR com pré-processamento avançado de imagem.
- ~~Software local/desktop~~ → **Aplicação web** com frontend React e backend FastAPI, conteinerizada com Docker.
- ~~Relatório Excel~~ → Relatório CSV (migração para Excel possível no futuro).
- ~~Sem banco de dados~~ → SQLite com SQLAlchemy para persistência de auditorias e histórico.

## 8. Fora de Escopo (Atual)
- Retificação automática da nota (Escrita).
- Suporte a outros estados além do Amapá.
- Armazenamento em nuvem / deploy em produção.
- Processamento em lote (múltiplos XMLs simultaneamente).