from pathlib import Path
import json
import copy
import io
import logging

import requests
import urllib


class LandaxAuthException(Exception):
    pass


class Client:
    def __init__(self, url: str, credentials: dict, version='v20'):
        """
        Constructs a new pylandax client
        :param url: The url of the Landax instance, eg. intrixtest.landax.no
        :param credentials: A dictionary containing the credentials to use
        :param version: The version of the API to use, defaults to v20
        :return: A new pylandax client
        """
        self.required_credentials = [
            'username', 'password',
            'client_id', 'client_secret'
        ]

        self.script_dir = Path(__file__).parent.absolute()

        for key, value in credentials.items():
            setattr(self, key, value)

        for attr in self.required_credentials:
            if not hasattr(self, attr):
                print(f'Error: credential field is required: {attr}')
                return

        self.base_url = f'https://{url}/'
        self.api_url = f'{self.base_url}api/{version}/'
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

    def get_all_data(self, data_model: str, params: {} = None, select: [] = None) -> [{}]:
        """
        Returns all records of the given data model
        :param data_model: The data model to fetch in Landax, eg. Contacts, Projects, etc.
        :param params: A dictionary of parameters passed as html query string parameters, eg. $filter, $expand
        :param select: A list of fields to select, eg. ['Id', 'Name']
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

        if select is not None:
            params['$select'] = ','.join(select)

        base_url = f'{self.api_url}{data_model}'
        initial_url = self.generate_url(base_url, params)
        response = self.request_raw(initial_url)
        data = response.json()['value']
        while '@odata.nextLink' in response.json():
            new_url = response.json()['@odata.nextLink']
            response = self.request_raw(new_url)
            data = data + response.json()['value']

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

    def request_raw(self, url: str) -> requests.Response:
        response = requests.get(url, headers=self.headers)
        return response

    def get_documents(self, folder_id: int):
        """
        Gets a list of documents in the given folder
        :param folder_id: The id of the folder to get documents from
        :return: A list of dictionaries, each dictionary representing a document
        """
        params = {'$filter': f'FolderId eq {folder_id}'}
        return self.get_all_data('Documents', params)

    def upload_document_from_file(self, file: Path, document_object: {} = None):
        """
        Helper function to upload a file to Landax by using a pathlib.Path object.
        :param file: The file to upload
        :param document_object: The associated document object, per the Landax API
        :return: requests.Response object, containing the response from Landax
        """
        if document_object is None:
            document_object = {}

        if not isinstance(file, Path):
            raise TypeError('file must be a pathlib.Path')

        if not file.exists():
            raise FileNotFoundError('file does not exist: ' + str(file))

        document_bytes = io.BytesIO(file.read_bytes())

        return self.upload_document(document_bytes, file.name, document_object)

    def upload_document(
            self,
            filedata: io.BytesIO,
            filename: str, folder_id: int,
            document_options: dict = None):
        """
        Upload a file to Landax by using an io.BytesIO object directly from memory.
        :param filedata: io.BytesIO object to upload of the document
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

        if 'ModuleId' in document_options:
            logging.warning('\
Warning: pylandax.upload_document does not support ModuleId parameter in document_options. It will be ignored. \
To upload a document linked to an object in a module, use pylandax.upload_linked_document instead.')
            del document_options['ModuleId']

        document_options['FolderId'] = folder_id

        response = self.documents_createdocument(filedata, filename, document_options)
        return response

    def upload_linked_document(
            self,
            filedata: io.BytesIO, filename: str, folder_id: int,
            module_name: str, linked_object_id: int,
            document_options: dict = None) -> requests.Response:
        """
        Upload a document to to Landax linked to another object via a module.
        :param filedata: io.BytesIO object to upload of the document
        :param filename: name of the file in Landax
        :param folder_id: the folder id to upload the document to
        :param module_name: name of the module to link the document to
        :param linked_object_id: the object id to associate with the document
        :param document_options: a dictionary of options to pass to the document object
        :return: True if the document was successfully uploaded and linked, False if something went wrong
        """

        if document_options is None:
            document_options = {}

        if 'FolderId' in document_options:
            logging.warning('\
Warning: pylandax.upload_linked_document does not support FolderId parameter in document_options. It will be ignored.')

        if 'ModuleId' in document_options:
            logging.warning('\
Warning: pylandax.upload_linked_document does not support ModuleId parameter in document_options. It will be ignored.')

        with open(Path(self.script_dir, 'modules.json')) as file:
            modules = json.loads(file.read())

        if module_name not in modules:
            logging.error(f'Error in pylandax.upload_linked_document: Module {module_name} not found.')
            return None

        module_id = modules[module_name]

        # This mapping maps the module id to the corresponding field name in the DocumentLink object
        # Should be updated as needed
        id_key_mapping = {
            10: 'CoworkerId',
            24: 'EquipmentId'
        }

        if module_id not in id_key_mapping:
            logging.error(f'Error in pylandax.upload_linked_document: Module {module_name}\'s id has no mapping to key')
            return None

        object_id_key = id_key_mapping[module_id]

        document_options['ModuleId'] = module_id

        document_link = {
            'FolderId': folder_id,
            object_id_key: linked_object_id
        }

        upload_response = self.documents_createdocument(filedata, filename, document_options, document_link)
        if upload_response.status_code != 200:
            logging.error(f'Error uploading document with filename {filename}: ' + upload_response.text)

        return upload_response

    def create_document(self, filedata: io.BytesIO, filename: str, document_object: dict, document_link: dict = None):
        """
        Create a document in Landax
        :param filename: The filename of the document
        :param filedata: The filedata of the document
        :param document_object: The document object to create
        :param document_link: The document link to create
        :return: The response from Landax
        """
        files = {
            'document': (None, json.dumps(document_object)),
            'fileData': (filename, filedata)
        }

        if document_link is not None:
            files['documentLink'] = (None, json.dumps(document_link))

        url = self.api_url + 'Documents/CreateDocument'
        response = requests.post(url, files=files, headers=self.headers)
        return response

    def get_document_content(self, document_id: int):
        """
        Retrieves the content of a document with the specified document ID.
        :param document_id (int): the id of the document to retrieve
        :return: The response object containing the content of the document.
        """
        initial_url = self.api_url + f'Documents/GetContent?documentid={document_id}&original=True&encode=raw'

        response = requests.get(initial_url, headers=self.headers)
        
        return response

    def push_document_content(self, document_data: io.BytesIO, document_id: int):
            """
            Pushes the content of a document with the specified document ID.
            :param document_data (io.BytesIO): The content of the document as a BytesIO object.
            :param document_id (int): The ID of the document.
            :return: The response object containing the result of the request.
            """
            doc_id = str(document_id)
            url = self.api_url + f'Documents/PushContent?documentid={doc_id}'

            data = document_data.read()

            response = requests.post(url, data=data, headers=self.headers)
            return response

    def custom_request(self, partial_url, method='GET', data=None) -> requests.Response:
        """
        Makes a custom request to the Landax API, given a partial url and a method
        :param partial_url: A partial URL to Landax, the part after v20/, eg. Documents/GetDocument
        :param method: The method to use, either GET or POST
        :param data: The data to send in the request, if any (only for POST)
        :return: The response from the request
        """
        url = self.api_url + partial_url

        if method == 'GET':
            response = requests.get(url, headers=self.headers)
        elif method == 'POST':
            response = requests.post(url, json=data, headers=self.headers)
        elif method == 'PATCH':
            response = requests.patch(url, json=data, headers=self.headers)
        elif method == 'DELETE':
            response = requests.delete(url, headers=self.headers)
        else:
            raise ValueError(
                f'pylandax.custom_request: Invalid method: {method}. Accepted methods: GET, POST, PATCH, DELETE')

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
