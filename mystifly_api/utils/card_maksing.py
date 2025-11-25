
def cardmapping(card,cvv,ExpiryDate):
    x = 0
    card_num =""
    cvv_num =""
    expiry = ""
    for i in card:
        if x >3 and x<12:
            card_num += "*"
        else:
            card_num+=i
        x+=1

    for i in cvv:
        cvv_num += "*"

    for i in ExpiryDate:
        expiry += "*"

    response = {
        "card":card_num,
        "cvv":cvv_num,
        "expiry":expiry
    }
        
    return response