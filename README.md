![](https://github.com/johanste/moln/workflows/Python%20application/badge.svg)

# moln {/mo:ln/}
Stupid simple access to [Microsoft Azure](https://azure.microsoft.com) services using Python. Built for the rest of us.


To install:
```bash
pip install moln
```

```python
import pathlib

import moln.storage

# Authentication is done using the azure-identity package.
# By default, it will use the azure.identity.DefaultAzureCredential
account = moln.storage.attach(account_url='https://molntest.blob.core.windows.net')

# Creating containers - just like you create directories!
container = account / 'jabbadabbadoo'
container.mkdir(exists_ok=True)

local_file = pathlib.Path('./stuff.json')
remote_file = container / 'stuff.json'

# Upload blobs like you would upload files - with the option to
# specify metadata like Content-Type headers for the uploaded blob.
if not remote_file.exists():
    with local_file.open(mode='rb') as lf:
        with remote_file.open(mode='wb', content_settings=azure.storage.blob.ContentSettings(content_type='application/json')) as rb:
            rb.write(lf.read())

# Work with the blob as if you opened a local file
with remote_file.open(mode='r') as rb:
    import json
    data = json.load(rb)
    print(data)
```
