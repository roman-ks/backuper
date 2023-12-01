import hashlib
import os
import datetime


def _get_root(name):
    if os.name == 'nt':
        return name + "\\"


class Drive:

    def __init__(self, id, sys_name):
        self.id = id
        self.sys_name = sys_name
        self.root = _get_root(sys_name)
        self.name = None
        self.folder_path = None

    def __str__(self):
        return f'Drive(sys_name={self.sys_name}, id={self.id}, name={self.name})'

    def __eq__(self, other):
        return self.id == other.id


class File:

    def __init__(self, rel_path, drive):
        self.drive = drive
        self.rel_path = rel_path
        self.path = os.path.join(drive.folder_path, rel_path)

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

    def get_str_last_modified(self, dateformat="%Y-%m-%d %H:%M:%S"):
        date = datetime.datetime.fromtimestamp(self.get_last_modified())
        return date.strftime(dateformat)

    def __eq__(self, other):
        return self.get_sha256() == other.get_sha256()
