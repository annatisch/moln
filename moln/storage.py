"""Simplified access to Azure Blob Storage.

.. code-block:: python

    import moln.storage

    # "Attaching" to the Azure Storage account gives me a pathlib.Path-like
    # object
    root = moln.storage.attach('https://molntest.blob.core.windows.net')

    # I can navigate to a specific blob
    blob = root / 'mycontainer' / 'myblob.json'

    # Downloading the blob is as easy as open:ing it.
    with blob.open(mode='r') as b:
        print(b.read())
"""

import abc
import fnmatch
import io

import azure.core.exceptions
import azure.identity
import azure.storage.blob

__all__ = ["AzurePath", "attach"]


class AzurePath(abc.ABC):
    """pathlib.Path-like object for interacting with Azure Storage Blobs.
    """

    @abc.abstractmethod
    def __truediv__(self, other):
        ...

    @abc.abstractmethod
    def mkdir(self, *, exists_ok: bool = False, **kwargs):
        """Create a new directory (container)

        Only supported for container-level paths.

        :param exists_ok: Don't report an error if directory (container) already exists.
        """

    @abc.abstractmethod
    def open(self, *, mode="r", **kwargs):
        """Open the given file (blob)

        Only supported for blob-level paths.
        """

    def is_dir(self):
        return False

    def is_file(self):
        return False


class AccountPath(AzurePath):
    def __init__(self, *, account_url=None, connection_string=None, **kwargs):
        if not account_url and not connection_string:
            raise ValueError(
                "Must specify either a connection string or an account_url"
            )

        if connection_string:
            self.client = azure.storage.blob.BlobServiceClient.from_connection_string(
                connection_string, **kwargs
            )
        else:
            kwargs.setdefault("credential", azure.identity.DefaultAzureCredential())
            self.client = azure.storage.blob.BlobServiceClient(account_url, **kwargs)

    def __truediv__(self, other):
        return ContainerPath(other, self.client.get_container_client(other))

    def open(self, *, mode="r", **kwargs):
        raise TypeError(f'Unable to open an account path for "{mode}""')

    def mkdir(self, exists_ok=False, **kwargs):
        raise TypeError("Unable to mkdir an account.")


class ContainerPath(AzurePath):
    def __init__(self, container_name, client):
        self.name = container_name
        self.client = client

    def mkdir(self, *, exists_ok=False, **kwargs):
        try:
            self.client.create_container(**kwargs)
        except azure.core.exceptions.ResourceExistsError:
            if not exists_ok:
                raise

    def open(self, *, mode="r", **kwargs):
        raise TypeError(f'Unable to open a container path for "{mode}""')

    def exists(self):
        try:
            self.client.get_container_properties()
            return True
        except azure.core.exceptions.ResourceNotFoundError:
            return False

    def glob(self, pattern, **kwargs):
        # ISSUE - should we manufacure "directories" when globbing blobs?
        if pattern.startswith("**/"):
            # recursive = True
            pattern = pattern[3:]
        # else:
        #    recursive = False

        if pattern[0] == ".":
            # leading_dot = True
            pattern = pattern[1:]
        # else:
        #    leading_dot = False

        for blob in self.client.list_blobs():
            if fnmatch.fnmatch(blob.name, pattern):
                yield BlobPath(
                    blob_name=blob.name,
                    container_name=self.name,
                    client=self.client.get_blob_client(blob),
                )

    def is_dir(self):
        return self.exists()

    def __truediv__(self, other):
        return BlobPath(
            container_name=self.name,
            blob_name=other,
            client=self.client.get_blob_client(other),
        )


class BlobPath(AzurePath):
    def __init__(self, container_name, blob_name, client):
        self.container_name = container_name
        self.name = blob_name
        self.client = client

    def __truediv__(self, other):
        # TODO - what should the correct behavior be here? Append a '/<other>' to the name or raise? Or give me a snapshot?
        raise NotImplementedError(
            "Undone - navigate below blogs is currently not implemented"
        )

    def exists(self):
        try:
            self.client.get_blob_properties()
            return True
        except azure.core.exceptions.ResourceNotFoundError:
            return False

    def is_file(self):
        return self.exists()

    def open(self, *, mode="r", **kwargs):
        if "r" in mode:
            return DownloadStream(self.client)
        elif "w" in mode:
            return UploadStream(self.client, **kwargs)

    def mkdir(self, exists_ok=False, **kwargs):
        raise TypeError("Unable to mkdir a blob.")

    def __repr__(self):
        return f"/{self.container_name}/{self.name}"


class DownloadStream(io.RawIOBase):
    def __init__(self, client: azure.storage.blob.BlobClient):
        self.client = client
        self.position = 0

    def read(self, size=-1):
        data_to_read = 4096 if size == -1 else size
        stream = self.client.download_blob(offset=self.position, length=data_to_read)
        data = stream.readall()
        self.position += len(data)
        return data

    def readinto(self, b):
        bufoffset = 0
        data_to_read = len(b)
        done = False
        while not done:
            read_data = self.read(data_to_read)
            data_read = len(read_data)

            if data_read:
                b[bufoffset : bufoffset + data_read] = read_data
                bufoffset += data_read

            done = data_read == 0 or bufoffset == len(b)

        return bufoffset

    def readall(self):
        blob_properties = self.client.get_blob_properties()
        data_to_read = blob_properties.size
        buf = bytearray(data_to_read)
        self.readinto(buf)
        return buf

    def write(self):
        raise NotImplementedError(
            "Huh - someone tried to write to a download stream. Never cross the streams!"
        )


class UploadStream(io.BytesIO):
    def __init__(self, client, **kwargs):
        self.client = client
        self.kwargs = kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if not exc_type:
            self.close()

    def close(self):
        self.seek(0)
        self.client.upload_blob(self, **self.kwargs)
        super().close()


def attach(
    *, account_url: str = None, connection_string: str = None, **kwargs
) -> AzurePath:
    """Attach to an existing azure storage account.

    :param account_url: Url of storage account to attach to. Required unless `connection_string` is provided.
    :param connection_string: Connection string of storage account to attach to. Required unless `account_url` is provided.
    """
    return AccountPath(
        account_url=account_url, connection_string=connection_string, **kwargs
    )
