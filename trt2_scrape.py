import requests
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

BASE_URL = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_BUSCA_JURISPRUDENCIA = 'https://pje.trt2.jus.br/juris-backend/api/jurisprudencia'

def setup_browser():
    """Setup and return browser instance"""
    options = webdriver.ChromeOptions()
    options.add_argument('--start-maximized')
    return webdriver.Chrome(options=options)

def get_session_info():
    """Open browser and get session information"""
    browser = setup_browser()
    try:
        # Open the webpage
        browser.get(BASE_URL)
        
        # Wait for page to load
        time.sleep(2)
        
        # Get cookies from browser
        cookies = browser.get_cookies()
        
        # Create requests session and add cookies
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        
        # Get initial token
        token_response = session.get(URL_TOKEN)
        initial_token = token_response.json().get('token') if token_response.ok else None
        
        # Get captcha token
        captcha_response = session.get(URL_CAPTCHA)
        captcha_token = captcha_response.json().get('tokenCaptcha') if captcha_response.ok else None
        
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
        return None
    finally:
        # Keep browser open for manual inspection
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
    
    try:
        response = session_info['session'].get(URL_BUSCA_JURISPRUDENCIA, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error searching documents: {e}")
        return None

def main():
    print("Starting jurisprudence search process...")
    
    # Get session information through browser
    session_info = get_session_info()
    
    if session_info:
        # Search documents
        results = buscar_documentos(session_info)
        if results:
            print("\nSearch Results:", results)
        else:
            print("\nNo results found or error occurred during search")

if __name__ == "__main__":
    main()