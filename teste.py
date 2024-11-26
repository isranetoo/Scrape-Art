from pathlib import Path
from requests.utils import dict_from_cookiejar
import json
import requests

# create a session to presists cookies
session = requests.session()

# send cookies through a response object
session.get("https://pje.trt2.jus.br/jurisprudencia/")

# turn cookiejar into dict
cookies = dict_from_cookiejar(session.cookies)  

# save them to file as JSON
Path("cookies.json").write_text(json.dumps(cookies))