# Tabela Mestra de Mapeamento: XML NFe vs. Memorial de Cálculo SEFAZ AP

Entidade de Negócio,Campo no XML (Path lxml),Exemplo XML (Item 1),Estratégia de Extração HTML (Regex/Tag),Exemplo HTML (Item 1),Regra de Auditoria (PRD)
Índice do Item,"det.get(""nItem"")",1,Tag: <h2>  Regex: ITEM:(\d+),ITEM:1,RF03: Match de Itens  (Chave Primária de ligação)
Código Produto,prod.cProd,000205,Tag: Texto solto após <h2>  Lógica: h2.next_sibling.strip(),000205,RF03/RF04: Validação de Correspondência
Descrição,prod.xProd,QUEIJO PRATO...,Tag: <h5>Descricao Nota</h5>  Lógica: Texto na célula abaixo,QUEIJO PRATO...,Informativo (Debug Visual)
NCM,prod.NCM,04069020,Tag: Célula com <h5>NCM</h5>,04069020,RF04: Auditoria Cadastral
CEST,prod.CEST,1702400,Tag: Célula com <h5>CEST</h5>,1702400,RF04: Auditoria Cadastral
CST (ICMS),imposto.ICMS.*.CST,40,Tag: Célula com <h5>CST</h5>  Regex: ^(\d+),040,RF04: Validação Tributária
Valor Produto,prod.vProd,4508.16,"Regex: A\)\s*VALOR PRODUTO\s*=\s*([\d\.,]+)","4.508,16",RF05: Auditoria de Valores  (Base de partida do cálculo)
Benefício ZFM,ICMS*.vICMSDeson  (Quando motDesICMS=7),540.98,"Tag: Célula com <h5>BENEFICIO</h5>  Regex: BENEFICIO SUFRAMA\s*R\$\s*([\d\.,]+)","540,98",RF07: Validação SUFRAMA  (Crítico: Deve bater centavo a centavo)
MVA Aplicada,ICMS*.pMVAST  (Geralmente vazio no CST 40),0.00 (N/A),"Regex: ALIQUOTA MVA AJUSTADA.*?=\s*([\d\.,]+)%\)",39.51,RF06: Validação MVA  (Detecta penalidade por reclassificação)
Base Calc. ST,ICMS*.vBCST,0.00,"Regex: F\)\s*BASE.*?=\s*([\d\.,]+)","5.534,61",RF05: Auditoria Intermediária
Valor Final (ST),ICMS*.vICMSST,0.00,"Tag: <h2> vizinha de <h5>CALCULO VALOR(Sefaz)</h5>  Regex: R\$\s*([\d\.,]+)","455,25",RF05: Auditoria de Valores  (Divergência aqui = Guia a Pagar)
Alíquota Interna,ICMS*.pICMS,18.00 (Implícito),"Regex: ALIQUOTA INTERNA\s*=\s*([\d\.,]+)%",18%,Conferência de Parâmetros Legais

# Visão Fiscal Profissional

| Grupo Fiscal | Campo XML (XPath) | Tag XML | Campo DANFE / HTML | Descrição Fiscal | Obrigatório | Regra Fiscal | Conferência Contábil | Observações |
|--------------|------------------|---------|--------------------|------------------|-------------|--------------|----------------------|-------------|
| ICMS | /det/imposto/ICMS/*/orig | <orig> | Origem Mercadoria | Nacional / Importada | Sim | Código tabela ICMS | Conferir NCM | Impacta alíquota |
| ICMS | /det/imposto/ICMS/*/CST | <CST> | CST ICMS | Situação tributária | Sim (Regime Normal) | Tabela CST válida | Conferir CFOP | Define cálculo imposto |
| ICMS | /det/imposto/ICMS/*/CSOSN | <CSOSN> | CSOSN | Situação Simples Nacional | Sim (SN) | Tabela CSOSN | Conferir CRT emitente | Exclusivo SN |
| ICMS | /det/imposto/ICMS/*/modBC | <modBC> | Mod Base Cálculo | Forma cálculo BC | Condicional | Código válido | Conferir legislação UF | 0–3 geralmente |
| ICMS | /det/imposto/ICMS/*/vBC | <vBC> | Base ICMS | Base cálculo ICMS | Condicional | ≥ 0 | Recalcular base | Valor monetário |
| ICMS | /det/imposto/ICMS/*/pICMS | <pICMS> | Alíquota ICMS | % ICMS | Condicional | Conforme UF | Conferir tabela UF | Percentual |
| ICMS | /det/imposto/ICMS/*/vICMS | <vICMS> | Valor ICMS | Valor imposto | Condicional | BC × Alíquota | Recalcular | Pode ser zero |

| ICMS ST | /det/imposto/ICMS/*/vBCST | <vBCST> | Base ICMS ST | Base substituição | Condicional | ≥ 0 | Conferir MVA | ST operações específicas |
| ICMS ST | /det/imposto/ICMS/*/pICMSST | <pICMSST> | Alíquota ST | % ST | Condicional | Conforme protocolo | Conferir convênio ICMS | Percentual |
| ICMS ST | /det/imposto/ICMS/*/vICMSST | <vICMSST> | Valor ICMS ST | Valor ST | Condicional | Base × Alíquota | Recalcular | Substituição tributária |

