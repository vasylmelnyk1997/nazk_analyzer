import json
import os
import unittest

from api.api_server import resolve_document_path, resolve_list_path, read_json_file


class ApiServerTests(unittest.TestCase):
    def test_document_map_points_to_existing_file(self):
        path = resolve_document_path("31f44ed5-9d90-465d-858f-7e182f27c745")
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
        payload = read_json_file(path)
        self.assertIn("id", payload)

    def test_list_map_points_to_existing_file(self):
        path = resolve_list_path(1432475)
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))
        payload = read_json_file(path)
        self.assertIn("data", payload)

    def test_missing_document_is_not_mapped(self):
        self.assertIsNone(resolve_document_path("00000000-0000-0000-0000-000000000000"))


if __name__ == "__main__":
    unittest.main()
