"""
Just for testing the basic database methods 
"""
import models as db
import unittest

class ModelsTest(unittest.TestCase):

    def setUp(self):
        db.initialize_db()

    def tearDown(self):
        db.drop_database()

    def test_db_exists(self):
        self.assertTrue(db.db_exists("Planet"))

    def test_route_table_exists(self):
        exists = db.table_exists("routes")
        self.assertTrue(exists)

    def test_route_len_table_exists(self):
        exists = db.table_exists("route_lengths")
        self.assertTrue(exists)

if __name__ == "__main__":
    unittest.main()
