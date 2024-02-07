import os
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException
from pymongo import MongoClient

client = MongoClient("localhost", 27017)

db = client[os.environ.get("MONGO_DB", "kraken")]

usersCollection = db["users"]
projectsCollection = db["projects"]
milestonesCollection = db["milestones"]
tasksCollection = db["tasks"]
sprintsCollection = db["sprints"]


def toObjectId(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid ObjectId")
    return ObjectId(id)


PyObjectId = Annotated[ObjectId, Depends(toObjectId)]
