import os
from typing import Annotated

from bson import ObjectId
from fastapi import Depends, HTTPException, status
from pymongo import MongoClient, ReturnDocument
from pymongo.database import Database

from api.schemas import Milestone, Project, User

client = MongoClient(os.environ.get("MONGO_URL", "localhost"), 27017)


def getDb():
    return client[os.environ.get("MONGO_DB", "kraken")]


DBDep = Annotated[Database, Depends(getDb)]


def toObjectId(id: str) -> ObjectId:
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ObjectId"
        )

    return ObjectId(id)


# Some helper functions that help offload id logic from the routers


# USER
def findUserById(db: Database, id: str):
    return db.users.find_one({"_id": toObjectId(id)})


def insertUser(db: Database, user: User):
    return db.users.insert_one(user.model_dump(exclude={"id"}))


def findUserAndUpdate(db: Database, user: User, update: dict):
    return db.users.find_one_and_update(
        {"_id": user.oid()},
        update,
        return_document=ReturnDocument.AFTER,
    )


def findUserAndUpdateByEmail(db: Database, email: str, update: dict):
    return db.users.find_one_and_update(
        {"email": email},
        update,
        return_document=ReturnDocument.AFTER,
    )


def findUserAndUpdateById(db: Database, id: str, update: dict):
    return db.users.find_one_and_update(
        {"_id": toObjectId(id)},
        update,
        return_document=ReturnDocument.AFTER,
    )


# PROJECT
def findProjectById(db: Database, id: str):
    return db.projects.find_one({"_id": toObjectId(id)})


def insertProject(db: Database, project: Project):
    return db.projects.insert_one(project.model_dump(exclude={"id"}))


def findProjectAndUpdate(db: Database, projectID: str, update: dict):
    return db.projects.find_one_and_update(
        {"_id": toObjectId(projectID)},
        update,
        return_document=ReturnDocument.AFTER,
    )


# MILESTONE
def findMilestoneById(db: Database, id: str):
    return db.milestones.find_one({"_id": toObjectId(id)})


def insertMilestone(db: Database, milestone: Milestone):
    return db.milestones.insert_one(milestone.model_dump(exclude={"id"}))


def findMilestoneAndUpdate(db: Database, milestoneID: str, update: dict):
    return db.milestones.find_one_and_update(
        {"_id": toObjectId(milestoneID)},
        update,
        return_document=ReturnDocument.AFTER,
    )
