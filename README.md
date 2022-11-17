# pylandax

A simple Python library for interfacing with Landax' API. Under active development.

# Usage

The library can be used as follows:

```
import pylandax

url = 'https://eksempel.landax.no'
credentials = {
  'username': 'my_user',
  'password': 'my_password',
  'client_id': 'my_client_id',
  'client_secret': 'my_client_secret'
}

client = pylandax.Client(url, credentials)

# Getting data
# The Contacts table is used an example here, but any table in Landax works
result = client.get_all_data('Contacts')

# Posting data, using Contacts as example again
new_contact = {
  'Name': 'Example Corp.',
  'Address': 'Park road 123'
}

client.post_data('Contacts', new_contact)
```

## Uploading documents

To upload a document, it's recommended to pass a Path-object and folder id to the upload_document like so:

```
from pathlib import Path
import pylandax

# Credentials and URL as defined above
client = pylandax.Client(url, credentials)
# Example values, this case assumes the file is in cwd
my_file = Path('myfile.pdf')
folder_id = 100

# The function returns the requests.Response object
response = client.upload_document(my_file, folder_id)
```
