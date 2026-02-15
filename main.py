import sys
import os
import logging
from src.utils.logging_config import setup_logging
from src.services.audit_service import AuditService
from src.domain.exceptions import AuditTaxException
from src.utils.config import Config

# Configura path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    # 1. Configurar Logging
    log_file = setup_logging(log_level=Config.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    
    print("=== AuditTax AP - Auditoria Fiscal ===")
    print(f"Log registrado em: {log_file}")
    
    # 2. Obter input
    xml_path = input("Digite o caminho do arquivo XML (ex: tests/samples/nfe_sample.xml): ").strip()
    if not xml_path:
        xml_path = os.path.join("tests", "samples", "nfe_sample.xml")
        print(f"Usando arquivo padrão: {xml_path}")
    
    if not os.path.exists(xml_path):
        logger.error(f"Arquivo não encontrado: {xml_path}")
        return

    nfe_key = input("Chave NFe (Opcional, Enter para detectar automática): ").strip()
    
    # 3. Executar Serviço
    try:
        service = AuditService()
        # Retorna: report_path, audit_results, consistency_errors, invoice_dto
        result = service.process_audit(xml_path, nfe_key)
        report_path = result[0]
        
        print("\n=== SUCESSO! ===")
        print(f"Relatório gerado com sucesso: {report_path}")
        
    except AuditTaxException as e:
        logger.error(f"Erro de Auditoria: {e}")
        print(f"\n[ERRO] Falha na auditoria: {e}")
        
    except Exception as e:
        logger.critical(f"Erro inesperado: {e}", exc_info=True)
        print(f"\n[CRITICO] Erro não tratado: {e}")

if __name__ == "__main__":
    main()
