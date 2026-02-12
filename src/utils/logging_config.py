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
