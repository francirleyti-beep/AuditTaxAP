from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import logging
import sys

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

URL = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"

def diagnose_selenium():
    try:
        logger.info(f"Starting Selenium Diagnosis for {URL}...")
        
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--log-level=3")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        try:
            logger.info("Opening page...")
            driver.get(URL)
            logger.info(f"Page Title: {driver.title}")
            
            inputs = driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"== Found {len(inputs)} input elements ==")
            
            for i, inp in enumerate(inputs):
                try:
                    attr_id = inp.get_attribute('id')
                    attr_name = inp.get_attribute('name')
                    attr_placeholder = inp.get_attribute('placeholder')
                    logger.info(f"Input {i}: id='{attr_id}', name='{attr_name}', placeholder='{attr_placeholder}'")
                except Exception as e:
                    logger.error(f"Error inspecting input {i}: {e}")

            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"== Found {len(iframes)} iframes ==")
            for i, iframe in enumerate(iframes):
                try:
                    logger.info(f"Iframe {i}: src='{iframe.get_attribute('src')}'")
                except: pass
                
        finally:
            driver.quit()

    except Exception as e:
        logger.error(f"Selenium diagnosis failed: {e}")

if __name__ == "__main__":
    diagnose_selenium()
