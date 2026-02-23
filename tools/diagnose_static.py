import requests
import logging
from bs4 import BeautifulSoup
import sys

# Configure logging to file AND stdout
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("debug_static.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

URL = "http://www.sefaz.ap.gov.br/EMISSAO/memorial.php"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def diagnose_static():
    try:
        logger.info(f"Fetching {URL}...")
        resp = requests.get(URL, headers=HEADERS, timeout=30)
        logger.info(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.content, 'html.parser')
            logger.info(f"Page Title: {soup.title.string if soup.title else 'No Title'}")
            
            inputs = soup.find_all('input')
            logger.info(f"== Found {len(inputs)} input elements ==")
            for i, inp in enumerate(inputs):
                logger.info(f"Input {i}: id='{inp.get('id')}', name='{inp.get('name')}', placeholder='{inp.get('placeholder')}', type='{inp.get('type')}'")
                
            iframes = soup.find_all('iframe')
            logger.info(f"== Found {len(iframes)} iframes ==")
            for i, iframe in enumerate(iframes):
                logger.info(f"Iframe {i}: src='{iframe.get('src')}'")

    except Exception as e:
        logger.error(f"Static diagnosis failed: {e}")

if __name__ == "__main__":
    diagnose_static()
