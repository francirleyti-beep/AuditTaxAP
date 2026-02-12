import pandas as pd
from datetime import datetime
from src.domain.dtos import AuditResultDTO

class ReportGenerator:
    def generate_excel(self, audit_results: list[AuditResultDTO], output_path: str = "relatorio_auditoria.xlsx"):
        """
        Gera um relatório Excel com os resultados da auditoria.
        """
        data = []
        
        for res in audit_results:
            status = "OK" if res.is_compliant else "DIVERGENTE"
            
            # Base info
            row = {
                "Item": res.item_index,
                "Produto": res.product_code,
                "Status": status,
                "Divergências": "",
                "Detalhes": ""
            }
            
            if not res.is_compliant:
                diff_texts = [d.message for d in res.differences]
                row["Divergências"] = "; ".join(diff_texts)
                
                details = []
                for d in res.differences:
                    details.append(f"{d.field}: XML={d.xml_value} | SEFAZ={d.sefaz_value}")
                row["Detalhes"] = " || ".join(details)
            
            data.append(row)

        df = pd.DataFrame(data)
        
        # Adiciona timestamp no nome se não fornecido
        if output_path == "relatorio_auditoria.xlsx":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"relatorio_auditoria_{ts}.xlsx"
            
        try:
            df.to_excel(output_path, index=False)
            print(f"\n[Relatório] Arquivo gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            print(f"\n[Erro] Falha ao gerar Excel: {e}")
            return None
