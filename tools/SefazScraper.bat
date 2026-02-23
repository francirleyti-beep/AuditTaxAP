del src\infrastructure\sefaz_scraper.py
echo # Compatibilidade: Re-exporta SefazScraper da nova estrutura modular > src\infrastructure\sefaz_scraper.py
echo from src.infrastructure.sefaz.scraper import SefazScraper >> src\infrastructure\sefaz_scraper.py
echo. >> src\infrastructure\sefaz_scraper.py
echo __all__ = ["SefazScraper"] >> src\infrastructure\sefaz_scraper.py