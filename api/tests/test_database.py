import unittest

from fastapi import HTTPException

from api.database import getDb, toObjectId


class TestDatabase(unittest.TestCase):
    def testGetDb(self):
        db = getDb()
        self.assertIsNotNone(db)

    def testToObjectId(self):
        oid = toObjectId("5f6e7d5f7e3f5e7d5f7e3f5e")
        self.assertIsNotNone(oid)

    def testToObjectIdBad(self):
        with self.assertRaises(HTTPException):
            toObjectId("123")
