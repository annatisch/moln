import collections
import unittest.mock as mock

import pytest

import azure.storage.blob
import moln.storage

def test_blob_repr():
    path = moln.storage.BlobPath(container_name='containername', blob_name='blobname.txt', client=None)
    assert repr(path) == '/containername/blobname.txt'

def test_container_glob():
    container_name = 'containername'

    MockBlobProperties = collections.namedtuple("BlobProperties", [ "name" ])
    
    class MockClient(azure.storage.blob.ContainerClient):

        def __init__(self, container_name):
            self.name = container_name
            super().__init__('https://localhost', container_name=container_name)

        def list_blobs(self):
            return [
                MockBlobProperties('one'),
                MockBlobProperties('two.js'),
                MockBlobProperties('three/four'),
                MockBlobProperties('three/four.json'),
                MockBlobProperties('three/five.json'),
                MockBlobProperties('six'),
                MockBlobProperties('seven/eight/nine/five.json'),
            ]

    path = moln.storage.ContainerPath(container_name='containername', client=MockClient(container_name))

    recursive_json_files = set([str(bp) for bp in path.glob('**/*.json')])
    assert recursive_json_files == { '/containername/three/four.json', '/containername/three/five.json', '/containername/seven/eight/nine/five.json' }

    js_files = set([str(bp) for bp in path.glob('**/*.js')])
    assert js_files == { '/containername/two.js' }

    three_files_with_extensions = set([str(bp) for bp in path.glob('three/*.*')])
    assert three_files_with_extensions == { '/containername/three/four.json', '/containername/three/five.json' }

    three_files = set([str(bp) for bp in path.glob('three/*')])
    assert three_files == { '/containername/three/four.json', '/containername/three/five.json', '/containername/three/four' }

    # TODO: Should this test pass? It depends on if we "invent" folders for missing blobs in our glob implementation. 
    # root_files = set([str(bp) for bp in path.glob('*')])
    #assert root_files == { '/containername/one', '/containername/two.js', '/containername/three', '/containername/six', '/containername/seven' }
