import requests
import json


def get_proxy():   
    response = requests.get(
        url="https://api.ttproxy.com/v1/obtain?sign=405f7991ad780aebc8106a7c89fa6742&license=PA75CB9293D88EED7&format=text&cnt=150",
        headers={
            "Content-Type": "text/plain; charset=utf-8",
        },
        data="1"
    )
    # Step 2 : Use proxy IP   
    res = response.text
    proxy = res.splitlines()

    return proxy