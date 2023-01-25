import pathlib
import json
import copy

import requests
import urllib


class LandaxAuthException(Exception):
    pass


class Client:
    def __init__(self, url: str, credentials: dict):
        self.required_credentials = [
            'username', 'password',
            'client_id', 'client_secret'
        ]

        for key, value in credentials.items():
            setattr(self, key, value)

        for attr in self.required_credentials:
            if not hasattr(self, attr):
                print(f'Error: credential field is required: {attr}')
                return

        self.base_url = f'https://{url}/'
        self.api_url = self.base_url + 'api/v20/'
        self.headers = {}

        self.oauth_token = self.get_oauth_token()

        self.headers['Authorization'] = 'Bearer ' + self.oauth_token

    # Returns a record with the given data_id (Id in in landax)
    def get_single_data(self, data_model: str, data_id: int, params: {} = None):
        if params is None:
            params = {}

        base_url = f'{self.api_url}{data_model}({str(data_id)})'
        url = self.generate_url(base_url, params)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            return None

        data = response.json()
        return data

    # Returns all records of the given data model
    def get_all_data(self, data_model: str, params: {} = None) -> [{}]:
        if params is None:
            params = {}

        if '$top' in params:
            print('Warning: pylandax.get_all_data does not support $top parameter. It will be ignored.')

        if '$skip' in params:
            print('Warning: pylandax.get_all_data does not support $skip parameter. It will be ignored.')

        params['$top'] = 1000
        base_url = f'{self.api_url}{data_model}'
        initial_url = self.generate_url(base_url, params)

        data = self.request_data(initial_url)
        count = len(data)
        if count != 1000:
            return data

        # If count is 1000, there is a chance that there are more than 1000 records
        # since Landax only returns 1000 records max at a time
        # so we need to make additional requests until we get less than 1000
        thousands = 0
        while count == 1000:
            thousands = thousands + 1
            # This is okay because we know that $top is always included
            new_url = initial_url + '&$skip=' + str(thousands * 1000)
            new_data = self.request_data(new_url)
            # + in this context is list concatenation
            data = data + new_data
            count = len(new_data)

        return data

    def post_data(self, data_model: str, data: dict):
        url = self.api_url + data_model
        headers = copy.deepcopy(self.headers)
        headers['Content-Type'] = 'application/json'

        response = requests.post(url, json=data, headers=headers)
        return response

    # Patches the given data model with the given id with data
    def patch_data(self, data_model: str, key: int, data: dict):
        url = f'{self.api_url}{data_model}({str(key)})'
        headers = copy.deepcopy(self.headers)
        headers['Content-Type'] = 'application/json'

        response = requests.patch(url, json=data, headers=headers)
        return response

    # Deletes data with the given key
    def delete_data(self, data_model: str, key: str):
        url = f'{self.api_url}{data_model}({key})?$format=json'
        response = requests.delete(url, headers=self.headers)
        if response.status_code == 404:
            return None
        return response

    # Helper function for get_data
    def request_data(self, url: str) -> []:
        response = requests.get(url, headers=self.headers)
        results = response.json()['value']
        return results

    def upload_document(self, file: pathlib.Path, folder_id: int):
        url = self.api_url + 'Documents/CreateDocument'
        document = json.dumps({'FolderId': folder_id})

        files = {
            'document': (None, document),
            'fileData': (str(file.name), open(file, 'rb'))
        }

        response = requests.post(url, files=files, headers=self.headers)

        return response

    # Creates a dict given the list of dicts list_in using the metakey
    @staticmethod
    def list_to_dict(list_in: [{}], metakey: str):
        return_dict = {}

        for record in list_in:
            key = record[metakey]
            if key in return_dict:
                print(f'Warning: {key} already present, overwriting')
            return_dict[key] = record

        return return_dict

    def get_oauth_token(self):
        url = self.base_url + 'authenticate/token?grant_type=password'

        post_body = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'username': self.username,
            'password': self.password
        }

        result = requests.post(url, json=post_body)
        if result.status_code != 200:
            raise LandaxAuthException(
                'Landax returned non-200 response when getting OAuth token. Body: ' + str(result.content))

        response_data = result.json()

        if 'access_token' not in response_data:
            raise LandaxAuthException('Landax response was non-json. Body: ' + str(result.content))

        return response_data['access_token']

    @staticmethod
    def generate_url(base_url: str, html_params: dict):
        if len(html_params) == 0:
            return base_url
        result = base_url + '?' + urllib.parse.urlencode(html_params)
        return result
