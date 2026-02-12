import csv
from datetime import datetime
from src.domain.dtos import AuditResultDTO

class ReportGenerator:
    def generate_csv(self, audit_results: list[AuditResultDTO], output_path: str = "relatorio_auditoria.csv"):
        """
        Gera um relatório CSV com os resultados da auditoria.
        """
        
        # Adiciona timestamp no nome se não fornecido
        if output_path == "relatorio_auditoria.csv" or output_path == "relatorio_auditoria.xlsx":
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"relatorio_auditoria_{ts}.csv"
            
        try:
            with open(output_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["Item", "Produto", "Status", "Divergências", "Detalhes"])
                writer.writeheader()
                
                for res in audit_results:
                    status = "OK" if res.is_compliant else "DIVERGENTE"
                    
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
                    
                    writer.writerow(row)

            print(f"\n[Relatório] Arquivo gerado com sucesso: {output_path}")
            return output_path
        except Exception as e:
            print(f"\n[Erro] Falha ao gerar CSV: {e}")
            return None
