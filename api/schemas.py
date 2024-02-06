import datetime
from enum import Enum
from pydantic import BaseModel


class Status(str, Enum):
    open = "open"
    inProgress = "In Progress"
    completed = "Completed"


class User(BaseModel):
    id: str
    username: str
    password: str
    email: str
    ownedProjects: list[str] = []
    joinedProjects: list[str] = []


class Project(BaseModel):
    id: str
    name: str
    description: str
    milestones: list[str] = []
    createdAt: datetime.datetime


class Milestone(BaseModel):
    id: str
    name: str
    description: str
    dueDate: datetime.datetime
    status: Status
    tasks: list[str] = []


class BaseTask(BaseModel):
    id: str
    name: str
    description: str
    createdAt: datetime.datetime
    dueDate: datetime.datetime
    status: Status
    assignedTo: str


class Task(BaseTask):
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
