import os
import sys
import json
from pathlib import Path

sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/../src")

import pylandax

script_dir = Path(os.path.dirname(os.path.realpath(__file__)))


def test_basic():
    confpath = Path(script_dir, 'mock_config.json')
    with open(confpath) as file:
        conf = json.loads(file.read())['landax']

    try:
        client = pylandax.Client(conf['url'], conf['credentials'])
    # Since the URL is bogus, this is what we expect
    except pylandax.LandaxAuthException:
        pass


def test_generate_url():
    base_url = 'https://test.landax.com'
    params = {
        'test': 'test',
        'test2': 'test2'
    }

    result = pylandax.Client.generate_url(base_url, params)
    assert result == 'https://test.landax.com?test=test&test2=test2'

    result2 = pylandax.Client.generate_url(base_url, {})
    assert result2 == 'https://test.landax.com'
