import logging
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.infrastructure.sefaz.driver_manager import SeleniumDriverManager

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

def diagnose():
    try:
        logger.info("Starting diagnosis...")
        
        # Use remote URL since we are running inside docker network ideally, 
        # but if running via docker-compose exec, we establish connection to selenium container
        # The selenium container is named 'selenium-chrome' and port 4444.
        
        with SeleniumDriverManager(headless=True) as driver_mgr:
            logger.info("Accessing SEFAZ...")
            
            # Wait a bit for page load
            import time
            time.sleep(5)

            logger.info("Page Title: %s", driver_mgr.driver.title)
            
            # Inspect Inputs
            try:
                inputs = driver_mgr.driver.find_elements("tag name", "input")
                logger.info(f"== Found {len(inputs)} input elements ==")
                for i, inp in enumerate(inputs):
                    try:
                        attr_id = inp.get_attribute('id')
                        attr_name = inp.get_attribute('name')
                        attr_placeholder = inp.get_attribute('placeholder')
                        logger.info(f"Input {i}: id='{attr_id}', name='{attr_name}', placeholder='{attr_placeholder}'")
                    except Exception as e:
                        logger.error(f"Error inspecting input {i}: {e}")
            except Exception as e:
                 logger.error(f"Could not inspect inputs: {e}")

            # Inspect Iframes
            try:
                iframes = driver_mgr.driver.find_elements("tag name", "iframe")
                logger.info(f"== Found {len(iframes)} iframes ==")
            except Exception as e:
                logger.error(f"Could not inspect iframes: {e}")

    except Exception as e:
        logger.error(f"Diagnosis failed: {e}", exc_info=True)

if __name__ == "__main__":
    diagnose()
