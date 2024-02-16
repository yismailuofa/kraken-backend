import datetime
import unittest

from fastapi import status
from fastapi.testclient import TestClient
from mongomock import MongoClient

from api.database import getDb
from api.main import app


class TestProjects(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.mockDb = MongoClient().db
        app.dependency_overrides[getDb] = lambda: cls.mockDb

        user = cls.client.post(
            "/users/register",
            json={
                "username": "test",
                "password": "test",
                "email": "test@test.com",
            },
        )

        cls.headers = {"Authorization": f"Bearer {user.json()['token']}"}

    def tearDown(self) -> None:
        self.mockDb.projects.delete_many({})

    def testCreateProject(self):
        projectName = "test"
        projectDescription = "test"

        response = self.client.post(
            "/projects/",
            json={
                "name": projectName,
                "description": projectDescription,
            },
            headers=self.headers,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json = response.json()

        self.assertEqual(json["name"], projectName)
        self.assertEqual(json["description"], projectDescription)

        for v in json.values():
            self.assertIsNotNone(v)

        # check that the time is within 1 minute of the current time
        difference = datetime.datetime.now() - datetime.datetime.fromisoformat(
            json["createdAt"]
        )
        self.assertLessEqual(
            difference,
            datetime.timedelta(minutes=1),
        )
