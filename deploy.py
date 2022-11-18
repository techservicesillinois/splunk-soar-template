#!/usr/bin/env python

import base64
import json
import os
import requests
import sys

file_contents = open(sys.argv[1], 'rb').read()
encoded_contents = base64.b64encode(file_contents)
payload = {'app': encoded_contents.decode('ascii')}
headers = {'ph-auth-token': os.environ['SOAR_TOKEN']}
hostname = os.environ['SOAR_HOSTNAME']
result = requests.post(f'https://{hostname}/rest/app',
                       headers=headers,
                       data=json.dumps(payload))

print(result.text)

if result.status_code != requests.codes.ok or 'failed' in result.json():
    sys.exit(1)
