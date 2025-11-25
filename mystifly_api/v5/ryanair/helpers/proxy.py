from django.conf import settings

proxyDict = {
    "http": f"http://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}@{settings.PROXY_HOST}:{settings.PROXY_PORT}",
    "https": f"http://{settings.PROXY_USERNAME}:{settings.PROXY_PASSWORD}@{settings.PROXY_HOST}:{settings.PROXY_PORT}",
}

HEADERS = {
    'authority': 'www.ryanair.com',
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
    'cache-control': 'no-cache',
    'cookie': 'fr-visit-id=25cf8c86-cec1-480c-8305-995c9f6a7d19; _ga=GA1.2.148026902.1675340460; STORAGE_PREFERENCES={"STRICTLY_NECESSARY":true,"PERFORMANCE":true,"FUNCTIONAL":true,"TARGETING":true,"SOCIAL_MEDIA":true,"PIXEL":true,"GANALYTICS":true,"__VERSION":2}; RY_COOKIE_CONSENT=true; bid_FRwdAp7a9G2cnLnTsgyBNeduseKcPcRy=658daf5c-797b-44d6-8935-d1c6de0568e8; RYANSESSION=Y9uqvwqhAm0AAFcgRUEAAAA7; _hjSessionUser_135144=eyJpZCI6IjMzMWE0Nzk1LTM5MzgtNWU5Ny1iYzY2LWM5ZGVhMzljN2JiZiIsImNyZWF0ZWQiOjE2NzUzNDA0NjEzMDcsImV4aXN0aW5nIjp0cnVlfQ==; agso=AQGewQwBAO9_ugEYBdtImQVi15IAl2k.; agsd=UaYSR_UKOM1tji40TZjzmKmN3POlgQFhaTSnz78WxEFTTO1u; agsn=h08Cz47eVZiWMjXAL8ctx8xh_RRzcxE1TpPcobm9pOc.; _cc=AYYTDLGQSwQwCkV22mxyzVLJ; fr-correlation-id=e8e522be-137e-48bb-966a-d0b7d1c8bdd4; fr-correlation-id.sig=ZMGcLW4B1zeAZ877ZsZBM0WrX9s; _cid_cc=AYYTDLGQSwQwCkV22mxyzVLJ; _gcl_au=1.1.513928296.1685632940; AMCVS_64456A9C54FA26ED0A4C98A5%40AdobeOrg=1; AMCV_64456A9C54FA26ED0A4C98A5%40AdobeOrg=-715282455%7CMCIDTS%7C19537%7CMCMID%7C27954480282341091821446040980061674464%7CMCAAMLH-1688553912%7C12%7CMCAAMB-1688553912%7CRKhpRz8krg2tLO6pguXWp5olkAcUniQYPHaMWWgdJ3xzPWQmdj0y%7CMCOPTOUT-1687956312s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C4.2.0%7CMCCIDH%7C-265859108; __zlcmid=1Gclw4gz7wwLwlU; mkt=/gb/en/; rid=cf6b44cb-e2cf-49a0-a129-203597860ed6; agssn=AaBwST4BAKgkStKmjdtIf3IzcQ..; ADRUM=s=1690355221420&r=https%3A%2F%2Fcarhire.ryanair.com%2Fin-path%3Fhash%3D-1645570585; aws-waf-token=66c49004-f11d-492a-89cc-47f52c77801d:HgoAlnyECpwEAAAA:QhYyfcZmpf72Fsn1fqnchNKbqJbBt8XyQCuQxkoO7JZUFhtOXT0PcLSTrN1/xgrJK6547GCdYmQvFrx5YFwToB89aIyirj4MDIQs/alVsBe1Ru6WP+YqsFNaRhf2RkyH22JDjhrTu7IHZXd1Mr//q4cGQREJ6KkUxuL1GW+VenYMwmj5Z4c2jZibRFkJ7fMv; _gid=GA1.2.1537530176.1690540022; myRyanairID=; .AspNetCore.Session=CfDJ8Bbvw3LfWchDv%2FP1nMsZXlkTIfl0oK9K5UZ5Gv50HdG2q7T%2FL%2BnxT8rsTZBs8ZX4ghOAUMOUEv1FhSdMhgn2TEtDWyfkqKjHSvK294qec3qAYLaA%2FUv%2Fy1hCdq2l0jcLs%2BGKmkIeIwT9EQk5ANVOoLQGRliE5I0HG%2BmbkL45W4hS; _gat_gtag_UA_153938230_2=1; rid.sig=jyna6R42wntYgoTpqvxHMK7H+KyM6xLed+9I3KsvYZaVt7P36AL6zp9dGFPu5uVxaIiFpNXrszr+LfNCdY3IT3oCSYLeNv/ujtjsDqOzkY5JmUFsCdAEz3kpPbhCUwiArp5oaa75tpJtO3kFwYQ8l0DbH67AtcN/PMbniLsiM5qn+2AjrrtoNJicE3ZQwFHVipe4lWPSRfq2OIyUrlFhwEDt20+wCX7l1mCubNXtG6ly1DzBqZYVDrO1g5GvXPZOA42fzbLan/n0LVhBklBpY9ThSINkxfhx06aFLl2Az71NT8nkb3crWpc4H+ouJqTRw7i/EJq20+9QJYWtNXEKQWd2AMGjcxk2m5LMmELWK4D3vK+/oR6+AfgkuE0lfjO6fvyLLub/yFRBmUyb+KSBtyaoQc3oaKqM4+uuUpacvQ4AoTf+JvO6py+xx7g67UmpWBXQ3nKTzfxOXwPqPhIApmW4QLXfxZPYpjubrBFkpDxA2kuCeE4EH7QoVRetv6ugXh5oPQ0L86rmRJVRqA3VnuyzAxgZGysOM5TDwBKts30JOC46pkg6hy7OL6ZRbFQ/SdYmFKLl4kPGoqX/2o66FNRua47tlcXISHqOyDIipASi/4kZ6uIXZnJI38zN2q7LjKLIiWQOCv8rOD/v/KfLt8xiAkwE8nYbuemJANcXqkHbXcyRbEhd9GhbcWlpsRiH3qRefilziBGvfg7CFVKj/scsHsyTgys0FpJ95IwVDlVEmWzXsvE8ffJ3M6K7uW3hSmueSh10ao8V8n7blNgUyQ==' ,
    'pragma': 'no-cache',
    # 'referer': 'https://www.ryanair.com/gb/en/trip/flights/select?adults=1&teens=0&children=0&infants=0&dateOut=2023-05-27&dateIn=2023-05-29&isConnectedFlight=false&isReturn=true&discount=0&promoCode=&originIata=STN&destinationIata=DUB&tpAdults=1&tpTeens=0&tpChildren=0&tpInfants=0&tpStartDate=2023-05-27&tpEndDate=2023-05-29&tpDiscount=0&tpPromoCode=&tpOriginIata=STN&tpDestinationIata=DUB',
    'sec-ch-ua': '"Not:A-Brand";v="99", "Chromium";v="112"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
}

MAX_TRY = 5
