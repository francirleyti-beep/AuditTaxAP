import csv
import logging
from datetime import datetime
from src.domain.dtos import AuditResultDTO, AuditDifference

class ReportGenerator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_csv(self, audit_results: list[AuditResultDTO], consistency_errors: list[AuditDifference] = None) -> str:
        """
        Gera um relatório CSV com os resultados da auditoria e erros de consistência.
        """
        if consistency_errors is None:
            consistency_errors = []

        # Adiciona timestamp no nome
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"relatorio_auditoria_{ts}.csv"
            
        try:
            with open(output_path, mode='w', newline='', encoding='utf-8-sig') as csv_file:
                fieldnames = ["Tipo", "Item", "Produto", "Status", "Campo Divergente", "Valor XML", "Valor SEFAZ/Calculado", "Mensagem"]
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                
                # 1. Erros de Consistência Interna
                for err in consistency_errors:
                    writer.writerow({
                        "Tipo": "CONSISTENCIA",
                        "Item": "-",
                        "Produto": "-",
                        "Status": "ERRO",
                        "Campo Divergente": err.field,
                        "Valor XML": err.xml_value,
                        "Valor SEFAZ/Calculado": err.sefaz_value,
                        "Mensagem": err.message
                    })

                # 2. Auditoria Cruzada (Item a Item)
                for res in audit_results:
                    status = "OK" if res.is_compliant else "DIVERGENTE"
                    
                    if res.is_compliant:
                        writer.writerow({
                            "Tipo": "AUDITORIA",
                            "Item": res.item_index,
                            "Produto": res.product_code,
                            "Status": "OK",
                            "Campo Divergente": "",
                            "Valor XML": "",
                            "Valor SEFAZ/Calculado": "",
                            "Mensagem": ""
                        })
                    else:
                        for diff in res.differences:
                            writer.writerow({
                                "Tipo": "AUDITORIA",
                                "Item": res.item_index,
                                "Produto": res.product_code,
                                "Status": "DIVERGENTE",
                                "Campo Divergente": diff.field,
                                "Valor XML": diff.xml_value,
                                "Valor SEFAZ/Calculado": diff.sefaz_value,
                                "Mensagem": diff.message
                            })
                            
            self.logger.info(f"Relatório gerado em: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Falha ao gerar CSV: {e}")
            raise
