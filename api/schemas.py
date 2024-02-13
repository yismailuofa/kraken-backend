import datetime
from enum import Enum
from typing import Annotated, Optional

from click import Option
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
    id: Annotated[str, Field(None, alias="_id"), BeforeValidator(str)]
    ownedProjects: list[str] = Field([], description="Project IDs that the user owns")
    joinedProjects: list[str] = Field(
        [], description="Project IDs that the user is a member of"
    )
    token: str


class Project(BaseModel):
    id: str
    name: str
    description: str
    milestones: list[str] = Field([], description="Milestone IDs in the project")
    sprints: list[str] = Field([], description="Sprint IDs in the project")
    createdAt: datetime.datetime


class Milestone(BaseModel):
    id: str
    name: str
    description: str
    dueDate: datetime.datetime
    status: Status
    tasks: list[str] = Field([], description="Task IDs in the milestone")


class BaseTask(BaseModel):
    name: str
    description: str
    createdAt: datetime.datetime
    dueDate: datetime.datetime
    status: Status
    priority: Priority
    assignedTo: str = Field(
        None, description="User ID of the user assigned to the task"
    )


class Task(BaseTask):
    id: str
    qaTask: BaseTask


class Sprint(BaseModel):
    id: str
    name: str
    description: str
    startDate: datetime.datetime
    endDate: datetime.datetime
    tasks: list[str] = Field([], description="Task IDs in the sprint")
    milestones: list[str] = Field([], description="Milestone IDs in the sprint")
    project: str
