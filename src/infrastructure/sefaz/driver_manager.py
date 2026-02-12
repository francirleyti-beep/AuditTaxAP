import logging
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from src.utils.config import Config

class SeleniumDriverManager:
    """
    Gerencia o ciclo de vida do WebDriver Selenium.
    Responsável por abrir, navegar e extrair o HTML da página.
    """
    
    # URL Baseada no código anterior
    URL_SEFAZ = Config.SEFAZ_URL
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.logger = logging.getLogger(__name__)
    
    def __enter__(self):
        """Context manager: abre driver."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager: fecha driver."""
        self.close()
    
    def open(self):
        """Inicializa e abre o WebDriver."""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
        
        self.logger.info("Inicializando WebDriver...")
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.get(self.URL_SEFAZ)
            self.logger.info(f"Acessado: {self.URL_SEFAZ}")
        except Exception as e:
            self.logger.error(f"Falha ao iniciar Selenium: {e}")
            raise

    def wait_for_manual_input(self):
        """Aguarda input manual do usuário (captcha, etc)."""
        print("\n>>> AÇÃO MANUAL NECESSÁRIA <<<")
        print("1. O navegador foi aberto.")
        print("2. Preencha o Captcha e clique em Consultar.")
        print("3. Aguarde a tabela de resultados aparecer.")
        input("Pressione ENTER aqui quando a tabela estiver visível no navegador...")
    
    def get_page_source(self) -> str:
        """Retorna HTML da página atual."""
        if not self.driver:
            raise RuntimeError("Driver não inicializado")
        
        html = self.driver.page_source
        self.logger.info(f"HTML capturado: {len(html)} chars")
        return html
    
    def close(self):
        """Fecha o WebDriver."""
        if self.driver:
            self.logger.info("Fechando WebDriver...")
            self.driver.quit()
            self.driver = None
