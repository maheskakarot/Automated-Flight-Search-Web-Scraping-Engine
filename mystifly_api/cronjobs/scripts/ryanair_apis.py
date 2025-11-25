import json
import pytz
import requests
from datetime import datetime, timedelta
from cronjobs.constants import payload_data
from random import randint

class RyanairExecuter():

    def __init__(self):
        self.token = ''
        self.result_id = ''
        self.currency_code = ''
        self.price = 0
        self.status = {
            'Subscriber API': {'status': 'Not checked','latency':0},
            'Search API': {'status': 'Not checked','latency':0},
            'Revalidation API': {'status': 'Not checked','latency':0},
            'Initiatebooking API': {'status': 'Not checked','latency':0},
            'Seat-selection API': {'status': 'Not checked','latency':0},
            'Baggage-selection API': {'status': 'Not checked','latency':0},
            'Fast-track API': {'status': 'Not checked','latency':0},
            'Login API': {'status': 'Not checked','latency':0}
        }

    def send_request(self, endpoint, payload, headers):

        response = requests.post(url=endpoint,
                                 headers=headers,
                                 data=payload,
                                 )

        return response

    def calculate_dates(self):
        today = datetime.now().date()
        date_10_days = today + timedelta(days=10)
        date_15_days = today + timedelta(days=15)
        return str(date_10_days), str(date_15_days)

    def check_subscriber(self):
        subscriber_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v1/ryanair/account/subscriber'
        payload = payload_data.subscriber_payload % randint(1000000000, 9999999999)
        headers = {
            'Content-Type': 'application/json'
        }
        print('subscriber payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200 or response['status'] == 201:
            subscriber_status['status'] = 'Success'
            self.token = response['data']['token']
        else:
            subscriber_status['status'] = 'Failed'

        subscriber_status['latency'] = latency.seconds

        self.status['Subscriber API'] = subscriber_status

        return response['status']

    def check_search(self):
        search_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v5/ryanair/search/flights'
        departure_date, arrival_date = self.calculate_dates()
        payload = payload_data.search_payload % (departure_date + 'T00:00:00', arrival_date + 'T00:00:00')
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('search payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)

        if response['status'] == 200:
            search_status['status'] = 'Success'
            self.result_id = response['data']['results'][0]['result_id'] + '-VF'
            self.currency_code = response['data']['results'][0]['fare_types'][0]['fare_currency']
            self.price = response['data']['results'][0]['fare_types'][0]['fare_value']
            print(self.result_id)
            print(self.price)
            print(self.currency_code)
        else:
            search_status['status'] = 'Failed'

        search_status['latency'] = latency.seconds

        self.status['Search API'] = search_status

        return response['status']

    def check_revalidation(self):
        revalidation_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v3/ryanair/reprice/validation'

        payload = payload_data.revalidation_payload % (self.result_id, self.currency_code, self.price)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200:
            revalidation_status['status'] = 'Success'
        else:
            revalidation_status['status'] = 'Failed'

        revalidation_status['latency'] = latency.seconds

        self.status['Revalidation API'] = revalidation_status

        return response['status']

    def check_initiatebooking(self):
        initiatebooking_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v2/ryanair/booking/initiate'

        payload = payload_data.initiate_booking_payload % (self.result_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('initiate booking payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200:
            initiatebooking_status['status'] = 'Success'
        else:
            initiatebooking_status['status'] = 'Failed'

        initiatebooking_status['latency'] = latency.seconds

        self.status['Initiatebooking API'] = initiatebooking_status

        return response['status']

    def check_seatselection(self):
        seatselection_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v2/ryanair/booking/seat-selection'

        payload = payload_data.seat_selection_payload % (self.result_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('seatselection payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200:
            seatselection_status['status'] = 'Success'
        else:
            seatselection_status['status'] = 'Failed'

        seatselection_status['latency'] = latency.seconds

        self.status['Seat-selection API'] = seatselection_status

        return response['status']

    def check_baggageselection(self):
        baggageselection_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v2/ryanair/booking/baggages-selection'

        payload = payload_data.baggage_selection_payload % (self.result_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('baggage payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200:
            baggageselection_status['status'] = 'Success'
        else:
            baggageselection_status['status'] = 'Failed'

        baggageselection_status['latency'] = latency.seconds

        self.status['Baggage-selection API'] = baggageselection_status

        return response['status']

    def check_fasttrack(self):
        fasttrack_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v2/ryanair/booking/fast-track/add'

        payload = payload_data.fastrack_payload % (self.result_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('fastrack payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        print(response)
        if response['status'] == 200:
            fasttrack_status['status'] = 'Success'
        else:
            fasttrack_status['status'] = 'Failed'

        fasttrack_status['latency'] = latency.seconds

        self.status['Fast-track API'] = fasttrack_status

        return response['status']

    def check_login(self):
        login_status = {}
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v1/ryanair/login'

        payload = payload_data.login_payload
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('login payload')
        print(payload)
        before_response = datetime.now()
        response = self.send_request(endpoint, payload, headers)
        after_response = datetime.now()
        latency = after_response - before_response
        response = json.loads(response.text)
        # print(response)
        if response['status'] == 200:
            login_status['status'] = 'Success'
        else:
            login_status['status'] = 'Failed'

        login_status['latency'] = latency.seconds

        self.status['Login API'] = login_status

        return response['status']

    def check_payment(self):
        endpoint = 'https://ryanpython.default-626251809c40d7000131dba0.mystifly.facets.cloud/v1/ryanair/payment/initiate'

        payload = payload_data.payment_payload % (self.result_id)
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Token {self.token}'
        }
        print('payment payload')
        print(payload)
        self.send_request(endpoint, payload, headers)

    def get_report(self):

        status = self.check_subscriber()
        if status != 200 and status != 201:
            return self.status

        status = self.check_search()
        if status != 200:
            return self.status

        status = self.check_revalidation()
        if status != 200:
            return self.status

        status = self.check_initiatebooking()
        if status != 200:
            return self.status

        status = self.check_seatselection()
        if status != 200:
            return self.status

        status = self.check_baggageselection()
        if status != 200:
            return self.status

        status = self.check_fasttrack()
        if status != 200:
            return self.status

        self.check_login()

        try:
            self.check_payment()
        except:
            pass

        return self.status

def get_timestamp():
    month_dict = {
        1: 'Jan',
        2: 'Feb',
        3: 'Mar',
        4: 'Apr',
        5: 'May',
        6: 'Jun',
        7: 'Jul',
        8: 'Aug',
        9: 'Sep',
        10: 'Oct',
        11: 'Nov',
        12: 'Dec'
    }

    current_time = datetime.now(pytz.utc)
    indian_timezone = pytz.timezone('Asia/Kolkata')
    now = current_time.astimezone(indian_timezone)
    timestamp = str(now.day) + '-' + month_dict.get(now.month) + '-' + str(now.year) + ' ' + str(now.time()).split('.')[0]
    return timestamp
def generate_html_content(report):

    data = [
        ['Subscriber API', report['Subscriber API']['status'], report['Subscriber API']['latency']],
        ['Search API', report['Search API']['status'], report['Search API']['latency']],
        ['Revalidation API',report['Revalidation API']['status'], report['Revalidation API']['latency']],
        ['Initiatebooking API', report['Initiatebooking API']['status'], report['Initiatebooking API']['latency']],
        ['Seat-selection API', report['Seat-selection API']['status'], report['Seat-selection API']['latency']],
        ['Baggage-selection API', report['Baggage-selection API']['status'], report['Baggage-selection API']['latency']],
        ['Fast-track API', report['Fast-track API']['status'], report['Fast-track API']['latency']],
        ['Login API', report['Login API']['status'], report['Login API']['latency']]
    ]

    html = f"""
    <html>
    <head>
    <style>
    body {{
        width: 100% !important;
        margin: 0;
        padding: 0;
    }}

    table {{
        border-collapse: collapse;
        width: 60%; /* Adjust the table width as needed */
        margin-left: auto;
        margin-right: auto;
    }}

    table, th, td {{
        border: 1px solid black;
        padding: 10px;
        text-align: center;
    }}

    tr.first_row {{
        background-color: lightyellow;
    }}

    tr.success td {{
        background-color: #52D017;
    }}

    tr.failed td {{
        background-color: #DC381F;
    }}

    tr.not_checked td {{
        background-color: #1589FF;
    }}

    tr.empty_row {{
        background-color: white;
    }}

    th:nth-child(3),
    td:nth-child(3) {{
        width: 33%; /* Set the third column width to 33% */
    }}
    </style>
    </head>
    <body>
    <center>
    <h2>The Ryanair APIs verified @ {get_timestamp()}</h2>
    <table align="center">
        <tr class="first_row">
            <th>API</th>
            <th>Status</th>
            <th>Latency in seconds</th>
        </tr>
    """

    # Rest of your code remains unchanged

    for i in range(8):
        if data[i][1] == 'Success':
            html += f'<tr class="success"><td>{data[i][0]}</td><td>{data[i][1]}</td><td>{data[i][2]}</td></tr>'
        elif data[i][1] == 'Failed':
            html += f'<tr class="failed"><td>{data[i][0]}</td><td>{data[i][1]}</td><td>{data[i][2]}</td></tr>'
        elif data[i][1] == 'Not Checked':
            html += f'<tr class="not_checked"><td>{data[i][0]}</td><td>{data[i][1]}</td><td>{data[i][2]}</td></tr>'

    html += """
            <tr class="empty_row"><td></td><td></td><td></td></tr>
            <tr>
                <td colspan="3"><b>Legend:</b></td>
            </tr>
            <tr>
                <td bgcolor="#52D017"></td>
                <td>Success</td>
                <td></td>
            </tr>
            <tr >
                <td bgcolor="#DC381F"></td>
                <td>Failure</td>
                <td></td>
            </tr>
            <tr>
                <td bgcolor="#1589FF"></td>
                <td>Not Checked</td>
                <td></td>
            </tr>
        </table>
        <p>
            For any additional details, please reach out to suim-scraping-team@mystifly.com 
        </p>
        </body>
        </html>
        """

    return html


