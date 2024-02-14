import os
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException
from pymongo import MongoClient

client = MongoClient(os.environ.get("MONGO_URL", "localhost"), 27017)


def getDb():
    return client[os.environ.get("MONGO_DB", "kraken")]


# This function is a dependency that will be used to convert a string in a request to an ObjectId.
def toObjectId(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")
    return ObjectId(id)


PyObjectId = Annotated[ObjectId, Depends(toObjectId)]
