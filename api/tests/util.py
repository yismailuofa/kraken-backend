import unittest

from fastapi.testclient import TestClient
from mongomock import MongoClient

from api.database import getDb
from api.main import app


class TestBase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.mockDb = MongoClient().db
        app.dependency_overrides[getDb] = lambda: cls.mockDb

    def createUser(self, keyword: str):
        return self.client.post(
            "/users/register",
            json={
                "username": keyword,
                "password": keyword,
                "email": f"{keyword}@{keyword}.com",
            },
        ).json()

    def userToHeader(self, user):
        return {"Authorization": f"Bearer {user['token']}"}

    def createProject(self, user, name, description):
        return self.client.post(
            "/projects/",
            json={
                "name": name,
                "description": description,
            },
            headers=self.userToHeader(user),
        )

    def createMilestone(self, user, projectId, name, description, dueDate):
        return self.client.post(
            "/milestones/",
            json={
                "projectId": projectId,
                "name": name,
                "description": description,
                "dueDate": dueDate,
            },
            headers=self.userToHeader(user),
        )

    def createTask(
        self, user, projectId, milestoneId, name, description, dueDate, qaTask
    ):
        return self.client.post(
            "/tasks/",
            json={
                "projectId": projectId,
                "milestoneId": milestoneId,
                "name": name,
                "description": description,
                "dueDate": dueDate,
                "qaTask": qaTask,
            },
            headers=self.userToHeader(user),
        )
