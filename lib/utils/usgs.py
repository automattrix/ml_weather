import json
import requests
import datetime
import time
import yaml
import os
from urllib.request import urlopen, urlretrieve
import sys
import cgi


def post_request(data, url, api_key=None):
    json_data = json.dumps(data)

    if api_key is None:
        r = requests.post(url=url, data=json_data)

    else:
        headers = {'X-Auth-Token': api_key}
        r = requests.post(url=url, data=json_data, headers=headers)

    if r.status_code == 200:
        return r
    else:
        return None


def download_from_url(downloads):
    downloads_failed = []

    for download in downloads:

        download_url = download['url']
        print("DOWNLOAD: " + download_url)

        remotefile = urlopen(download_url)
        remotefile_info = remotefile.info()['Content-Disposition']
        value, params = cgi.parse_header(remotefile_info)
        file_name = params["filename"]

        print(f"Filename: {file_name}")

        download_path = f'./data/01_raw/{file_name}'
        print(download_path)

        if not os.path.exists(download_path):
            try:
                urlretrieve(download_url, download_path)

            except Exception as e:
                print(e)
                downloads_failed.append(download)
        else:
            print("Already downloaded")
    if downloads_failed:
        print(downloads_failed)


class UsgsRequest:
    def __init__(self, params):
        self.params = params
        self.api_key = None
        self.session_id = None
        self.last_login_time = None
        self.dataset_alias = None

        self.scenes_id_list = None
        self.image_download_list = []

    def build_enpoint_url(self, endpoint):
        base_url = self.params['API_URL']
        endpoint_url = base_url + endpoint
        return endpoint_url

    def check_previous_login(self):
        login_check = False
        login_session_path = './conf/local/login.yaml'

        if os.path.exists(login_session_path):
            with open(login_session_path, 'r') as login_yaml:
                previous_session = yaml.load(login_yaml, Loader=yaml.FullLoader)

                self.last_login_time = previous_session['last_login_time']

                # API key from login valid for 2 hours
                # Check if last login still valid
                LOGIN_TIMEOUT = 7200
                current_time = datetime.datetime.now()
                time_elapsed = current_time - self.last_login_time
                time_elapsed = time_elapsed.seconds
                print(f"Time since last login: {round(time_elapsed / 60, 2)} min")

                if time_elapsed < LOGIN_TIMEOUT:
                    print("Valid session, continuing...")
                    self.api_key = previous_session['api_key']
                    login_check = True
                else:
                    print("No previous valid session. Logging in again...")

        return login_check

    def login(self):
        # Check for previous login
        if not self.check_previous_login():
            username = self.params['USERNAME']
            password = self.params['PASSWORD']
            data = {"username": username, "password": password}
            url = self.build_enpoint_url(endpoint='login')

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
                self.last_login_time = datetime.datetime.now()

                with open('./conf/local/login.yaml', 'w') as f:
                    data = {
                        'last_login_time': self.last_login_time,
                        'api_key': self.api_key
                    }
                    yaml.dump(data, f)

            else:
                print("Login Unsuccessful")
                print(error_message)

    def search_dataset(self):
        dataset_search_params = {'datasetName': self.params['DATASET']}
        print("Searching datasets...\n")
        url = self.build_enpoint_url(endpoint='dataset-search')

        datasets = post_request(url=url, data=dataset_search_params, api_key=self.api_key)
        datasets = json.loads(datasets.text)
        print(f"Found: {datasets['data'][0]['datasetAlias']}")

        self.dataset_alias = datasets['data'][0]['datasetAlias']

    def scene_search(self):
        dataset = self.dataset_alias
        acquisitionFilter = {"end": "2020-07-15",
                             "start": "2020-06-01"}

        # Path: 047
        # Row: 026
        spatialFilter = {'filterType': "mbr",
                         'lowerLeft': {'latitude': 48.4824, 'longitude': -124.0711},
                         'upperRight': {'latitude': 49.1526, 'longitude': -122.9024}
                         }

        scene_search_parameters = {
            'datasetName': dataset,
            'maxResults': 5,
            'startingNumber': 1,
            'sceneFilter': {
                'acquisitionFilter': acquisitionFilter,
                'spatialFilter': spatialFilter
            }
        }

        url = self.build_enpoint_url(endpoint='scene-search')
        scenes = post_request(data=scene_search_parameters, url=url, api_key=self.api_key)
        scenes = json.loads(scenes.text)
        records_returned = scenes['data']['recordsReturned']
        scenes_list = []
        if records_returned > 0:
            scene_results = scenes['data']['results']

            for result in scene_results:
                scenes_list.append(result['entityId'])
            self.scenes_id_list = scenes_list

        else:
            print("Search found no results.\n")
            sys.exit()

    def retrieve_scenes_downloads(self):
        # https://m2m.cr.usgs.gov/api/docs/example/download_data-py
        scene_id_list = self.scenes_id_list
        dataset = self.dataset_alias
        url = self.build_enpoint_url(endpoint='download-options')

        download_options_parameters = {
            'datasetName': dataset,
            'entityIds': scene_id_list
        }

        download_options = post_request(
            data=download_options_parameters,
            url=url,
            api_key=self.api_key
        )
        download_options = json.loads(download_options.text)
        download_options_results = download_options['data']

        downloads_list = []

        for option in download_options_results:

            if option['available']:
                product_name = option['productName']

                if product_name == 'LandsatLook Natural Color Image':  # TODO make parameter
                    downloads_list.append(
                        {'entityId': option['entityId'],
                         'productId': option['id'],
                         'displayId': option['displayId']
                         }
                    )
        if downloads_list:

            requested_download_count = len(downloads_list)
            # set a label for the download request
            label = "download-sample"
            download_request_parameters = {
                'downloads': downloads_list,
                'label': label
            }
            # Call the download to get the direct download urls
            download_url = self.build_enpoint_url(endpoint='download-request')
            download_requests = post_request(data=download_request_parameters, url=download_url, api_key=self.api_key)
            download_requests = json.loads(download_requests.text)
            download_requests_results = download_requests['data']

            master_image_downloads = []
            if download_requests_results['preparingDownloads'] is not None \
                    and len(download_requests_results['preparingDownloads']) > 0:

                download_retrieve_parameters = {'label': label}
                more_download_url = self.build_enpoint_url(endpoint='download-retrieve')
                more_download_urls = post_request(
                    data=download_retrieve_parameters,
                    url=more_download_url,
                    api_key=self.api_key)

                more_download_urls = json.loads(more_download_urls.text)
                more_download_urls_results = more_download_urls['data']

                download_ids = []

                for download in more_download_urls_results['available']:
                    download_ids.append(download['downloadId'])
                    self.image_download_list.append(download)

                for download in more_download_urls_results['requested']:
                    download_ids.append(download['downloadId'])
                    self.image_download_list.append(download)

                # Didn't get all of the reuested downloads, call the download-retrieve method again after 30 seconds
                while len(download_ids) < requested_download_count:
                    preparing_downloads = requested_download_count - len(download_ids)
                    print("\n", preparing_downloads, "downloads are not available. Waiting for 30 seconds.\n")
                    time.sleep(30)
                    print("Trying to retrieve data\n")

                    more_download_urls = post_request(
                        data=download_retrieve_parameters,
                        url=download_url,
                        api_key=self.api_key
                    )

                    more_download_urls = json.loads(more_download_urls.text)
                    more_download_urls_results = more_download_urls['data']
                    for download in more_download_urls_results['available']:
                        if download['downloadId'] not in download_ids:
                            download_ids.append(download['downloadId'])
                            self.image_download_list.append(download)

            else:
                # Get all available downloads
                for download in download_requests_results['availableDownloads']:
                    self.image_download_list.append(download)
            print("\nAll downloads are available to download.\n")

    def download_images(self):
        download_from_url(downloads=self.image_download_list)

