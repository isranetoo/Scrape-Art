import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
from urllib.parse import urlparse, parse_qs

BASE_URL = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'

class JurisprudenciaSession:
    def __init__(self):
        self.browser = None
        self.session = requests.Session()
        self.challenge_token = None
        self.captcha_response = None

    def setup_browser(self):
        """Setup Chrome browser with appropriate options"""
        options = webdriver.ChromeOptions()
        
        options.add_argument('--start-maximized')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        
        options.set_capability(
            "goog:loggingPrefs",
            {
                "browser": "ALL",
                "performance": "ALL",
            }
        )
        
        service = Service(ChromeDriverManager().install())
        
        try:
            self.browser = webdriver.Chrome(
                service=service,
                options=options
            )
            print("Browser setup successful")
        except Exception as e:
            print(f"Error setting up browser: {e}")
            raise

    def get_network_requests(self):
        """Get all network requests containing 'tokenDesafio'"""
        try:
            logs = self.browser.get_log('performance')
            for entry in logs:
                log_data = json.loads(entry.get('message', {}))
                message = log_data.get('message', {})
                if message.get('method') == 'Network.requestWillBeSent':
                    request = message.get('params', {}).get('request', {})
                    url = request.get('url', '')
                    if 'tokenDesafio' in url:
                        print(f"Found token URL: {url}")
                        return url
        except Exception as e:
            print(f"Error getting network requests: {e}")
        return None

    def wait_for_token_in_page(self, timeout=30):
        """Wait and extract token from page source or network requests"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                page_source = self.browser.page_source
                if 'tokenDesafio' in page_source:
                    print("Found token in page source")
                
                token_url = self.get_network_requests()
                if token_url:
                    parsed = urlparse(token_url)
                    params = parse_qs(parsed.query)
                    if 'tokenDesafio' in params:
                        return params['tokenDesafio'][0]
                
                time.sleep(1)
            except Exception as e:
                print(f"Error while waiting for token: {e}")
        
        print("Timeout waiting for token")
        return None

    def make_request_with_headers(self, url):
        """Make request with proper headers"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': BASE_URL,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = self.session.get(url, headers=headers)
            print(f"\nRequest URL: {url}")
            print(f"Response Status: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            print(f"Response Content: {response.text[:500]}")
            return response
        except Exception as e:
            print(f"Error making request: {e}")
            return None

    def start_session(self):
        """Start the browser session and handle token/captcha process"""
        try:
            print("Starting new session...")
            self.setup_browser()
            
            print("Loading page...")
            self.browser.get(BASE_URL)
            time.sleep(5) 
            
            print("\nExtracting cookies...")
            cookies = self.browser.get_cookies()
            for cookie in cookies:
                print(f"Cookie: {cookie['name']} = {cookie['value']}")
                self.session.cookies.set(cookie['name'], cookie['value'])
            
            print("\nWaiting for token to appear...")
            self.challenge_token = self.wait_for_token_in_page()
            if self.challenge_token:
                print(f"\nExtracted token: {self.challenge_token}")
            else:
                print("\nFailed to extract token")
                return

            print("\nPlease enter the captcha solution you see in the browser.")
            print("The format should be like 'k8fe6w' (6 characters)")
            self.captcha_response = input("Enter captcha solution: ").strip()
            
            if self.challenge_token and self.captcha_response:
                final_url = f"{URL_DOCUMENTOS}?tokenDesafio={self.challenge_token}&resposta={self.captcha_response}"
                print(f"\nMaking request with URL: {final_url}")
                response = self.make_request_with_headers(final_url)
                
        except Exception as e:
            print(f"\nError during session: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            input("\nPress Enter to close the browser...")
            if self.browser:
                self.browser.quit()

def main():
    session = JurisprudenciaSession()
    session.start_session()

if __name__ == "__main__":
    main()