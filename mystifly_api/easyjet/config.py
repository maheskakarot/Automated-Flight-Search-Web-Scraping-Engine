import random
# Email and Password
EMAIL = 'surya.r@mystifly.com'
PASSWORD = 'Mystifly@123'

# User Agents
user_agents= ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36x-b2b-misc',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24',
                    'Chrome (AppleWebKit/537.1; Chrome50.0; Windows NT 6.3) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14393',
                    'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.24 Safari/532.0',
                    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.9200',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
                    'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_8; en-US) AppleWebKit/533.4 (KHTML, like Gecko) Chrome/5.0.375.125 Safari/533.4',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19582',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/51.0.2704.79 Safari/537.36 Edge/14.14931',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.8810.3391 Safari/537.36 Edge/18.14383',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36 Edge/18.19577',
                    'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/532.0 (KHTML, like Gecko) Chrome/3.0.195.24 Safari/532.0',
                    'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/10.0.649.0 Safari/534.17',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36 Edge/12.246',
                    'Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.36 (KHTML like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.9200',
                    'Mozilla/5.0 (Windows; U; Windows NT 6.1) AppleWebKit/526.3 (KHTML, like Gecko) Chrome/14.0.564.21 Safari/526.3',
                    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/29.0.1547.62 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.8810.3391 Safari/537.36 Edge/18.14383'
	]
user_agent = random.choice(user_agents)
headers ={
                "Accept": 'application/json, text/plain, */*',
                "Accept-Encoding": 'gzip, deflate, br',
                "Accept-Language": 'en-US,en;q=0.9,hi;q=0.8',
                "ADRUM": 'isAjax:true',
                "Connection": 'keep-alive',
                "Host": 'www.easyjet.com',
                "Referer": 'https://www.easyjet.com/en/buy/flights?isOneWay=off&pid=www.easyjet.com',
                "sec-ch-ua": '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
                "sec-ch-ua-mobile": '?0',
                "sec-ch-ua-platform": "Windows",
                "Sec-Fetch-Dest": 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': user_agent,
                'X-Requested-With': 'XMLHttpRequest'
    }


XPATH = {
    "accept_cookies": '/html/body/section[2]/div/div/div[2]/button[2]',
    'one_way_button': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[1]/div[1]/label/span[1]',
    'origin': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[2]/div/div[2]/div[1]/input',
    'destination': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[2]/div/div[4]/div/input',
    'depature_date': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[3]/div/div[1]/div/button',
    'return_date': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[3]/div/div[3]/div/button',
    'add_adult': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[4]/div[1]/div/div/button[2]',
    'add_child': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[4]/div[2]/div/div/button[2]',
    'add_infant': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[4]/div[3]/div/div/button[2]',
    'remove_adult': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[4]/div[1]/div/div/button[1]',
    'departure_date': '/html/body/div[3]/div[1]/main/div/div[1]/section/div[1]/div/div/ul/li[1]/div/div/form/div[3]/div/div[1]/div/button',
    'same_day_travel': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[3]',
    'travelling_with_infants': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[3]',
    'search_button': '//*[@ej-click-event="SubmitFlightSearch()"]',
    'list_of_flights': '/html/body/div[3]/div[1]/main/div[1]/div[2]/div[5]/div[2]/div/div/div/div/div[1]/div/div/div[3]/div/div/div[2]/div/div[2]/div[2]/div/ul',
    'continue_with_flight': '/html/body/div[3]/div[1]/header/div[3]/div/div/div/div[2]/button',
    'flying_with_infants': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[3]/button',
    'skip_seat_selection': '/html/body/div[3]/div[1]/header/div[3]/div/div/div/div[2]/button',
    'skip_seat_popup': '/html/body/div[3]/div[1]/main/div/div[2]/div[4]/div/div/div[2]/div/div[2]/button[2]',
    'continue_with_standerd': '/html/body/div[5]/div/div[2]/div[2]/div[1]/div/div/div[2]/div/button',
    'skip_bags': '/html/body/div[3]/div[1]/header/div[3]/div/div/div/div[2]/button',
    'skip_bags_popup': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[3]/button',
    'Email_Id': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[1]/div[4]/div/div[1]/form/div[1]/input',
    'Password': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[1]/div[4]/div/div[1]/form/div[3]/input',
    'Sign_in': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[1]/div[4]/div/div[1]/form/div[5]/input',
    'Keep_signedin': '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/div[1]/div[4]/div/div[1]/form/div[6]/label/span[1]/span',
    'Liesure': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[1]/form/div[2]/div/input',
    'Title': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/form/div[1]/div/div[3]/div[1]/div/select',
    'FirstName': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/form/div[1]/div/div[3]/div[2]/div/input',
    'Last_Name': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/form/div[1]/div[1]/div[3]/div[3]/div/input',
    'Age': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[2]/div/form/div[1]/div/div[3]/div[4]/div/select',
    'Insurance_Cover': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[3]/form/div[1]/input',
    'Continue': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[2]/div[1]/div[4]/button',
    'Basket_Amount': '/html/body/div[3]/div[2]/a/div[1]/h3',
    'Card_Number': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[2]/div/form/div[1]/div/input',
    'Card_Holder_Name': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[2]/div/form/div[2]/div/input',
    'Expiry_Month': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[2]/div/form/fieldset/div[1]/select[1]',
    'Expiry_Year': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[2]/div/form/fieldset/div[1]/select[2]',
    'CVV': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[2]/div/form/div[3]/div[2]/input[1]',
    'Pay_Now': '/html/body/div[3]/div[1]/main/div/div[2]/div[2]/div[2]/div[1]/div[3]/div[1]/div[4]/button',
    "session_expiry": '/html/body/div[4]/div[1]/div/div[2]/div/div/div[2]/div/div/div[1]/div/button',
}

    
    
  
  

CSS_SELECTORS = {

}

WEBSITE={
    'easyjet':'https://www.easyjet.com/en',
    'bags':"https://www.easyjet.com/en/buy/bags"

}