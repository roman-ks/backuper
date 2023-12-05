import os
import shutil
import string
import json
import glob
import urllib.request

from files_module import Drive, File

config = {}
drive_name_file = ''
rel_folder_path = ''
include_pathname = ''
exclude_pathname = ''


def load_config():
    with open('backuper_config.json', 'r') as conf_file:
        global config
        config = json.load(conf_file)

    global drive_name_file
    drive_name_file = config.get("files", {}).get("drive_name_file", None)
    global rel_folder_path
    rel_folder_path = config["folder_path"]
    global include_pathname
    include_pathname = config.get("files", {}).get("include", None)
    global exclude_pathname
    exclude_pathname = config.get("files", {}).get("exclude", None)


def get_drives():
    drives_list = []
    if os.name == 'nt':  # win
        for letter in string.ascii_uppercase:
            drive_path = letter + ":\\"
            if os.path.exists(drive_path):
                drives_list.append(Drive(str(os.stat(drive_path).st_dev) + '-win', letter + ':'))

    if drive_name_file:
        for drive in drives_list:
            drive_name_file_path = os.path.join(drive.root, rel_folder_path, drive_name_file)
            if os.path.exists(drive_name_file_path) and os.path.isfile(drive_name_file_path):
                with open(drive_name_file_path, "r") as name_file:
                    name = name_file.read()
                    drive.name = name

    for drive in drives_list:
        drive.folder_path = os.path.join(drive.root, rel_folder_path)

    return drives_list


def get_files_on_drive(drive):
    paths = glob.glob(os.path.join(drive.folder_path, include_pathname), recursive=True)

    drive_name_file_on_this_drive = os.path.join(drive.folder_path, drive_name_file)
    if drive_name_file_on_this_drive in paths:
        paths.remove(os.path.join(drive.folder_path, drive_name_file))

    if exclude_pathname:
        excluded_paths = glob.glob(os.path.join(drive.folder_path, exclude_pathname), recursive=True)
        paths = [p for p in paths if p not in excluded_paths]

    file_paths = filter(lambda x: os.path.isfile(x), paths)

    return [File(os.path.relpath(path, drive.folder_path), drive) for path in file_paths]


def get_unique_paths():
    rel_paths = set({})
    for drive in drives_list:
        files = get_files_on_drive(drive)

        [rel_paths.add(file.rel_path) for file in files]

    return rel_paths


def get_newest_file(files):
    existent_files = filter(lambda x: x.exists(), files)
    return next(iter(sorted(existent_files, key=lambda x: x.get_last_modified(), reverse=True)))


def file_to_dto(file):
    return {
        "path": file.rel_path,
        "driveId": file.drive.id,
        "driveName": file.drive.name,
        "lastModified": file.get_last_modified()
    }


def post_to_endpoint(files):
    print("Preparing to do POST to endpoint")
    url = config["endpoint"]
    if not url:
        print("No endpoint config")
        return

    request_list = [file_to_dto(file) for file in files]

    data = json.dumps(request_list).encode('utf8')
    request = urllib.request.Request(url, data=data,
                                     headers={'content-type': 'application/json'})
    try:
        response = urllib.request.urlopen(request)
        if response.code == 200:
            print("Posted successfully")
        else:
            print(f"Response code: {response.getCode()}")
    except Exception as e:
        print(f"Error posting: {e}")


load_config()
if not config.get('folder_path', None):
    print("folder_path not set in config!")
    exit(0)

drives_list = get_drives()
drives_str = ', '.join(map(str, drives_list))
print(f'Found {len(drives_list)} drives: [{drives_str}]')

unique_files = get_unique_paths()
print(f"Found unique files: {unique_files}")
copied_files = []
for unique_path in unique_files:
    # list files with the same path on different drives
    files_on_drives = []
    for drive in drives_list:
        files_on_drives.append(File(unique_path, drive))

    # get newest
    newest_file = get_newest_file(files_on_drives)
    print(f"Newest {unique_path}: {newest_file.get_str_last_modified()}")
    # copy newest to all drives
    for drive in drives_list:
        file_on_this_drive = File(newest_file.rel_path, drive)
        if drive != newest_file.drive:
            if file_on_this_drive.exists() and file_on_this_drive == newest_file:
                print(f"File {file_on_this_drive.path} is up to date")
            else:
                os.makedirs(os.path.dirname(file_on_this_drive.path), exist_ok=True)
                shutil.copy2(newest_file.path, file_on_this_drive.path)
                print(f'Copied {newest_file.path} to {file_on_this_drive.path}')
                copied_files.append(file_on_this_drive)
        else:
            print(f"File {file_on_this_drive.path} is up to date")

if copied_files:
    post_to_endpoint(copied_files)
