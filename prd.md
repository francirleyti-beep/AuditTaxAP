# Product Requirements Document (PRD) - AuditTax AP

## 1. Visão Geral do Produto
O **AuditTax AP** é uma ferramenta de conformidade fiscal projetada para varejistas e contadores que operam no estado do Amapá. O software automatiza a comparação entre os impostos destacados na Nota Fiscal (XML de Entrada) e o cálculo de cobrança exigido pela SEFAZ AP (Memorial de Cálculo), identificando pagamentos indevidos ou riscos de autuação fiscal.

## 2. O Problema
- O cálculo do ICMS-ST no Amapá envolve variáveis complexas: Desoneração da SUFRAMA, MVA Ajustada e Crédito Presumido.
- A SEFAZ AP disponibiliza o "Memorial de Cálculo" via web, protegido por Captcha.
- A conferência manual item a item é inviável para alto volume de notas.
- Divergências de centavos ou erros de cadastro (NCM/CEST) geram multas pesadas.

## 3. Público Alvo
- Analistas Fiscais e Contadores.
- Supermercados e Varejistas do Regime Normal e Simples Nacional no AP.

## 4. Fluxos do Usuário (User Journey)

### Fluxo Principal: Auditoria de Lote
1. **Importação:** Usuário carrega uma pasta contendo XMLs de NFe.
2. **Conexão SEFAZ:**
   - O software abre um navegador controlado (Selenium).
   - O software preenche a Chave da NFe.
   - O software **pausa** e solicita que o usuário digite o Captcha visual.
   - O usuário confirma.
   - O software extrai o HTML da tabela de resultados.
3. **Processamento:** O sistema cruza os dados do XML com o HTML extraído.
4. **Resultado:** O sistema gera uma planilha Excel destacando em vermelho as divergências.

## 5. Requisitos Funcionais (RF)

| ID | Requisito | Descrição |
|---|---|---|
| RF01 | Parsing XML | Ler tags complexas de NFe 4.0 (incluindo `vICMSDeson`, `CEST`, `motDesICMS`). |
| RF02 | Scraping Híbrido | Navegar na SEFAZ AP, aguardar resolução de Captcha pelo humano, e extrair tabela HTML. |
| RF03 | Match de Itens | Algoritmo inteligente para vincular Item 1 do XML com Item X da SEFAZ (usando Código ou Ordem). |
| RF04 | Auditoria Cadastral | Validar igualdade de NCM, CEST, CFOP, CST e GTIN. |
| RF05 | Auditoria de Valores | Recalcular a cadeia de impostos (Base, MVA, Crédito, Débito) com tolerância de R$ 0,05. |
| RF06 | Detecção de Penalidade | Identificar se a SEFAZ alterou a MVA por erro de classificação (Ex: "Genérico"). |

## 6. Fora de Escopo (V1)
- Quebra automática de Captcha (Risco legal/técnico).
- Retificação automática da nota (Escrita).
- Suporte a outros estados além do Amapá.
- Armazenamento em nuvem (Software será local/desktop inicialmente).