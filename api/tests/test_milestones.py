import unittest

from bson import ObjectId
from fastapi import status
from fastapi.testclient import TestClient
from mongomock import MongoClient

from api.database import getDb
from api.main import app


class TestMilestones(unittest.TestCase):
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

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.milestones.delete_many({})

    def testCreateMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestoneName = "test"
        milestoneDescription = "test"
        milestoneDueDate = "2001-10-01T00:00:00"

        milestoneResponse = self.createMilestone(
            user, project["id"], milestoneName, milestoneDescription, milestoneDueDate
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_200_OK)

        milestone = milestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], milestoneName)
        self.assertEqual(milestone["description"], milestoneDescription)
        self.assertEqual(milestone["dueDate"], milestoneDueDate)

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testCreateMilestoneProjectNotFound(self):
        user = self.createUser("test")

        milestoneResponse = self.createMilestone(
            user, str(ObjectId()), "test", "test", "2001-10-01T00:00:00"
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateMilestoneUserNoAccess(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test").json()

        otherUser = self.createUser("other")

        milestoneResponse = self.createMilestone(
            otherUser, project["id"], "test", "test", "2001-10-01T00:00:00"
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testGetMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestoneName = "test"
        milestoneDescription = "test"
        milestoneDueDate = "2001-10-01T00:00:00"

        createMilestoneResponse = self.createMilestone(
            user, project["id"], milestoneName, milestoneDescription, milestoneDueDate
        )

        self.assertEqual(createMilestoneResponse.status_code, status.HTTP_200_OK)

        milestoneResponse = self.client.get(
            f"/milestones/{createMilestoneResponse.json()['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_200_OK)

        milestone = milestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], milestoneName)
        self.assertEqual(milestone["description"], milestoneDescription)
        self.assertEqual(milestone["dueDate"], milestoneDueDate)

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testGetMilestoneMilestoneNotFound(self):
        user = self.createUser("test")

        milestoneResponse = self.client.get(
            f"/milestones/{str(ObjectId())}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testGetMilestoneUserNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        otherUser = self.createUser("other")

        createMilestoneResponse = self.createMilestone(
            user, project["id"], "test", "test", "2001-10-01T00:00:00"
        )

        milestoneResponse = self.client.get(
            f"/milestones/{createMilestoneResponse.json()['id']}",
            headers=self.userToHeader(otherUser),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2001-10-01T00:00:00"
        ).json()

        milestoneName = "test2"
        milestoneDescription = "test2"
        milestoneDueDate = "2001-10-02T00:00:00"
        milestoneStatus = "In Progress"

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={
                "name": milestoneName,
                "description": milestoneDescription,
                "dueDate": milestoneDueDate,
                "status": milestoneStatus,
            },
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateMilestoneResponse.status_code, status.HTTP_200_OK)

        milestone = updateMilestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], milestoneName)
        self.assertEqual(milestone["description"], milestoneDescription)
        self.assertEqual(milestone["dueDate"], milestoneDueDate)
        self.assertEqual(milestone["status"], milestoneStatus)

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testUpdateMilestoneMilestoneForbidden(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2001-10-01T00:00:00"
        ).json()

        otherUser = self.createUser("other")

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={},
            headers=self.userToHeader(otherUser),
        )

        self.assertEqual(updateMilestoneResponse.status_code, status.HTTP_403_FORBIDDEN)
