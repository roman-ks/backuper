import hashlib
import os


def _get_root(name):
    if os.name == 'nt':
        return name + "\\"


class Drive:

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.root = _get_root(name)

    def __str__(self):
        return f'Drive(name={self.name}, id={self.id})'


class File:

    def __init__(self, name, drive):
        self.name = name
        self.drive = drive
        self.path = os.path.join(drive.root, name)
        self.sha256 = None

    def get_sha256(self):
        sha256_hash = hashlib.sha256()

        with open(self.path, "rb") as file:
            for byte_block in iter(lambda: file.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def exists(self):
        return os.path.exists(self.path)

    def get_last_modified(self):
        return os.path.getmtime(self.path)
