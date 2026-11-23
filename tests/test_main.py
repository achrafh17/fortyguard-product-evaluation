import unittest
from main import payload, extract

class TestAPI(unittest.TestCase):
    def test_payload(self):
        d = payload("2024-07-15", "14:00", 100)
        c = d["polygon_aoi"]["features"][0]["geometry"]["coordinates"][0]
        self.assertEqual(c[0], c[-1])
        self.assertEqual(d["date_time"]["filter_type"], 1)

    def test_extract(self):
        self.assertEqual(extract({"data": {"activity_id": "abc"}}, "activity_id"), "abc")
        self.assertEqual(extract({"data": {"status": "Completed"}}, "status"), "Completed")
        with self.assertRaises(ValueError):
            extract({"data": {}}, "status")

if __name__ == "__main__":
    unittest.main()
