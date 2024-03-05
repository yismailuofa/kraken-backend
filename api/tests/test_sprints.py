from unittest.mock import Mock

from bson import ObjectId
from fastapi import status

from api.tests.util import TestBase


class TestSprints(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.testSprint = {
            "name": "test",
            "description": "test",
            "startDate": "2022-01-01T00:00:00",
            "endDate": "2022-01-01T00:00:00",
        }

        cls.mockDb.sprints.insert_one = Mock(wraps=cls.mockDb.sprints.insert_one)
        cls.mockDb.sprints.find_one_and_update = Mock(
            wraps=cls.mockDb.sprints.find_one_and_update
        )
        cls.mockDb.sprints.delete_one = Mock(wraps=cls.mockDb.sprints.delete_one)

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.sprints.delete_many({})

        opts = {
            "return_value": True,
            "side_effect": True,
        }
        self.mockDb.sprints.insert_one.reset_mock(**opts)
        self.mockDb.sprints.find_one_and_update.reset_mock(**opts)
        self.mockDb.sprints.delete_one.reset_mock(**opts)

    def testCreateSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        sprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(sprintResponse.status_code, status.HTTP_200_OK)

        sprint = sprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], self.testSprint["name"])
        self.assertEqual(sprint["description"], self.testSprint["description"])
        self.assertEqual(sprint["startDate"], self.testSprint["startDate"])
        self.assertEqual(sprint["endDate"], self.testSprint["endDate"])

        for v in sprint.values():
            self.assertIsNotNone(v)

    def testCreateSprintProjectNotFound(self):
        user = self.createUser("test")

        sprintResponse = self.createSprint(
            user,
            str(ObjectId()),
            **self.testSprint,
        )

        self.assertEqual(sprintResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateSprintNotAuthorized(self):
        user = self.createUser("test")

        otherUser = self.createUser("other")

        project = self.createProject(user, "test", "test").json()

        sprintResponse = self.createSprint(
            otherUser,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(sprintResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testCreateSprintFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        self.mockDb.sprints.insert_one.return_value.acknowledged = False

        sprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(
            sprintResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testGetSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, status.HTTP_200_OK)

        createSprint = createSprintResponse.json()

        getSprintResponse = self.client.get(
            f"/sprints/{createSprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getSprintResponse.status_code, status.HTTP_200_OK)

        sprint = getSprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], createSprint["name"])
        self.assertEqual(sprint["description"], createSprint["description"])
        self.assertEqual(sprint["startDate"], createSprint["startDate"])
        self.assertEqual(sprint["endDate"], createSprint["endDate"])

        for v in sprint.values():
            self.assertIsNotNone(v)

    def testGetSprintNotAuthorized(self):
        user = self.createUser("test")

        otherUser = self.createUser("other")

        project = self.createProject(user, "test", "test").json()

        createSprint = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        ).json()

        getSprintResponse = self.client.get(
            f"/sprints/{createSprint['id']}", headers=self.userToHeader(otherUser)
        )

        self.assertEqual(getSprintResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, status.HTTP_200_OK)

        sprint = createSprintResponse.json()

        newName, newDescription = "newName", "newDescription"

        updateSprintResponse = self.client.patch(
            f"/sprints/{sprint['id']}",
            headers=self.userToHeader(user),
            json={"name": newName, "description": newDescription},
        )

        self.assertEqual(updateSprintResponse.status_code, status.HTTP_200_OK)

        sprint = updateSprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], newName)
        self.assertEqual(sprint["description"], newDescription)
        self.assertEqual(sprint["startDate"], self.testSprint["startDate"])
        self.assertEqual(sprint["endDate"], self.testSprint["endDate"])

        for v in sprint.values():
            self.assertIsNotNone(v)

    def testUpdateSprintNotFound(self):
        user = self.createUser("test")

        updateSprintResponse = self.client.patch(
            f"/sprints/{str(ObjectId())}",
            headers=self.userToHeader(user),
            json={"name": "test", "description": "test"},
        )

        self.assertEqual(updateSprintResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateSprintNotAuthorized(self):
        user = self.createUser("test")

        otherUser = self.createUser("other")

        project = self.createProject(user, "test", "test").json()

        createSprint = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        ).json()

        updateSprintResponse = self.client.patch(
            f"/sprints/{createSprint['id']}",
            headers=self.userToHeader(otherUser),
            json={"name": "test", "description": "test"},
        )

        self.assertEqual(updateSprintResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateSprintFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test").json()

        createSprint = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        ).json()

        self.mockDb.sprints.find_one_and_update.return_value = None

        updateSprintResponse = self.client.patch(
            f"/sprints/{createSprint['id']}",
            headers=self.userToHeader(user),
            json={"name": "test", "description": "test"},
        )

        self.assertEqual(
            updateSprintResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, status.HTTP_200_OK)

        sprint = createSprintResponse.json()

        deleteSprintResponse = self.client.delete(
            f"/sprints/{sprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteSprintResponse.status_code, status.HTTP_200_OK)

        getSprintResponse = self.client.get(
            f"/sprints/{sprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getSprintResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteSprintNotFound(self):
        user = self.createUser("test")

        deleteSprintResponse = self.client.delete(
            f"/sprints/{str(ObjectId())}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteSprintResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteSprintNotAuthorized(self):
        user = self.createUser("test")

        otherUser = self.createUser("other")

        project = self.createProject(user, "test", "test").json()

        createSprint = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        ).json()

        deleteSprintResponse = self.client.delete(
            f"/sprints/{createSprint['id']}", headers=self.userToHeader(otherUser)
        )

        self.assertEqual(deleteSprintResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteSprintFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test").json()

        createSprint = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        ).json()

        self.mockDb.sprints.delete_one.return_value.deleted_count = 0

        deleteSprintResponse = self.client.delete(
            f"/sprints/{createSprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteSprintResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )
