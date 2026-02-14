import logging
import time
import io
import re
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

from src.utils.config import Config

class SeleniumDriverManager:
    """
    Gerencia o ciclo de vida do WebDriver Selenium.
    Responsável por abrir, navegar e extrair o HTML da página.
    """
    
    URL_SEFAZ = Config.SEFAZ_URL
    
    def __init__(self, headless: bool = False, remote_url: Optional[str] = None):
        self.headless = headless
        self.remote_url = remote_url or Config.SELENIUM_REMOTE_URL
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
        
        # Opções para evitar detecção de bot
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
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

    def resolve_captcha_and_submit(self, nfe_key: str, max_retries: int = 10):
        """
        Tenta resolver o captcha e submeter o formulário automaticamente.
        """
        if not self.driver:
            raise RuntimeError("Driver não inicializado")

        if not pytesseract or not Image:
            self.logger.warning("Bibliotecas de OCR não encontradas. Solicitando input manual.")
            return self.wait_for_manual_input()

        for attempt in range(max_retries):
            self.logger.info(f"Tentativa de automação {attempt + 1}/{max_retries}")
            
            try:
                # 1. Encontrar campos
                key_input = self._find_input_by_candidates([
                    "chave", "nfe", "txtChave", "chaveAcesso", "nfeKey",
                    "txtChaveAcesso", "edtChave", "NFe", "chave_acesso_nfe",
                    "Chave de Acesso", "Chave de Acesso da NF-e"
                ])
                
                # Se não achar o campo da chave, debug e erro
                if not key_input:
                    self.logger.warning("Campo da Chave NFe não encontrado.")
                    self.logger.warning(f"URL Atual: {self.driver.current_url}")
                    self.logger.warning("DUMPING PAGE SOURCE (First 2000 chars):")
                    self.logger.warning(self.driver.page_source[:2000])
                    
                    if self._is_results_page():
                        return
                    raise RuntimeError("Campo da Chave NFe não encontrado no formulário.")

                # 2. Preencher Chave
                key_input.clear()
                key_input.send_keys(nfe_key)
                
                # 3. Captcha
                captcha_img = self._find_captcha_image()
                if not captcha_img:
                    # Pode ser que não tenha captcha
                    self.logger.info("Imagem de captcha não encontrada. Tentando submeter sem captcha.")
                else:
                    captcha_text = self._solve_captcha(captcha_img)
                    self.logger.info(f"Captcha lido: {captcha_text}")
                    
                    # Encontrar o input do captcha usando múltiplas estratégias
                    captcha_input = self._find_captcha_input(key_input)
                    
                    if captcha_input:
                        captcha_input.clear()
                        captcha_input.send_keys(captcha_text)
                        self.logger.info("Captcha preenchido no campo.")
                    else:
                        self.logger.error("CAMPO DO CAPTCHA NÃO ENCONTRADO! O formulário será enviado sem captcha.")
                
                # 4. Submeter
                submit_btn = self._find_submit_button()
                if submit_btn:
                    submit_btn.click()
                else:
                    # Tenta submeter pelo input da chave
                    key_input.submit()
                
                # 5. Verificar Resultado
                if self._wait_for_results(timeout=5):
                    self.logger.info("Acesso realizado com sucesso!")
                    return
                
                # Se chegou aqui, falhou (provavelmente captcha incorreto)
                self.logger.warning(f"Tentativa {attempt + 1} falhou. Recarregando página para novo captcha...")
                self._handle_error_messages()
                
                # Navegar de volta para a URL original (refresh não funciona após erro)
                self.driver.get(self.URL_SEFAZ)
                time.sleep(3)
                
            except Exception as e:
                self.logger.error(f"Erro na tentativa {attempt + 1}: {e}")
                
                # Se for a última tentativa, tenta resetar a página antes de lançar o erro
                if attempt == max_retries - 1:
                    try:
                        self.logger.warning("Falha final. Resetando página...")
                        self._handle_error_messages()
                        self.driver.get(self.URL_SEFAZ)
                    except:
                        pass
                    raise

                # Recuperar: navegar para URL nova
                try:
                    self._handle_error_messages()
                    self.driver.get(self.URL_SEFAZ)
                    time.sleep(3)
                except:
                    pass

        # Caso saia do loop sem sucesso (improvável com o raise acima, mas por segurança)
        try:
            self.driver.get(self.URL_SEFAZ)
        except:
            pass
        raise RuntimeError("Falha ao resolver captcha automaticamente após várias tentativas.")

    def wait_for_manual_input(self):
        """Fallback: Aguarda interação do usuário."""
        self.logger.info("Aguardando input manual...")
        if self._wait_for_results(timeout=300):
            return
        raise RuntimeError("Tempo excedido para input manual.")

    def get_page_source(self) -> str:
        if not self.driver: raise RuntimeError("Driver não inicializado")
        return self.driver.page_source
    
    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    # --- Helpers ---

    def _find_input_by_candidates(self, candidates: list, timeout: int = 10) -> Optional[webdriver.remote.webelement.WebElement]:
        """
        Procura input por nome, id ou placeholder com espera explícita.
        Tenta também procurar dentro de iframes se não encontrar no main content.
        """
        end_time = time.time() + timeout
        
        while time.time() < end_time:
            # 1. Tenta no conteúdo principal
            element = self._search_candidates(candidates)
            if element: return element
            
            # 2. Tenta em iframes
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for i, iframe in enumerate(iframes):
                try:
                    self.driver.switch_to.frame(iframe)
                    element = self._search_candidates(candidates)
                    if element:
                        self.logger.info(f"Elemento encontrado no iframe {i}")
                        return element
                    self.driver.switch_to.default_content()
                except Exception:
                    self.driver.switch_to.default_content()
            
            time.sleep(0.5)
            
        return None

    def _search_candidates(self, candidates):
        for name in candidates:
            try: return self.driver.find_element(By.ID, name)
            except NoSuchElementException: pass
            try: return self.driver.find_element(By.NAME, name)
            except NoSuchElementException: pass
            try: return self.driver.find_element(By.XPATH, f"//input[contains(@placeholder, '{name}')]")
            except NoSuchElementException: pass
        return None

    def _find_captcha_image(self):
        """Encontra imagem que parece ser um captcha."""
        candidates = [
            "//img[contains(@src, 'memo_captcha.php')]", 
            "//img[contains(@src, 'captcha')]", 
            "//img[contains(@src, 'image')]", 
            "//img[contains(@id, 'captcha')]"
        ]
        for xpath in candidates:
            try: return self.driver.find_element(By.XPATH, xpath)
            except NoSuchElementException: pass
        return None

    def _find_captcha_input(self, key_input_element):
        """
        Encontra o campo de texto do captcha usando múltiplas estratégias.
        """
        # Estratégia 1: Buscar por name/id comuns
        candidates = ["captcha", "codigo", "security", "textoImagem", "txtCaptcha", "palavraseg"]
        for name in candidates:
            try: return self.driver.find_element(By.ID, name)
            except NoSuchElementException: pass
            try: return self.driver.find_element(By.NAME, name)
            except NoSuchElementException: pass

        # Estratégia 2: Input do tipo text/search perto da imagem do captcha (XPath following-sibling)
        captcha_xpaths = [
            "//img[contains(@src, 'memo_captcha')]/following::input[@type='text'][1]",
            "//img[contains(@src, 'captcha')]/following::input[@type='text'][1]",
            "//img[contains(@src, 'memo_captcha')]/following::input[1]",
            "//img[contains(@src, 'captcha')]/following::input[1]",
        ]
        for xpath in captcha_xpaths:
            try:
                el = self.driver.find_element(By.XPATH, xpath)
                if el != key_input_element:
                    self.logger.info(f"Captcha input encontrado via XPath: {xpath}")
                    return el
            except NoSuchElementException:
                pass

        # Estratégia 3: Pegar TODOS os inputs de texto e escolher o que NÃO é o campo da chave
        all_text_inputs = self.driver.find_elements(By.XPATH, "//input[@type='text']")
        self.logger.info(f"Total de inputs text na página: {len(all_text_inputs)}")
        for inp in all_text_inputs:
            if inp != key_input_element:
                attr_name = inp.get_attribute('name')
                attr_id = inp.get_attribute('id')
                self.logger.info(f"Candidato captcha input: name='{attr_name}', id='{attr_id}'")
                return inp

        # Estratégia 4: Qualquer input que não seja hidden, submit, ou o campo da chave
        all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
        self.logger.info(f"Total de inputs na página: {len(all_inputs)}")
        for inp in all_inputs:
            inp_type = inp.get_attribute('type') or 'text'
            if inp_type not in ('hidden', 'submit', 'button', 'image') and inp != key_input_element:
                self.logger.info(f"Fallback captcha input: type='{inp_type}', name='{inp.get_attribute('name')}', id='{inp.get_attribute('id')}'")
                return inp

        return None

    def _find_submit_button(self):
        candidates = ["//input[@type='submit']", "//button[contains(text(), 'Consultar')]", "//button[contains(text(), 'Pesquisar')]"]
        for xpath in candidates:
            try: return self.driver.find_element(By.XPATH, xpath)
            except NoSuchElementException: pass
        return None

    def _solve_captcha(self, element) -> str:
        """Captura screenshot do elemento e resolve OCR com pré-processamento."""
        from PIL import ImageOps, ImageFilter  # Import inside

        # 1. Captura imagem
        png = element.screenshot_as_png
        img = Image.open(io.BytesIO(png))
        
        # 2. Pré-processamento
        # Converter para escala de cinza
        img = img.convert('L')
        
        # Aumentar tamanho (3x é suficiente, 4x pode distorcer)
        width, height = img.size
        img = img.resize((width * 3, height * 3), Image.Resampling.LANCZOS)
        
        # Binarização (Threshold)
        # Manter pixels claros
        img = img.point(lambda p: p > 140 and 255)
        
        # Dilatação (Engrossar caracteres brancos)
        img = img.filter(ImageFilter.MaxFilter(3))
        
        # Inverter cores (Branco no Preto -> Preto no Branco) para o Tesseract
        img = ImageOps.invert(img)
        
        # Sharpen para definir bordas (v vs y, 4 vs h etc)
        img = img.filter(ImageFilter.SHARPEN)
        img = img.filter(ImageFilter.SHARPEN)
        
        # 3. OCR
        # --psm 7: Trata como uma linha única de texto (lida melhor com espaços)
        custom_config = r'--psm 7 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        text = pytesseract.image_to_string(img, config=custom_config)
        
        # 4. Limpeza
        clean_text = re.sub(r'[^a-zA-Z0-9]', '', text)
        
        self.logger.info(f"OCR Raw: '{text.strip()}' -> Clean: '{clean_text}'")
        return clean_text

    def _wait_for_results(self, timeout=10) -> bool:
        """Aguarda elemento da tabela de resultados."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'IMPOSTO COBRADO')]"))
            )
            return True
        except TimeoutException:
            return False

    def _is_results_page(self) -> bool:
        try:
            self.driver.find_element(By.XPATH, "//*[contains(text(), 'IMPOSTO COBRADO')]")
            return True
        except NoSuchElementException:
            return False

    def _handle_error_messages(self):
        """Tenta fechar alerts ou detectar mensagens de erro."""
        try:
            alert = self.driver.switch_to.alert
            self.logger.warning(f"Alert detectado: {alert.text}")
            alert.accept()
        except:
            pass
