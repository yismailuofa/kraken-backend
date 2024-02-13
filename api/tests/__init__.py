from mongomock import MongoClient

from api.database import getDb
from api.main import app

mockDb = MongoClient().db
app.dependency_overrides[getDb] = lambda: mockDb
