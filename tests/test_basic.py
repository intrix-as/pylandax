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
