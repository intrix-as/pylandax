import pylandax
import json
from pyodata.exceptions import HttpError

def test_basic():
	with open('mock_config.json') as file:
		landax_conf = json.loads(file.read())['landax']

	try:
		# Since the oauth token is bogus, we know this won't work
		# And it will throw a pyodata.exceptions.HttpError
		client = pylandax.Client(landax_conf)
	except HttpError:
		pass
