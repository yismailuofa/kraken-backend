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

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.sprints.delete_many({})

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

    def testGetSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, 200)

        createSprint = createSprintResponse.json()

        getSprintResponse = self.client.get(
            f"/sprints/{createSprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getSprintResponse.status_code, 200)

        sprint = getSprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], createSprint["name"])
        self.assertEqual(sprint["description"], createSprint["description"])
        self.assertEqual(sprint["startDate"], createSprint["startDate"])
        self.assertEqual(sprint["endDate"], createSprint["endDate"])

        for v in sprint.values():
            self.assertIsNotNone(v)

    def testUpdateSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, 200)

        sprint = createSprintResponse.json()

        newName, newDescription = "newName", "newDescription"

        updateSprintResponse = self.client.patch(
            f"/sprints/{sprint['id']}",
            headers=self.userToHeader(user),
            json={"name": newName, "description": newDescription},
        )

        self.assertEqual(updateSprintResponse.status_code, 200)

        sprint = updateSprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], newName)
        self.assertEqual(sprint["description"], newDescription)
        self.assertEqual(sprint["startDate"], self.testSprint["startDate"])
        self.assertEqual(sprint["endDate"], self.testSprint["endDate"])

        for v in sprint.values():
            self.assertIsNotNone(v)

    def testDeleteSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createSprintResponse = self.createSprint(
            user,
            project["id"],
            **self.testSprint,
        )

        self.assertEqual(createSprintResponse.status_code, 200)

        sprint = createSprintResponse.json()

        deleteSprintResponse = self.client.delete(
            f"/sprints/{sprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteSprintResponse.status_code, 200)

        getSprintResponse = self.client.get(
            f"/sprints/{sprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getSprintResponse.status_code, 404)
