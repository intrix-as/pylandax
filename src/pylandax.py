import pathlib
import json
import copy
import io
import logging

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

    def get_single_data(self, data_model: str, data_id: int, params: {} = None) -> {}:
        """
        Returns a single record of the given data model
        :param data_model: The data model to fetch in Landax, eg. Contacts, Projects, etc.
        :param data_id: The id of the record to fetch
        :param params: A dictionary of parameters passed as html query string parameters, eg. $filter, $expand
        :return: A dictionary representing a record
        """
        if params is None:
            params = {}

        base_url = f'{self.api_url}{data_model}({str(data_id)})'
        url = self.generate_url(base_url, params)
        response = requests.get(url, headers=self.headers)
        if response.status_code == 404:
            return None

        data = response.json()
        return data

    def get_all_data(self, data_model: str, params: {} = None) -> [{}]:
        """
        Returns all records of the given data model
        :param data_model: The data model to fetch in Landax, eg. Contacts, Projects, etc.
        :param params: A dictionary of parameters passed as html query string parameters, eg. $filter, $expand
        :return: A list of dictionaries, each dictionary representing a record
        """
        if params is None:
            params = {}

        if '$top' in params:
            print('Warning: pylandax.get_all_data does not support $top parameter. It will be ignored.')
            del params['$top']

        if '$skip' in params:
            print('Warning: pylandax.get_all_data does not support $skip parameter. It will be ignored.')
            del params['$skip']

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

    def post_data(self, data_model: str, data: {}) -> requests.Response:
        """
        Posts data to the given data model in Landax
        :param data_model: The data model in Landax, eg. Contacts, Projects, etc.
        :param data: the data to post, as a dictionary
        :return: the requests.Response object returned from the post request
        """
        url = self.api_url + data_model
        headers = copy.deepcopy(self.headers)
        headers['Content-Type'] = 'application/json'

        response = requests.post(url, json=data, headers=headers)
        return response

    def patch_data(self, data_model: str, key: int, data: dict) -> requests.Response:
        """
        Patches the record with the given key and data
        :param data_model: The data model in Landax, eg. Contacts, Projects, etc.
        :param key: The key of the record to patch
        :param data: The data to patch, as a dictionary
        :return: the requests.Response object returned from the patch request
        """
        url = f'{self.api_url}{data_model}({str(key)})'
        headers = copy.deepcopy(self.headers)
        headers['Content-Type'] = 'application/json'

        response = requests.patch(url, json=data, headers=headers)
        return response

    # Deletes data with the given key
    def delete_data(self, data_model: str, key: str) -> requests.Response:
        """
        Deletes the record with the given key
        :param data_model: The data model in Landax, eg. Contacts, Projects, etc.
        :param key: The key of the record to delete
        :return: the requests.Response object returned from the delete request
        """
        url = f'{self.api_url}{data_model}({key})?$format=json'
        response = requests.delete(url, headers=self.headers)
        return response

    # Helper for the public functions
    def request_data(self, url: str) -> []:
        response = requests.get(url, headers=self.headers)
        results = response.json()['value']
        return results

    def upload_document_from_file(self, file: pathlib.Path, document_object: {} = None):
        """
        Helper function to upload a file to Landax by using a pathlib.Path object.
        :param file: The file to upload
        :param document_object: The associated document object, per the Landax API
        :return: requests.Response object, containing the response from Landax
        """
        if document_object is None:
            document_object = {}

        if not isinstance(file, pathlib.Path):
            raise TypeError('file must be a pathlib.Path')

        if not file.exists():
            raise FileNotFoundError('file does not exist: ' + str(file))

        document_bytes = io.BytesIO(file.read_bytes())

        return self.upload_document(document_bytes, file.name, document_object)

    def upload_document(self, document_data: io.BytesIO, filename: str, folder_id: int, document_options: dict = None):
        """
        Upload a file to Landax by using an io.BytesIO object directly from memory.
        :param document_data: io.BytesIO object to upload of the document
        :param filename: name of the file
        :param folder_id: The folder ID to upload the document to
        :param document_options: The document options as a dictionary, per the Landax API. Eg. IsTemplate, Number
        :return requests.Response object, containing the response from Landax
        """
        if document_options is None:
            document_options = {}

        if 'FolderId' in document_options:
            logging.warning('\
Warning: pylandax.upload_document does not support FolderId parameter in document_options. It will be ignored.')

        document_options['FolderId'] = folder_id

        url = self.api_url + 'Documents/CreateDocument'
        document_object_str = json.dumps(document_options)

        files = {
            'document': (None, document_object_str),
            'fileData': (filename, document_data)
        }

        response = requests.post(url, files=files, headers=self.headers)

        return response

    def document_pushcontent(self, document_data: io.BytesIO, document_id: int):
        doc_id = str(document_id)
        url = self.api_url + f'Documents/PushContent?documentid={doc_id}'

        data = document_data.read()

        response = requests.post(url, data=data, headers=self.headers)
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
