import datetime
import time
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

    def tearDown(self) -> None:
        self.mockDb.projects.delete_many({})
        self.mockDb.users.delete_many({})

    def createProject(self, user, name, description):
        return self.client.post(
            "/projects/",
            json={
                "name": name,
                "description": description,
            },
            headers=self.userToHeader(user),
        )

    def testCreateProject(self):
        projectName = "test"
        projectDescription = "test"
        user = self.createUser("test")

        response = self.createProject(user, projectName, projectDescription)
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

    def testGetProjects(self):
        user = self.createUser("test")

        getResponse = self.client.get("/projects/", headers=self.userToHeader(user))

        self.assertEqual(getResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(getResponse.json(), [])

        createResponse = self.createProject(user, "test", "test")
        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        newGetResponse = self.client.get("/projects/", headers=self.userToHeader(user))
        self.assertEqual(newGetResponse.status_code, status.HTTP_200_OK)

        json = newGetResponse.json()
        self.assertEqual(len(json), 1)
        self.assertDictEqual(createResponse.json(), json[0])

    def testGetProject(self):
        user = self.createUser("test")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        getResponse = self.client.get(
            f"/projects/{projectId}", headers=self.userToHeader(user)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_200_OK)
        self.assertDictEqual(createResponse.json(), getResponse.json())

    def testGetProjectForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        getResponse = self.client.get(
            f"/projects/{projectId}", headers=self.userToHeader(user2)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testAddUserToProject(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        addUserResponse = self.client.post(
            "/projects/users/add",
            headers=self.userToHeader(user),
            params={"projectId": projectId, "username": user2["username"]},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_200_OK)

        user2GetResponse = self.client.get(
            "/users/me", headers=self.userToHeader(user2)
        )

        self.assertEqual(user2GetResponse.status_code, status.HTTP_200_OK)
        self.assertListEqual(user2GetResponse.json()["joinedProjects"], [projectId])
