import os
from typing import Annotated

from fastapi import Depends
from pymongo import MongoClient
from pymongo.database import Database

client = MongoClient(os.environ.get("MONGO_URL", "localhost"), 27017)


def getDb():
    return client[os.environ.get("MONGO_DB", "kraken")]


DBDep = Annotated[Database, Depends(getDb)]
