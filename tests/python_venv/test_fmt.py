"""Provide unit tests for `~python_venv.fmt`:py:mod:."""

import unittest

import parameterized  # https://pypi.org/project/parameterized/

from python_venv import fmt

########################################
# Tests


class TestFormat(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_PV_FM_000_instantiate(self):
        fmt.Formatter()

    def test_PV_FM_001_instantiate_with_args(self):
        fmt.Formatter(dummy_key="dummy_value")

    @parameterized.parameterized.expand(
        [
            ("none", {}, []),
            ("one", {"dummy_key": "dummy_value"}, ["dummy_key"]),
            (
                "more",
                {"dummy_key": "dummy_value", "dummy_key_2": "dummy_value_2"},
                ["dummy_key", "dummy_key_2"],
            ),
        ]
    )
    def test_PV_FM_010_keys(self, name, kwargs, expected):
        x = fmt.Formatter(**kwargs)
        self.assertListEqual(x.keys(), expected)

    def test_PV_FM_020_has(self):
        x = fmt.Formatter(dummy_key="dummy_value")
        self.assertTrue(x.has("dummy_key"))

    def test_PV_FM_030_get(self):
        x = fmt.Formatter(dummy_key="dummy_value")
        self.assertEqual(x.get("dummy_key"), "dummy_value")

    def test_PV_FM_031_get_default(self):
        x = fmt.Formatter()
        self.assertIsNone(x.get("dummy_key"))

    def test_PV_FM_032_get_default_value(self):
        x = fmt.Formatter()
        self.assertEqual(x.get("dummy_key", default="dummy_value"), "dummy_value")

    def test_PV_FM_033_get_raises(self):
        x = fmt.Formatter()
        with self.assertRaises(KeyError):
            x.get("dummy_key", should_raise=True)

    def test_PV_FM_040_set(self):
        x = fmt.Formatter()
        self.assertListEqual(x.keys(), [])
        x.set("dummy_key", "dummy_value")
        self.assertEqual(x.get("dummy_key"), "dummy_value")

    def test_PV_FM_041_set_override(self):
        x = fmt.Formatter(dummy_key="dummy_value")
        self.assertEqual(x.get("dummy_key"), "dummy_value")
        x.set("dummy_key", "new_dummy_value")
        self.assertEqual(x.get("dummy_key"), "new_dummy_value")

    @parameterized.parameterized.expand(
        [
            ("none", {}, [], []),
            ("one", {"dummy_key": "dummy_value"}, ["dummy_key"], ["dummy_value"]),
            (
                "more",
                {"dummy_key": "dummy_value", "dummy_key_2": "dummy_value_2"},
                ["dummy_key", "dummy_key_2"],
                ["dummy_value", "dummy_value_2"],
            ),
        ]
    )
    def test_PV_FM_050_add(self, name, kwargs, expected_keys, expected_values):
        x = fmt.Formatter()
        x.add(**kwargs)
        self.assertListEqual(x.keys(), expected_keys)
        if expected_keys:
            for key, value in zip(expected_keys, expected_values):
                self.assertEqual(x.get(key), value)

    def test_PV_FM_051_add_override(self):
        x = fmt.Formatter(dummy_key="dummy_value")
        x.add(dummy_key="new_dummy_value", dummy_key_2="dummy_value_2")
        self.assertEqual(x.get("dummy_key"), "new_dummy_value")
        self.assertEqual(x.get("dummy_key_2"), "dummy_value_2")

    @parameterized.parameterized.expand(
        [
            ("none", {}, "dummy_text", "dummy_text"),
            ("one_value", {"dummy_key": "dummy_value"}, "{dummy_key}", "dummy_value"),
            (
                "two_values",
                {"dummy_key": "dummy_value", "dummy_key_2": "dummy_value_2"},
                "{dummy_key} {dummy_key_2}",
                "dummy_value dummy_value_2",
            ),
            (
                "multi",
                {"dummy_key": "dummy_value", "dummy_key_2": "dummy_value_2"},
                ["{dummy_key}", "{dummy_key_2}", "{dummy_key} {dummy_key_2}"],
                ["dummy_value", "dummy_value_2", "dummy_value dummy_value_2"],
            ),
        ]
    )
    def test_PV_FM_100_format(self, name, kwargs, template, expected):
        x = fmt.Formatter(**kwargs)
        result = x.format(template)
        if isinstance(template, str):
            self.assertEqual(result, expected)
        else:
            self.assertListEqual(result, expected)

    def test_PV_FM_101_format_raises(self):
        x = fmt.Formatter()
        with self.assertRaises(KeyError) as raised:
            x.format("{nonexistent}")
        self.assertEqual(raised.exception.args[0], "nonexistent")
