import skript_keyword


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

    def create_arg_or_args(self, root_path="") -> list:
        splitted = self.arg_value.split()
        arg_created = []
        for s in splitted:
            single_arg = ""
            if self.arg_value != skript_keyword.POSITIONAL_ARGUMENT:
                single_arg += "--" + self.arg_name + " "
            single_arg += root_path + "/" + s
            arg_created.append(single_arg)

        return arg_created
