import requests

url = 'https://ipinfo.io'
username = 'sahil1021'
password = 'Sahil1234'

proxy = f'http://{username}:{password}@gate.smartproxy.com:7000'

response = requests.get(url, proxies={'http': proxy, 'https': proxy})

print(response.text)


"""
from utils.test import *
"""