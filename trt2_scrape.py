import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# URLs
BASE_URL = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_BUSCA_JURISPRUDENCIA = 'https://pje.trt2.jus.br/juris-backend/api/jurisprudencia'

def setup_browser():
    """Setup and return browser instance"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    return webdriver.Chrome(options=options)

def get_session_info():
    """Open browser and get session information"""
    browser = setup_browser()
    try:
        # Open the webpage
        print("Opening webpage...")
        browser.get(BASE_URL)
        
        # Wait for page to load
        time.sleep(5)
        
        # Get cookies from browser
        print("\nCollecting cookies...")
        cookies = browser.get_cookies()
        for cookie in cookies:
            print(f"Cookie found: {cookie['name']}")
        
        # Create requests session and add cookies
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Get initial token with error handling
        print("\nRequesting initial token...")
        try:
            token_response = session.get(URL_TOKEN)
            print(f"Token response status: {token_response.status_code}")
            print(f"Token response content: {token_response.text}")
            initial_token = token_response.json().get('token') if token_response.ok else None
        except json.JSONDecodeError as e:
            print(f"Error parsing token response: {e}")
            print(f"Raw response: {token_response.text}")
            initial_token = None
        except requests.exceptions.RequestException as e:
            print(f"Request error for token: {e}")
            initial_token = None
        
        # Get captcha token with error handling
        print("\nRequesting captcha token...")
        try:
            captcha_response = session.get(URL_CAPTCHA)
            print(f"Captcha response status: {captcha_response.status_code}")
            print(f"Captcha response content: {captcha_response.text}")
            captcha_token = captcha_response.json().get('tokenCaptcha') if captcha_response.ok else None
        except json.JSONDecodeError as e:
            print(f"Error parsing captcha response: {e}")
            print(f"Raw response: {captcha_response.text}")
            captcha_token = None
        except requests.exceptions.RequestException as e:
            print(f"Request error for captcha: {e}")
            captcha_token = None
        
        print("\nInitial Token:", initial_token)
        print("Captcha Token:", captcha_token)
        
        # Wait for manual captcha input
        captcha_input = input("\nPlease solve the captcha in the browser and enter the response here: ")
        
        return {
            'session': session,
            'initial_token': initial_token,
            'captcha_token': captcha_token,
            'captcha_response': captcha_input
        }
        
    except Exception as e:
        print(f"Error during browser automation: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        input("Press Enter to close the browser...")
        browser.quit()

def buscar_documentos(session_info, pagina=0, tamanho=10):
    """Search for documents using the session information"""
    if not session_info:
        print("No session information available")
        return
    
    params = {
        "tokenDesafio": session_info['initial_token'],
        "tokenCaptcha": session_info['captcha_response'],
        "pagina": pagina,
        "tamanho": tamanho
    }
    
    print("\nMaking search request with params:", params)
    
    try:
        response = session_info['session'].get(URL_BUSCA_JURISPRUDENCIA, params=params, timeout=10)
        print(f"Search response status: {response.status_code}")
        print(f"Search response content: {response.text}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching documents: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing search response: {e}")
        print(f"Raw response: {response.text}")
        return None

def main():
    print("Starting jurisprudence search process...")
    
    session_info = get_session_info()
    
    if session_info:
        results = buscar_documentos(session_info)
        if results:
            print("\nSearch Results:", results)
        else:
            print("\nNo results found or error occurred during search")

if __name__ == "__main__":
    main()