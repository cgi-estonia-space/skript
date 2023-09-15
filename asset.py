import os

import skript_fs_util as fs_util
import skript_keyword
import unpack
import uri_fetch


class AssetError(Exception):
    pass


class Asset:
    def __init__(self, dict_obj=None, **kwargs):
        self.__dict__.update(dict_obj or {})
        combined_dict = {**self.__dict__, **(kwargs or {})}

        if len(combined_dict) < 1:
            raise AssetError("Asset was provided without items, this is implementation error")

        self.special_keys = ['url', 'post-process', 'destination', skript_keyword.POSITIONAL_ARGUMENT]
        self.arg_name = next(iter(combined_dict))
        if self.arg_name != skript_keyword.POSITIONAL_ARGUMENT and self.arg_name in self.special_keys:
            raise AssetError(
                f"The 'asset' definition shall begin either with '{skript_keyword.POSITIONAL_ARGUMENT}' or real argument name")

        self.arg_value = combined_dict[self.arg_name]
        if len(self.arg_value) < 1:
            raise AssetError("C'mon the asset gotta have some meaningful resource name")

        keys_not_special = [key for key in combined_dict if key not in self.special_keys and key != self.arg_name]
        if len(keys_not_special) > 0:
            raise AssetError(f"Asset definition has extraneous fields: {', '.join(keys_not_special)}")

        for key in self.special_keys:
            if key in combined_dict:
                setattr(self, key, combined_dict[key])
            else:
                setattr(self, key, None)

        self.asset_path = None

    def create_arg_or_args(self, root_path="") -> list:
        splitted = self.arg_value.split()
        arg_created = []
        for s in splitted:
            single_arg = ""
            if self.arg_name != skript_keyword.POSITIONAL_ARGUMENT:
                if len(self.arg_name) == 1:
                    single_arg += "-"
                else:
                    single_arg += "--"
                single_arg += self.arg_name + " "
            if os.path.isabs(s):
                single_arg += s
            else:
                single_arg += root_path + "/" + s
            arg_created.append(single_arg)

        return arg_created

    def fetch(self, asset_store_dir="", fetch_store_dir=""):
        if os.path.isabs(self.arg_value):
            return self.arg_value

        exist_entry = fs_util.file_exists_in_directory(asset_store_dir, self.arg_value)
        if exist_entry is None:
            if self.url is None:
                raise RuntimeError(f"Given asset {self.arg_value} not found in {asset_store_dir} and no source defined to download")
            content_file = uri_fetch.fetch(self.url, fetch_store_dir)
            if content_file is None:
                raise RuntimeError(f"Given asset {self.arg_value} could not be downloaded from {self.url}")
            if os.path.basename(content_file) != os.path.basename(self.arg_value) and self.__dict__["post-process"] is None:
                raise RuntimeError(f"The asset '{self.arg_value}' fetched from '{self.url}' has different form - {content_file}")
            if self.__dict__["post-process"] is not None:
                action = self.__dict__["post-process"]
                if action == "UNPACK":
                    print(f"Extracting {content_file} to {asset_store_dir}...")
                    unpack.extract(os.path.join(fetch_store_dir, content_file), asset_store_dir)
                else:
                    raise RuntimeError(
                        f"The post-process action {action} is not currently supported for asset {self.arg_value}")
        else:
            self.asset_path = exist_entry
            return self.asset_path

        self.asset_path = fs_util.file_exists_in_directory(asset_store_dir, self.arg_value)
        return self.asset_path
