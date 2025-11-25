from easyjet.models import ProxySelection
import time
from django.utils import timezone


def get_proxy_automation():

    proxy_obj = ProxySelection.objects.first()
    try:
        proxy = proxy_obj.proxy
    except:
        proxy = "PS"
        db=ProxySelection.objects.create(id=1,proxy="PS")
        db.save()
        
    
    return proxy
    