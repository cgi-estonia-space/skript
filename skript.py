import argparse
import subprocess
import yaml
import os
import requests
from tqdm import tqdm

import unpack

asset_dir = "/tmp/"
asset_stash_dir = "/tmp/"


def run_command(command, working_directory="."):
    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            cwd=working_directory,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        raise


def get_filename_from_url(url):
    # Send a HEAD request to the URL to retrieve headers
    response = requests.head(url)

    # Check if the request was successful (HTTP status code 200)
    if response.status_code == 200:
        # Try to get the filename from the Content-Disposition header
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('\'"')
        else:
            # If the header is not available, extract the filename from the URL
            filename = url.split("/")[-1]

        return filename
    else:
        print(f"Failed to retrieve headers for {url}, status code: {response.status_code}")
        return None


def download_http(url, save_directory):
    filename = get_filename_from_url(url)

    if filename:
        save_path = os.path.join(save_directory, filename)

        response = requests.get(url, stream=True)

        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))

            with open(save_path, 'wb') as file, tqdm(
                    desc=filename,
                    total=total_size,
                    unit='B',
                    unit_scale=True,
                    unit_divisor=1024,
            ) as bar:
                for data in response.iter_content(chunk_size=1024):
                    file.write(data)
                    bar.update(len(data))

            print(f"Downloaded {filename} to {save_directory}")
            return filename
        else:
            print(f"Failed to download {url}, status code: {response.status_code}")
            return None


def entries_in_directory(directory):
    entries = []
    for root, dirs, files in os.walk(directory):
        for entry in dirs + files:
            entry_path = os.path.join(root, entry)
            entries.append(entry_path)
    return entries


def file_exists_in_directory(directory, path_item):
    matching_entries = [entry for entry in entries_in_directory(directory) if path_item in entry]

    matching_files = [entry for entry in matching_entries if
                      os.path.isfile(entry) and entry.endswith(os.path.sep + path_item)]
    matching_folders = [
        entry for entry in matching_entries if os.path.isdir(entry) and entry.endswith(os.path.sep + path_item)
    ]

    if not matching_entries:
        return None
    elif len(matching_folders) == 1 and len(matching_files) == 0:
        return matching_folders[0]
    elif len(matching_files) == 1 and len(matching_folders) == 0:
        return matching_files[0]
    else:
        raise RuntimeError(f"Multiple matches found for '{path_item}':\n{matching_entries}")


def fetch_asset(asset_entry, dest_dir):
    asset_key_arg = next(iter(asset_entry))
    exist_entry = file_exists_in_directory(dest_dir, asset_entry[asset_key_arg])
    if exist_entry is None:
        if "url" not in asset_entry:
            raise RuntimeError(f"Given asset {asset_entry} not found in {dest_dir} and no source defined to download")
        the_uri = asset_entry["url"]
        content_file = download_http(the_uri, asset_stash_dir)
        if content_file is None:
            raise RuntimeError(f"Given asset {asset_entry} could not be downloaded from {the_uri}")
        if "post-process" in asset_entry:
            action = asset_entry["post-process"]
            if action == "UNPACK":
                print(f"Extracting {content_file} to {dest_dir}...")
                unpack.extract(os.path.join(asset_stash_dir, content_file), dest_dir)
            else:
                raise RuntimeError(
                    f"The post-process action {action} is not currently supported for asset {asset_entry}")
    else:
        return exist_entry

    return file_exists_in_directory(dest_dir, asset_entry[asset_key_arg])


def extract_if_multiple_assets_in_argument(asset_entry):
    arg_key = next(iter(asset_entry))
    arg_values = asset_entry[arg_key]
    arg_value_list = arg_values.split()
    if len(arg_value_list) == 1:
        return [asset_entry]

    first_item = asset_entry.copy()
    first_item[arg_key] = arg_value_list[0]
    multiple_arg_values_as_dict = [first_item]
    for i in range(1, len(arg_value_list)):
        multiple_arg_values_as_dict.append({arg_key: arg_value_list[i]})
    return multiple_arg_values_as_dict


def process_yaml(skript_file):
    with open(skript_file, "r") as file:
        skript_content = yaml.load(file, Loader=yaml.FullLoader)

    if "asset_dir" in skript_content:
        asset_dir = skript_content["asset_dir"]
    if "asset_stash_dir" in skript_content:
        asset_stash_dir = skript_content["asset_stash_dir"]
    else:
        asset_stash_dir = asset_dir

    if "tests" in skript_content:
        for test_id, test_data in skript_content["tests"].items():
            command_to_launch = []
            if "command" in test_data:
                command_to_launch.append(test_data["command"])
                if "assets" in test_data:
                    for a in test_data["assets"]:
                        asset_items = extract_if_multiple_assets_in_argument(a)
                        combine_multiple_args = False
                        arg_value = []
                        for asset in asset_items:
                            asset_path = fetch_asset(asset, asset_dir)
                            if asset_path is None:
                                raise RuntimeError(f"Failed to acquire {asset}")
                            arg_name = next(iter(asset))
                            if not combine_multiple_args and arg_name != "NONAME":
                                if len(arg_name) > 1:
                                    command_to_launch.append("--" + arg_name)
                                else:
                                    command_to_launch.append("-" + arg_name)
                            combine_multiple_args = True
                            arg_value.append(asset_path)

                        if len(arg_value) == 1:
                            command_to_launch.append(arg_value[0])
                        else:
                            arg_value_combined = " ".join(arg_value)
                            arg_value_combined = f'"{arg_value_combined}"'
                            command_to_launch.append(arg_value_combined)
                if "arguments" in test_data:
                    for arg in test_data["arguments"]:
                        arg_name = next(iter(arg))
                        if len(arg_name) > 1:
                            command_to_launch.append("--" + arg_name)
                        else:
                            command_to_launch.append("-" + arg_name)
                        command_to_launch.append(arg[arg_name])

                print(f"Running test '{test_id}' - {test_data['name']}")
                command_to_launch_str = " ".join(command_to_launch)
                print(f"Command str:\n{command_to_launch_str}")
                run_command(command_to_launch_str, "/tmp")
                print(f"Test '{test_id}' completed.")


if __name__ == "__main__":
    try:
        # Create an ArgumentParser object
        parser = argparse.ArgumentParser(description='Process YAML files')

        # Add an argument to accept an arbitrary number of file paths
        parser.add_argument('yaml_files', nargs='+', metavar='.yaml file', help='YAML file(s) to process')

        # Parse the command-line arguments
        args = parser.parse_args()
        for file_path in args.yaml_files:
            process_yaml(file_path)
    except RuntimeError as e:
        print(f"Caught RuntimeError:\n{e}")
    except Exception as e:
        print(f"Caught Exception:\n{e}")
