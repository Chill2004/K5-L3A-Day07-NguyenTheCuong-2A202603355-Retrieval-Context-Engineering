"""Offline checks of source-identifier parsing; no model requests."""
import unittest
from src.advanced.entities import caption_entities, requested_entities


class EntityLookupTests(unittest.TestCase):
    def test_vietnamese_and_english_aliases(self):
        self.assertEqual(requested_entities("H\u00ecnh O.7"),[("figure","O.7")])
        self.assertEqual(requested_entities("Figure O.7"),[("figure","O.7")])
        self.assertEqual(requested_entities("B\u1ea3ng 3.1"),[("table","3.1")])

    def test_multiple_entities(self):
        self.assertEqual(requested_entities("Figure S3.1 and Table 11.2"),[("figure","S3.1"),("table","11.2")])

    def test_caption_not_body_reference(self):
        self.assertEqual(caption_entities("Discussed in figure O.7 below.\nFigure O.70 A caption"),[("figure","O.70")])

    def test_no_partial_id(self):
        self.assertEqual(requested_entities("Figure O.70"),[("figure","O.70")])


if __name__=="__main__":
    unittest.main()
