# import pyodata
import requests
import json
import copy
# from pyodata.v2.model import PolicyFatal, PolicyWarning, PolicyIgnore, ParserError, Config


class Client:
	def __init__(self, config : dict):
		self.required_attrs = [
			'url', 'username', 'password',
			'client_id', 'client_secret'
		]

		for key, value in config.items():
			setattr(self, key, value)

		for attr in self.required_attrs:
			if not hasattr(self, attr):
				print(f'Error: config attribute is required: {attr}')
				return

		self.base_url = f'https://{self.url}/'
		self.api_url = self.base_url + 'api/v19/'
		self.headers = {}

		if hasattr(self, 'oauth_file'):
			self.oauth_data = self.oauth_from_file()
		else:
			self.oauth_data = self.oauth_from_server()

		self.headers['Authorization'] = 'Bearer ' + self.oauth_data['access_token']

		self.odata_client = None

		# Default: json format
		if not hasattr(self, 'format'):
			self.format = 'json'

		if self.format == 'xml':
			self.setup_odata_client()

	def setup_odata_client(self):
		session = requests.Session()
		session.headers = self.headers
		odata_config = Config(
			default_error_policy=PolicyFatal(),
			custom_error_policies={
				ParserError.ANNOTATION: PolicyWarning(),
				ParserError.ASSOCIATION: PolicyIgnore()
			})

		self.odata_client = pyodata.Client(self.api_url, session, config=odata_config)

	# Returns a record with the given data_id (Id in in landax)
	def get_single_data(self, data_model: str, data_id: int):
		url = f'{self.api_url}{data_model}({str(data_id)})?$format=json'
		response = requests.get(url, headers=self.headers)
		if response.status_code == 404:
			return None

		data = response.json()['d']['results']
		return data

	# Returns all records of the given data model
	def get_all_data(self, data_model: str) -> [{}]:
		if self.format == 'json':
			initial_url = f'{self.api_url}{data_model}?$format=json&$top=1000'
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
				new_url = initial_url + '&$skip=' + str(thousands * 1000)
				new_data = self.request_data(new_url)
				data = data + new_data
				count = len(new_data)

			return data

		elif self.format == 'xml':
			# WIP: the pyodata library from SAP doesn't parse ATOM correctly
			# See https://github.com/SAP/python-pyodata/issues/202
			# There are some other issues as well, so this isn't ready for use
			raise NotImplementedError
			# print('Warning: Using xml format, experimental feature')
			# print(self.odata_client.entity_sets)
			# data = getattr(self.odata_client.entity_sets, data_model)
			# print(data.get_entities().execute())
		else:
			print('Error: Unknown format: ' + self.format)

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
		url = f'{self.api_url}{data_model}({key})?$format={self.format}'
		response = requests.delete(url, headers=self.headers)
		if response.status_code == 404:
			return None
		return response

	# Helper function for get_data
	def request_data(self, url: str) -> []:
		response = requests.get(url, headers=self.headers)
		results = response.json()['d']['results']
		return results

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

	# Contact the remote server for an OAuth token
	def oauth_from_server(self):
		url = self.base_url + 'authenticate/token?grant_type=password'

		post_body = {
			'client_id': self.client_id,
			'client_secret': self.client_secret,
			'username': self.username,
			'password': self.password
		}

		result = requests.post(url, json=post_body)
		return result.json()

	# Load OAuth data from file
	def oauth_from_file(self):
		with open(self.oauth_file) as file:
			data = json.loads(file.read())

		return data
