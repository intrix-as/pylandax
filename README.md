# pylandax

A simple Python library for interfacing with Landax' API. Under active development.

## Setup

This is typically used as a submodule, which can be added to a python project as follows:

```(bash)
git submodule add git@github.com:intrix-as/pylandax.git ./src/pylandax
```

This will put pylandax in the src/pylandax folder of the project, which can then be imported as a module.

The library can be used as follows:

## Usage

```(python)
import pylandax

url = 'eksempel.landax.no'
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
  'FirstName': 'Example Corp.',
}

client.post_data('Contacts', new_contact)
```

## Uploading documents

To upload a document, it's recommended to pass a Path-object and folder id to the upload_document like so:

```(python)
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

```(python)
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
