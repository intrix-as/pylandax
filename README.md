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
