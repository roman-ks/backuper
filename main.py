import datetime
import os
import shutil
import string
from files_module import Drive, File

rel_file_path = 'backup/MainDatabase.kdbx'


def get_drives():
    drives_list = []
    if os.name == 'nt':  # win
        for letter in string.ascii_uppercase:
            drive_path = letter + ":\\"
            if os.path.exists(drive_path):
                drives_list.append(Drive(str(os.stat(drive_path).st_dev) + '-win', letter + ':'))

    return drives_list


def get_abs_file_paths(drives_list):
    return [os.path.join(drive.root, rel_file_path) for drive in drives_list]


def get_newest_file(files):
    existent_files = filter(lambda x: x.exists(), files)
    return next(iter(sorted(existent_files, key=lambda x: x.get_last_modified())))


drives_list = get_drives()
drives_str = ', '.join(map(str,drives_list))
print(f'Found {len(drives_list)} drives: [{drives_str}]')

files = [File(rel_file_path, drive) for drive in drives_list]

existent_files = filter(lambda x: x.exists(), files)
if existent_files:
    newest_file = get_newest_file(files)
    newest_date = datetime.datetime.fromtimestamp(newest_file.get_last_modified())
    print(f'Newest file {newest_file.path}({newest_date.strftime("%Y-%m-%d %H:%M:%S")})')

    for file in files:
        if file != newest_file:
            if not file.exists() or (file.exists() and newest_file.get_sha256() != file.get_sha256()):
                os.makedirs(os.path.dirname(file.path), exist_ok=True)
                shutil.copy2(newest_file.path, file.path)

                file_hash = file.get_sha256()
                print(
                    f'Copied to drive: {file.drive.name}, id:{file.drive.id}, abs path: {file.path}, hash:{file_hash}')
            else:
                print(f'File {file.path} up to date')

else:
    print("File not found on any drive")
