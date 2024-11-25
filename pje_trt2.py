import base64
import os
import csv
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from PIL import Image
from captcha_local_solver import solve_captcha_local

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'