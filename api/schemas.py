import datetime
from enum import Enum
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field


class Status(str, Enum):
    open = "Open"
    inProgress = "In Progress"
    completed = "Completed"


class Priority(str, Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class EditableUser(BaseModel):
    username: str
    password: str
    email: str


class User(EditableUser):
    id: Annotated[Optional[str], Field(alias="_id"), BeforeValidator(str)] = None
    ownedProjects: list[str] = []
    joinedProjects: list[str] = []
    token: Optional[str] = None


class Project(BaseModel):
    id: str
    name: str
    description: str
    milestones: list[str] = []
    sprints: list[str] = []
    createdAt: datetime.datetime


class Milestone(BaseModel):
    id: str
    name: str
    description: str
    dueDate: datetime.datetime
    status: Status
    tasks: list[str] = []


class BaseTask(BaseModel):
    name: str
    description: str
    createdAt: datetime.datetime
    dueDate: datetime.datetime
    status: Status
    priority: Priority
    assignedTo: Optional[str] = None


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
