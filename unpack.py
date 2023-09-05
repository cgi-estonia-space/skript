import os
import tarfile
import zipfile


def extract(file_path, dest_dir):
    # Check the file extension to determine the archive type
    file_extension = os.path.splitext(file_path)[1].lower()

    unpacked_items = []
    if file_extension == ".zip":
        # Unpack ZIP archive
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            zip_ref.extractall(dest_dir)
            unpacked_items = zip_ref.namelist()
    elif file_extension in (".tar", ".gz", ".tgz"):
        # Unpack TAR or GZipped TAR archive
        with tarfile.open(file_path, 'r:*') as tar_ref:
            tar_ref.extractall(dest_dir)
            unpacked_items = tar_ref.namelist()
    else:
        raise RuntimeError(f"Unsupported archive format for '{file_path}'")

    return unpacked_items
