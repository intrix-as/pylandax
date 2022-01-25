import pyodata
import requests
import json
from pyodata.v2.model import PolicyFatal, PolicyWarning, PolicyIgnore, ParserError, Config

class Client:
	def __init__(self, config : dict):
		self.host = config['host']
		self.username = config['username']
		self.password = config['password']
		self.client_id = config['client_id']
		self.client_secret = config['client_secret']

		if 'oauth_file' in config:
			self.oauth_file = config['oauth_file']
		else:
			self.oauth_file = None

		self.base_url = f'https://{self.host}/'
		self.api_url = self.base_url + 'api/v19/'
		self.headers = {}

		self.authenticate()
		self.setup_odata_client()

	def authenticate(self):
		if self.oauth_file is not None:
			self.oauth_data = self.oauth_from_file()
		else:
			self.oauth_data = self.oauth_from_server()

		self.headers['Authorization'] = 'Bearer' + self.oauth_data['access_token']

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
