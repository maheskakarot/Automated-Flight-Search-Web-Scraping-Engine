from django.conf import settings

proxyDict = {
    "http": f"http://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}@{settings.PROXY_HOST}:{settings.PROXY_PORT}",
    "https": f"http://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}@{settings.PROXY_HOST}:{settings.PROXY_PORT}",
}


USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"

HEADERS = {
    'user-agent': USER_AGENT
}

MAX_TRY = 5
