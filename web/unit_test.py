import models as db
import unittest

class ModelsTest(unittest.TestCase):

    # def test_init(self):
    #     db.initialize_db_with_extension_and_table()

    # def test_table_exists_returns_true(self):
    #     exists = db.table_exists("routes")
    #     self.assertTrue(exists)
    #
    # def test_drop_table(self):
    #     db.drop_table("routes")
    #
    # def test_table_exists_returns_false(self):
    #     exists = db.table_exists("routes")
    #     self.assertFalse(exists)

    def test_create_and_drop_database(self):
        # created = db.create_new_database()
        # self.assertTrue(created)
        dropped = db.drop_database()
        self.assertTrue(dropped)

    # def test_activate_postgis_script(self):
    #     created = db.create_new_database()
    #     postgis = db.activate_postgis_extension()
    #     self.assertTrue(postgis)
    #
    # def test_initialize_db_with_extension_and_table(self):
    #     db.initialize_db_with_extension_and_table()

if __name__ == "__main__":
    unittest.main()
