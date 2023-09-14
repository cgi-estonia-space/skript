import unittest

from asset import Asset, AssetError


class TestAsset(unittest.TestCase):

    def test_that_if_empty_data_to_ctor_throws_asset_error(self):
        with self.assertRaisesRegex(AssetError, "provided without items"):
            obj = Asset()

    def test_if_arg_not_supplied_throws_asset_error(self):
        with self.assertRaisesRegex(AssetError, "definition shall begin either with 'NONAME'"):
            obj = Asset(url="value")

        with self.assertRaisesRegex(AssetError, "definition shall begin either with 'NONAME'"):
            values = {"url": "www.tere.ee", "post-process": "UNPACK", "destination": "/tmp/"}
            obj = Asset(values)

    def test_if_arg_not_first_throws_asset_error(self):
        with self.assertRaises(AssetError):
            obj = Asset(url="value", NONAME="definition shall begin either with")
        with self.assertRaises(AssetError):
            obj = Asset(url="value", tere="foo")

    def test_if_additional_definitions_supplied_throws_asset_error(self):
        with self.assertRaisesRegex(AssetError, "has extraneous fields: some_random"):
            obj = Asset(arg_name="hei", url="http://tere.www", some_random="optional_value")

    def test_all_values_parsed(self):
        # Test that all values are correctly parsed
        obj = Asset(arg_name="hei", url="http://tere.www", destination="/tmp/")

        self.assertEqual(obj.url, "http://tere.www")
        self.assertEqual(obj.destination, "/tmp/")

    def test_when_arg_has_multiple_files_they_are_repeated_with_arg_name(self):
        obj = Asset(dem="srtm_20_20.tif srtm_10_05.tif srtm_05_15.tif")
        result = obj.create_arg_or_args("/tmp")
        expected = ["--dem /tmp/srtm_20_20.tif", "--dem /tmp/srtm_10_05.tif", "--dem /tmp/srtm_05_15.tif"]

        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()
