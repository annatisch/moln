import pathlib

import azure.storage.blob
import moln.storage

account = moln.storage.attach(account_url='https://molntest.blob.core.windows.net')

container = account / 'jabbadabbadoo'
container.mkdir(exists_ok=True)

local_file = pathlib.Path('./stuff.json')
remote_file = container / 'stuff.json'

if not remote_file.exists():
    with local_file.open(mode='rb') as lf:
        with remote_file.open(mode='wb', content_settings=azure.storage.blob.ContentSettings(content_type='application/json')) as rb:
            rb.write(lf.read())

with remote_file.open(mode='r') as rb:
    import json
    data = json.load(rb)
    print(data)

for blob in container.glob('**/*.*'):
    print(blob)

with (container / 'customspeech.swagger.json').open(logging_enable=True) as f:
    for line in f:
        print(line)