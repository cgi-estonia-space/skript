import argparse
import subprocess
import sys

import yaml
import os

from asset import Asset, AssetError
import skript_fs_util as fs_util
import unpack
import uri_fetch


class AssetLocations:
    def __init__(self, assets, stash):
        self.asset_dir = assets
        self.stash_dir = stash


launch_failures = 0
exit_on_launch_error = False
launch_count = 0


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
        global launch_failures
        launch_failures += 1
        global exit_on_launch_error
        if exit_on_launch_error:
            raise


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


def process_yaml(skript_file, asset_dir=None, stash_dir=None):

    asset_locations = AssetLocations("/tmp/", "/tmp/")
    with open(skript_file, "r") as file:
        skript_content = yaml.load(file, Loader=yaml.FullLoader)

    if asset_dir is not None:
        asset_locations.asset_dir = asset_dir
        asset_locations.stash_dir = asset_dir  # Same until specification is well thought through
    elif "asset_dir" in skript_content:
        asset_locations.asset_dir = skript_content["asset_dir"]
        asset_locations.stash_dir = skript_content["asset_dir"]  # Same until specification is well thought through
    else:
        raise RuntimeError(f"Please specify asset directory either via '--asset_dir' or 'asset_dir' key in skript.")

    if stash_dir is not None:
        asset_locations.stash_dir = stash_dir
    elif "stash_dir" in skript_content:
        asset_locations.stash_dir = skript_content["stash_dir"]

    if not os.path.exists(asset_locations.asset_dir) or not os.path.isdir(asset_locations.asset_dir):
        raise RuntimeError(f"Given asset dir '{asset_locations.asset_dir}' does not exist")

    if not os.path.exists(asset_locations.stash_dir) or not os.path.isdir(asset_locations.stash_dir):
        raise RuntimeError(f"Given stash dir '{asset_locations.stash_dir}' does not exist")

    global launch_count
    if "tests" in skript_content:
        for test_id, test_data in skript_content["tests"].items():
            command_to_launch = []
            if "command" in test_data:
                command_to_launch.append(test_data["command"])
                if "assets" in test_data:
                    for a in test_data["assets"]:
                        asset_items = extract_if_multiple_assets_in_argument(a)
                        for asset in asset_items:
                            the_asset = Asset(asset)
                            asset_path = the_asset.fetch(asset_locations.asset_dir, asset_locations.stash_dir)
                            if asset_path is None:
                                raise RuntimeError(f"Failed to acquire {asset}")
                            arg_set = the_asset.create_arg_or_args(asset_locations.asset_dir)
                            for an_arg in arg_set:
                                command_to_launch.append(an_arg)

                if "arguments" in test_data:
                    for arg in test_data["arguments"]:
                        arg_name = next(iter(arg))
                        if len(arg_name) > 1:
                            command_to_launch.append("--" + arg_name)
                        else:
                            command_to_launch.append("-" + arg_name)
                        if arg[arg_name] is not None:
                            command_to_launch.append(arg[arg_name])

                print(f"Running test '{test_id}' - {test_data['name']}")
                launch_count += 1
                command_to_launch_str = " ".join(command_to_launch)
                print(f"Command str:\n{command_to_launch_str}")
                run_command(command_to_launch_str, "/tmp")
                print(f"Test '{test_id}' completed.")


if __name__ == "__main__":
    skript_count = 0
    try:
        # Create an ArgumentParser object
        parser = argparse.ArgumentParser(description='Process YAML files')

        # Add an argument to accept an arbitrary number of file paths
        parser.add_argument('yaml_files', nargs='+', metavar='.yaml file', help='YAML file(s) to process')
        parser.add_argument('--asset_dir', metavar='asset_directory', help='Path to the asset directory')

        # Parse the command-line arguments
        args = parser.parse_args()
        for file_path in args.yaml_files:
            skript_count += 1
            process_yaml(file_path, args.asset_dir, args.asset_dir)
    except AssetError as e:
        print(f"There was an error raised concerning asset:\n{e}")
        sys.exit(10)
    except RuntimeError as e:
        print(f"Caught RuntimeError:\n{e}")
        sys.exit(1)
    except Exception as e:
        print(f"Caught Exception:\n{e}")
        sys.exit(2)

    print(f"Ran {launch_count} items from {skript_count} skripts with {launch_failures} failures")
    if launch_failures > 0:
        if launch_failures > 255 - 100:
            sys.exit(255)
        else:
            sys.exit(100 + launch_failures)
