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
response = client.upload_document(open(my_file, 'rb').read(), folder_id)
```

## Uploading linked documents

By default, uploaded documents will be associated with the Documents module in Landax and tied to its folder ids.

However, it may be desirable to upload documents linked to other objects in other modules, such as coworkers or equipment.

In this case, a different function has to be used. In this example, we'll upload a document linked to a coworker:
```
    coworker_id = 123
    filename = 'test.pdf'
    # Folder id in the coworkers module
    folder_id = 560
    # Not all modules are implemented in pylandax yet, see the source code for the full list
    module_name = 'COWORKERS'

    # The function returns True if all is successful and False if not
    upload_succeeded = client.landax_client.upload_linked_document(
        open(filename, 'rb').read(), filename, folder_id, module_name, coworker_id)
```
