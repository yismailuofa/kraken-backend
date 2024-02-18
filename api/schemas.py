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
    open = "Open"
    inProgress = "In Progress"
    completed = "Completed"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


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


class CreateableProject(BaseModel):
    name: str
    description: str


class EditableProject(CreateableProject):
    milestones: list[str] = []
    sprints: list[str] = []
    createdAt: datetime.datetime = now()


class Project(EditableProject):
    id: MongoID = None


class Milestone(BaseModel):
    id: str
    name: str
    description: str
    dueDate: datetime.datetime
    status: Status
    projectId: str
    tasks: list[str] = []
    dependentMilestones: list[str] = []
    dependentTasks: list[str] = []


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


class Sprint(BaseModel):
    id: str
    name: str
    description: str
    startDate: datetime.datetime
    endDate: datetime.datetime
    tasks: list[str] = []
    milestones: list[str] = []
    project: str
