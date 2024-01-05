import os
import sys
from pathlib import Path

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

import pylandax

script_dir = Path(os.path.dirname(os.path.realpath(__file__)))

url = 'example.landax.no'
credentials = {
    "client_id": "123456",
    "client_secret": "123456",
    "username": "123456",
    "password": "123456"
}

client = pylandax.Client(url, credentials)

def test_all_data_functions():
    get_all_data = client.get_all_data('Contacts')
    print(f'Get all data: {bool(get_all_data)}\n')

    if bool(get_all_data) == True:
        post_data = client.post_data('Contacts', {'FirstName': 'Test'})
        print(f'Post data: {post_data}\n')

        if post_data.status_code == 201:
            get_single_data = client.get_single_data('Contacts', post_data.json()['Id'])
            print(f'Get single data: {bool(get_single_data)}\n')

            if bool(get_single_data) == True:
                patch_data = client.patch_data('Contacts', post_data.json()['Id'], {'FirstName': 'Test222'})
                print(f'Patch data: {patch_data}\n')

                if patch_data.status_code == 204:
                    delete_data = client.delete_data('Contacts', post_data.json()['Id'])
                    print(f'Delete data: {delete_data}\n')

                    if delete_data.status_code == 200:
                        print('All data functions tested successfully!\n')
                        return True



def test_all_document_functions():
    # test folder id
    # make sure the folder contains at least one document
    pylandax_test_folder_id = 192
    print(f'Pylandax test folder id: {pylandax_test_folder_id}\n')

    get_documents = client.get_documents(pylandax_test_folder_id)
    print(f'Get documents: {bool(get_documents)}\n')

    if bool(get_documents) == True:
        get_document_content = client.get_document_content(get_documents[0]['Id'])
        print(f'Documents get content: {get_document_content}\n')

        if get_document_content.status_code == 200:        
            documents_upload = client.upload_document(get_document_content.content, f'test-{get_documents[0]["FileName"]}', pylandax_test_folder_id)
            print(f'Documents upload: {documents_upload}\n')

            if documents_upload.status_code == 200:            
                push_document_content = client.push_document_content(get_document_content.content, int(get_documents[0]['Id']))
                print(f'Document push content: {push_document_content}\n')

                if push_document_content.status_code == 200:
                    delete_document = client.delete_data('Documents', documents_upload.json()['value']['document']['DocumentId'])
                    print(f'Delete document: {delete_document}\n')

                    if delete_document.status_code == 200:
                        print('All document functions tested successfully!\n')
                        return True


if __name__ == '__main__':
    try:
        assert test_all_data_functions() == True
    except AssertionError:
        print('All data functions failed!\n')

    try:
        assert test_all_document_functions() == True
    except AssertionError:
        print('All document functions failed!\n')
