import datetime
from enum import Enum
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import AliasChoices, BaseModel, BeforeValidator, Field

"""
This custom type does some helpful things:
On create, the id field is not required, so it is set to None.
When saving to the database we use the alias _id in serialization.
When retrieving from the database we use the alias _id in deserialization.
When returning the object we use the BeforeValidator to convert the ObjectId to a string.
"""
MongoID = Annotated[
    Optional[str],
    Field(validation_alias=AliasChoices("_id", "id")),
    BeforeValidator(str),
]


# Truncates the precision of a datetime to milliseconds to match the database.
def now():
    return datetime.datetime.now().replace(microsecond=0)


class Status(str, Enum):
    todo = "Todo"
    inProgress = "In Progress"
    completed = "Completed"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


# USER
class UserView(BaseModel):
    id: MongoID
    username: str
    email: str


class CreatableUser(BaseModel):
    username: str
    password: str
    email: str


class User(CreatableUser):
    id: MongoID = None
    ownedProjects: list[str] = []
    joinedProjects: list[str] = []
    token: Optional[str] = None

    def oid(self) -> ObjectId:
        return ObjectId(self.id)

    def canAccess(self, id: str) -> bool:
        return id in self.ownedProjects + self.joinedProjects

    def isAdmin(self, id: str) -> bool:
        return id in self.ownedProjects

    def projects(self) -> list[str]:
        return self.ownedProjects + self.joinedProjects


# PROJECT
class CreateableProject(BaseModel):
    name: str
    description: str


class UpdateableProject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Project(CreateableProject):
    id: MongoID = None
    createdAt: datetime.datetime = now()

    def oid(self) -> ObjectId:
        return ObjectId(self.id)


# MILESTONE
class CreateableMilestone(BaseModel):
    name: str
    description: str
    dueDate: datetime.datetime
    projectId: str


class Milestone(CreateableMilestone):
    id: MongoID = None
    status: Status = Status.todo
    tasks: list[str] = []
    dependentMilestones: list[str] = []
    dependentTasks: list[str] = []


# TASK
class BaseTask(BaseModel):
    name: str
    description: str
    createdAt: datetime.datetime
    dueDate: datetime.datetime
    status: Status
    projectId: str
    priority: Priority
    assignedTo: Optional[str] = None
    dependentMilestones: list[str] = []
    dependentTasks: list[str] = []


class Task(BaseTask):
    id: str
    qaTask: BaseTask


# SPRINT
class Sprint(BaseModel):
    id: str
    name: str
    description: str
    startDate: datetime.datetime
    endDate: datetime.datetime
    tasks: list[str] = []
    milestones: list[str] = []
    project: str
