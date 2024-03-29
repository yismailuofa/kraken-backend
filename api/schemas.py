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
    todo = "To Do"
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


class CreateableProject(BaseModel):
    name: str
    description: str


class UpdateableProject(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class Project(CreateableProject):
    id: MongoID = None
    createdAt: datetime.datetime = now()


class CreateableMilestone(BaseModel):
    name: str
    description: str
    dueDate: datetime.datetime
    projectId: str
    dependentMilestones: list[str] = []
    dependentTasks: list[str] = []


class UpdateableMilestone(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dueDate: Optional[datetime.datetime] = None
    status: Optional[Status] = None
    dependentMilestones: Optional[list[str]] = None
    dependentTasks: Optional[list[str]] = None


class Milestone(CreateableMilestone):
    id: MongoID = None
    status: Status = Status.todo
    tasks: list[str] = []
    createdAt: datetime.datetime = Field(default_factory=now)


class BaseCreateableTask(BaseModel):
    name: str
    description: str
    dueDate: datetime.datetime
    priority: Priority = Priority.medium
    status: Status = Status.todo
    assignedTo: str = "Unassigned"


class CreateableTask(BaseCreateableTask):
    projectId: str
    milestoneId: str
    dependentMilestones: list[str] = []
    dependentTasks: list[str] = []
    qaTask: BaseCreateableTask


class BaseUpdateableTask(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    dueDate: Optional[datetime.datetime] = None
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    assignedTo: Optional[str] = None


class UpdateableTask(BaseUpdateableTask):
    projectId: Optional[str] = None
    milestoneId: Optional[str] = None
    qaTask: Optional[BaseUpdateableTask] = None
    dependentMilestones: Optional[list[str]] = None
    dependentTasks: Optional[list[str]] = None


class Task(CreateableTask):
    id: MongoID = None
    qaTask: BaseCreateableTask
    createdAt: datetime.datetime = Field(default_factory=now)


class CreateableSprint(BaseModel):
    name: str
    description: str
    startDate: datetime.datetime
    endDate: datetime.datetime
    projectId: str


class UpdateableSprint(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    startDate: Optional[datetime.datetime] = None
    endDate: Optional[datetime.datetime] = None
    tasks: Optional[list[str]] = None
    milestones: Optional[list[str]] = None


class Sprint(CreateableSprint):
    id: MongoID = None
    tasks: list[str] = []
    milestones: list[str] = []


class SprintView(Sprint):
    tasks: list[Task] = []
    milestones: list[Milestone] = []


class ProjectView(Project):
    milestones: list[Milestone] = []
    tasks: list[Task] = []
    sprints: list[SprintView] = []