| IPI | /det/imposto/IPI/IPITrib/CST | <CST> | CST IPI | Situação IPI | Condicional | Tabela CST IPI | Conferir NCM | Indústria / importação |
| IPI | /det/imposto/IPI/IPITrib/vBC | <vBC> | Base IPI | Base cálculo IPI | Condicional | ≥ 0 | Conferir cálculo | Monetário |
| IPI | /det/imposto/IPI/IPITrib/pIPI | <pIPI> | Alíquota IPI | % IPI | Condicional | Tabela TIPI | Conferir produto | Percentual |
| IPI | /det/imposto/IPI/IPITrib/vIPI | <vIPI> | Valor IPI | Valor imposto | Condicional | Base × Alíquota | Recalcular | Pode não existir |

| PIS | /det/imposto/PIS/*/CST | <CST> | CST PIS | Situação PIS | Sim | Tabela CST PIS | Conferir regime | Define tributação |
| PIS | /det/imposto/PIS/*/vBC | <vBC> | Base PIS | Base cálculo | Condicional | ≥ 0 | Conferir receita | Monetário |
| PIS | /det/imposto/PIS/*/pPIS | <pPIS> | Alíquota PIS | % PIS | Condicional | Conforme regime | Conferir cumulatividade | Percentual |
| PIS | /det/imposto/PIS/*/vPIS | <vPIS> | Valor PIS | Valor imposto | Condicional | Base × Alíquota | Recalcular | Monetário |

| COFINS | /det/imposto/COFINS/*/CST | <CST> | CST COFINS | Situação COFINS | Sim | Tabela CST COFINS | Conferir regime | Tributação receita |
| COFINS | /det/imposto/COFINS/*/vBC | <vBC> | Base COFINS | Base cálculo | Condicional | ≥ 0 | Conferir receita | Monetário |
| COFINS | /det/imposto/COFINS/*/pCOFINS | <pCOFINS> | Alíquota COFINS | % COFINS | Condicional | Conforme regime | Conferir cumulatividade | Percentual |
| COFINS | /det/imposto/COFINS/*/vCOFINS | <vCOFINS> | Valor COFINS | Valor imposto | Condicional | Base × Alíquota | Recalcular | Monetário |

| Totais | /total/ICMSTot/vProd | <vProd> | Total Produtos | Soma produtos | Sim | Soma itens | Recalcular total | Base NF |
| Totais | /total/ICMSTot/vNF | <vNF> | Total Nota | Valor final NF | Sim | Soma geral | Conferir financeiro | Valor final |
| Totais | /total/ICMSTot/vICMS | <vICMS> | Total ICMS | Soma ICMS | Condicional | Soma itens ICMS | Validar apuração | Tributação estadual |
| Totais | /total/ICMSTot/vST | <vST> | Total ICMS ST | Soma ST | Condicional | Soma itens ST | Validar apuração | ST geral |
| Totais | /total/ICMSTot/vPIS | <vPIS> | Total PIS | Soma PIS | Condicional | Soma itens PIS | Validar apuração | Federal |
| Totais | /total/ICMSTot/vCOFINS | <vCOFINS> | Total COFINS | Soma COFINS | Condicional | Soma itens COFINS | Validar apuração | Federal |
| Totais | /total/ICMSTot/vIPI | <vIPI> | Total IPI | Soma IPI | Condicional | Soma itens IPI | Validar apuração | Industrial |
