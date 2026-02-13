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
    
    def __init__(self, headless: bool = False, remote_url: Optional[str] = None):
        self.headless = headless
        self.remote_url = remote_url or Config.SELENIUM_REMOTE_URL # Add to config
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
            if self.remote_url:
                self.logger.info(f"Conectando ao WebDriver Remoto em: {self.remote_url}")
                self.driver = webdriver.Remote(
                    command_executor=self.remote_url,
                    options=options
                )
            else:
                self.driver = webdriver.Chrome(options=options)
            
            self.driver.get(self.URL_SEFAZ)
            self.logger.info(f"Acessado: {self.URL_SEFAZ}")
        except Exception as e:
            self.logger.error(f"Falha ao iniciar Selenium: {e}")
            raise

    def wait_for_manual_input(self):
        """
        Aguarda o carregamento da página de resultados após o captcha.
        Substitui o input manual por espera explícita do elemento chave.
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        self.logger.info("Aguardando resolução do Captcha e carregamento da página...")
        
        try:
            # Aguarda até 300 segundos (5 minutos) para o usuário resolver o captcha
            # Procura por "IMPOSTO COBRADO" que é um cabeçalho da tabela de resultados
            # "MEMORIAL" sozinha dava match na página de login ("CONSULTA MEMORIAL...")
            WebDriverWait(self.driver, 300).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'IMPOSTO COBRADO')]"))
            )
            self.logger.info("Página de resultados detectada (Tabela encontrada)!")
            # Pequeno delay para garantir renderização completa
            time.sleep(2)
            
        except Exception as e:
            self.logger.error("Timeout aguardando a página de resultados.")
            raise RuntimeError("Tempo excedido para resolução do Captcha. Tente novamente.") from e
    
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
