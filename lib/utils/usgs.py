import json
import requests
import datetime


def post_request(data, url, api_key=None):
    json_data = json.dumps(data)

    if api_key == None:
        r = requests.post(url=url, data=json_data)

    else:
        headers = {'X-Auth-Token': api_key}
        r = requests.post(url=url, data=json_data, headers=headers)

    if r.status_code == 200:
        return r
    else:
        return None


class UsgsRequest:
    def __init__(self, params):
        self.params = params
        self.api_key = None
        self.session_id = None
        self.login_time = None

    def build_enpoint_url(self, endpoint):
        base_url = self.params['API_URL']
        endpoint_url = base_url + endpoint
        return endpoint_url

    def login(self):
        username = self.params['USERNAME']
        password = self.params['PASSWORD']
        data = {"username": username, "password": password}
        url = self.build_enpoint_url(endpoint='login')

        # API key from login valid for 2 hours
        # Check if login
        # current_time = datetime.datetime.now()

        # if self.login_time is not None:
        #     time_elapsed = current_time - self.login_time

        r = post_request(data=data, url=url)
        r = json.loads(r.text)
        api_key = r['data']
        session_id = r['sessionId']
        error_code = r['errorCode']
        error_message = r['errorMessage']

        if not error_code:
            print("Login successful")
            self.api_key = api_key
            self.session_id = session_id
            self.login_time = datetime.datetime.now()
        else:
            print("Login Unsuccessful")
            print(error_message)

    def search_dataset(self):
        dataset_search_params = {'datasetName': self.params['DATASET']}
        print("Searching datasets...\n")
        url = self.build_enpoint_url(endpoint='dataset-search')

        datasets = post_request(url=url, data=dataset_search_params, api_key=self.api_key)
        datasets = json.loads(datasets.text)
        print("Found ", len(datasets), " datasets\n")
        print(datasets)

    def download_data(self):
        test = ''