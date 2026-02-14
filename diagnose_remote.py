from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import sys
import time

# Configure logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

URL = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
REMOTE_URL = "http://selenium-chrome:4444/wd/hub"

def diagnose():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    logger.info(f"Connecting to {REMOTE_URL}...")
    try:
        driver = webdriver.Remote(command_executor=REMOTE_URL, options=options)
        try:
            logger.info(f"Navigating to {URL}...")
            driver.get(URL)
            logger.info(f"Page Title: {driver.title}")
            
            # Wait a bit
            time.sleep(2)

            # Inputs
            inputs = driver.find_elements(By.TAG_NAME, "input")
            logger.info(f"== Found {len(inputs)} input elements ==")
            for i, inp in enumerate(inputs):
                 logger.info(f"Input {i}: id='{inp.get_attribute('id')}', name='{inp.get_attribute('name')}', placeholder='{inp.get_attribute('placeholder')}'")

            # Iframes
            iframes = driver.find_elements(By.TAG_NAME, "iframe")
            logger.info(f"== Found {len(iframes)} iframes ==")
            for i, fr in enumerate(iframes):
                 logger.info(f"Iframe {i}: src='{fr.get_attribute('src')}'")

            # HTML Source
            print("\n--- HTML SOURCE START ---")
            print(driver.page_source)
            print("--- HTML SOURCE END ---\n")
            
        finally:
            driver.quit()
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == "__main__":
    diagnose()
